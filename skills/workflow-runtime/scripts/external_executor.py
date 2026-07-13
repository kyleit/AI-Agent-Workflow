# external_executor.py
import os
import sys
import uuid
import time
import signal
import asyncio
import subprocess
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Set
from event_store import SQLiteEventStore

class ForbiddenProcessSpawnError(Exception):
    pass

class ToolRequest:
    def __init__(
        self,
        session_id: str,
        agent_id: str,
        task_id: str,
        command: str,
        arguments: Optional[List[str]] = None,
        cwd: str = ".",
        environment: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        permission_scope: str = "sandbox",
        resource_limits: Optional[Dict[str, Any]] = None,
        retry_policy: Optional[Dict[str, Any]] = None
    ) -> None:
        self.tool_request_id = str(uuid.uuid4())
        self.session_id = session_id
        self.agent_id = agent_id
        self.task_id = task_id
        self.command = command
        self.arguments = arguments or []
        self.cwd = cwd
        self.environment = environment or os.environ.copy()
        self.timeout = timeout
        self.permission_scope = permission_scope
        self.resource_limits = resource_limits or {"max_stdout_mb": 5.0}
        self.retry_policy = retry_policy or {"max_retries": 3}

class ToolResult:
    def __init__(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration: float,
        error_category: str = "none"  # "none" | "timeout" | "permission_denied" | "invalid_command" | "compile_error" | "retryable_failure"
    ) -> None:
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration
        self.error_category = error_category
        self.resource_usage = {}
        self.artifacts = []
        self.changed_files = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": self.duration,
            "error_category": self.error_category
        }

# Global registry of allowed commands
ALLOWED_COMMANDS = {"pytest", "git", "npm", "docker", "browser", "go", "python", "python3"}

class ToolExecutor:
    def __init__(self, event_store: Optional[SQLiteEventStore] = None) -> None:
        self.event_store = event_store
        self._active_pgids: Set[int] = set()

    def validate_request(self, request: ToolRequest) -> None:
        # 1. Allowed Commands check (Registry check)
        if request.command not in ALLOWED_COMMANDS:
            raise PermissionError(f"Command '{request.command}' is not in the allowed Tool Registry.")
            
        # 2. Permission Boundary & Sandbox isolation check
        resolved_cwd = os.path.abspath(request.cwd)
        resolved_workspace = os.path.abspath(".")
        
        # Sandbox must remain inside workspace root
        if request.permission_scope == "sandbox":
            if not resolved_cwd.startswith(resolved_workspace):
                raise PermissionError("Sandbox violation: Path is outside the workspace root.")

    def classify_error(self, exit_code: int, stderr: str) -> str:
        if exit_code == -signal.SIGKILL or exit_code == -signal.SIGTERM or exit_code == 124:
            return "timeout"
        if "permission denied" in stderr.lower() or "not permitted" in stderr.lower():
            return "permission_denied"
        if "command not found" in stderr.lower() or exit_code == 127:
            return "invalid_command"
        if "syntax error" in stderr.lower() or "compile error" in stderr.lower() or "syntaxerror" in stderr.lower():
            return "compile_error"
        if exit_code != 0:
            return "retryable_failure"
        return "none"

    async def execute_tool(self, request: ToolRequest) -> ToolResult:
        # Validate boundary before execute
        self.validate_request(request)
        
        if self.event_store:
            self.event_store.append_event(
                session_id=request.session_id,
                topic="tool.requested",
                payload={"command": request.command, "arguments": request.arguments}
            )

        start_time = time.time()
        
        # Construct full command list
        full_cmd = [request.command] + request.arguments
        
        # Flag to indicate if call is authorized (spawning through ToolExecutor)
        # Used by the global patched Popen
        try:
            task = asyncio.current_task()
            if task:
                setattr(task, "_authorized_spawn", True)
        except Exception:
            pass
        
        try:
            if self.event_store:
                self.event_store.append_event(
                    session_id=request.session_id,
                    topic="tool.started",
                    payload={"command": request.command}
                )

            # Spawn subprocess with os.setsid on Unix to assign new PGID
            # preexec_fn=os.setsid assigns group PGID equal to subprocess PID
            proc = await asyncio.create_subprocess_exec(
                *full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=request.cwd,
                env=request.environment,
                preexec_fn=os.setsid if sys.platform != "win32" else None
            )
            
            pgid = proc.pid
            if sys.platform != "win32":
                self._active_pgids.add(pgid)

            stdout_chunks = []
            stderr_chunks = []
            max_stdout_bytes = int(request.resource_limits.get("max_stdout_mb", 5.0) * 1024 * 1024)
            stdout_len = 0

            # Read stream helper
            async def read_stream(stream, name):
                nonlocal stdout_len
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded_line = line.decode("utf-8", errors="replace")
                    
                    if name == "stdout":
                        if stdout_len < max_stdout_bytes:
                            stdout_chunks.append(decoded_line)
                            stdout_len += len(line)
                    else:
                        stderr_chunks.append(decoded_line)
                        
                    if self.event_store:
                        self.event_store.append_event(
                            session_id=request.session_id,
                            topic="tool.output",
                            payload={"stream": name, "line": decoded_line}
                        )

            try:
                # Wait for streams under timeout limit
                await asyncio.wait_for(
                    asyncio.gather(
                        read_stream(proc.stdout, "stdout"),
                        read_stream(proc.stderr, "stderr"),
                        proc.wait()
                    ),
                    timeout=request.timeout
                )
                exit_code = proc.returncode
            except asyncio.TimeoutError:
                # Handle timeout with force PGID cleanup
                exit_code = 124
                if self.event_store:
                    self.event_store.append_event(
                        session_id=request.session_id,
                        topic="tool.timeout",
                        payload={"timeout": request.timeout}
                    )
                await self.cleanup_process_tree(pgid)
            except asyncio.CancelledError:
                # Handle cancellation
                exit_code = -signal.SIGTERM
                if self.event_store:
                    self.event_store.append_event(
                        session_id=request.session_id,
                        topic="tool.cancelled",
                        payload={"reason": "cancelled by scheduler"}
                    )
                await self.cleanup_process_tree(pgid)
                raise

            duration = time.time() - start_time
            stdout_str = "".join(stdout_chunks)
            stderr_str = "".join(stderr_chunks)
            
            error_cat = self.classify_error(exit_code, stderr_str)
            result = ToolResult(exit_code, stdout_str, stderr_str, duration, error_cat)
            
            if self.event_store:
                topic = "tool.completed" if exit_code == 0 else "tool.failed"
                self.event_store.append_event(
                    session_id=request.session_id,
                    topic=topic,
                    payload=result.to_dict()
                )
                
            return result
        finally:
            if sys.platform != "win32" and 'pgid' in locals():
                self._active_pgids.discard(pgid)
            try:
                task = asyncio.current_task()
                if task:
                    setattr(task, "_authorized_spawn", False)
            except Exception:
                pass

    async def cleanup_process_tree(self, pgid: int) -> None:
        if sys.platform == "win32":
            return # Process groups not supported natively via setsid on Windows
            
        try:
            # Send SIGTERM to process group PGID
            os.killpg(pgid, signal.SIGTERM)
            # Give a brief moment to shut down gracefully
            await asyncio.sleep(0.1)
            # Force cleanup by sending SIGKILL to entire process group tree
            os.killpg(pgid, signal.SIGKILL)
            
            if self.event_store:
                self.event_store.append_event(
                    session_id="",
                    topic="tool.cleaned",
                    payload={"pgid": pgid}
                )
        except ProcessLookupError:
            pass
        except Exception as e:
            print(f"Error during PGID process group cleanup: {e}", file=sys.stderr)

# Global Runtime Validator (Patched subprocess.Popen)
_original_popen = subprocess.Popen

def patched_Popen(*args, **kwargs):
    # Retrieve active asyncio task to inspect if authorized
    try:
        task = asyncio.current_task()
        if task and getattr(task, "_authorized_spawn", False):
            return _original_popen(*args, **kwargs)
    except RuntimeError:
        pass  # Event loop not running in current thread context
        
    # Analyze stacktrace
    stack = traceback.extract_stack()
    is_authorized = False
    for frame in stack:
        # Check if caller is strictly the execute_tool method inside external_executor.py
        if os.path.basename(frame.filename) == "external_executor.py" and frame.name == "execute_tool":
            is_authorized = True
            break
            
    if not is_authorized:
        raise ForbiddenProcessSpawnError(
            "Forbidden process spawn call detected! All OS subprocesses must be created through Tool Executor."
        )
        
    return _original_popen(*args, **kwargs)

# Inject patched Popen globally
subprocess.Popen = patched_Popen
