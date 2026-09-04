"""Handler: do_provider_action part A."""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

from workflow_runtime.infrastructure.persistence.runtime_daemon_state import (
    RuntimeDaemonState)

from typing import Any, cast


def _is_outside_workflow_gateway() -> bool:
    session_data: dict[str, Any] = {}
    session_path = os.path.abspath(os.path.join(".", ".agents", ".session.json"))
    if os.path.exists(session_path):
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                raw_session = json.load(f)
                if isinstance(raw_session, dict):
                    session_data = cast(dict[str, Any], raw_session)
        except Exception:
            session_data = {}
    execution_mode = str(os.environ.get("AIWF_EXECUTION_MODE") or session_data.get("execution_mode") or "")
    workflow_id = str(os.environ.get("AIWF_WORKFLOW_ID") or session_data.get("workflow_id") or "")
    return execution_mode != "workflow" or not bool(workflow_id)

def _is_aiwf_project_root(path: str) -> bool:
    return os.path.exists(os.path.join(path, ".agents", "AI_RULES.md")) or os.path.exists(os.path.join(path, "AI_RULES.md"))

def _resolve_aiwf_project_root() -> str:
    cwd = os.path.abspath(".")
    if _is_aiwf_project_root(cwd):
        return cwd
    probe = Path(__file__).resolve()
    for parent in probe.parents:
        if parent.name == ".agents":
            return str(parent.parent)
        if parent.name == "public_export":
            return str(parent.parent)
        if _is_aiwf_project_root(str(parent)):
            return str(parent)
    try:
        from workflow_runtime.application.workflow import aiwf_registry
        registry = aiwf_registry.load_registry()
        for project in registry.get("projects", []):
            path = str(project.get("path") or "")
            if path and os.path.exists(path) and _is_aiwf_project_root(path):
                return os.path.abspath(path)
    except Exception:
        pass
    return cwd

def _runtime_pythonpath_root() -> str:
    probe = Path(__file__).resolve()
    for parent in probe.parents:
        if (parent / "workflow_runtime").is_dir():
            return str(parent)
    return str(probe.parents[6])

def kill_all_telegram_processes(pid_file_pid: int | None = None) -> list[int]:
    """Kill ALL python processes running 'workflow_runtime telegram daemon'.

    Uses real OS process scan (not just .pid file) so stale PID files cannot
    hide zombie daemons.  Returns list of killed PIDs.
    """
    killed: list[int] = []
    my_pid = os.getpid()

    if os.name == "nt":

        import subprocess

        # Use wmic /format:list — key=value lines, safe for CommandLine with commas
        try:
            res = subprocess.run(
                ["wmic", "process", "where",
                 "name='python.exe' or name='python3.exe' or name='pythonw.exe'",
                 "get", "ProcessId,CommandLine", "/format:list"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, timeout=10, encoding="utf-8", errors="replace"
            )
            current_cmdline = ""
            current_pid: int | None = None
            for line in res.stdout.splitlines():
                line = line.strip()
                if line.startswith("CommandLine="):
                    current_cmdline = line[len("CommandLine="):]
                    current_pid = None
                elif line.startswith("ProcessId="):
                    pid_str = line[len("ProcessId="):].strip()
                    if pid_str.isdigit():
                        current_pid = int(pid_str)
                    if current_pid and current_pid != my_pid:
                        if ("workflow_runtime" in current_cmdline
                                and "telegram" in current_cmdline
                                and "daemon" in current_cmdline):
                            subprocess.run(
                                ["taskkill", "/F", "/PID", str(current_pid)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                            )
                            killed.append(current_pid)
                    current_cmdline = ""
                    current_pid = None
        except Exception:
            pass

        # Fallback: kill the PID from the file if not already caught
        if pid_file_pid and pid_file_pid not in killed:
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid_file_pid)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
    else:
        import signal
        import subprocess
        try:
            res = subprocess.run(
                ["ps", "-eo", "pid,args"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, timeout=10
            )
            for line in res.stdout.splitlines():
                parts = line.strip().split(None, 1)
                if len(parts) < 2:
                    continue
                try:
                    pid = int(parts[0])
                except ValueError:
                    continue
                cmdline = parts[1]
                if pid == my_pid:
                    continue
                if ("workflow_runtime" in cmdline
                        and "telegram" in cmdline
                        and "daemon" in cmdline):
                    try:
                        os.kill(pid, signal.SIGTERM)
                        killed.append(pid)
                    except Exception:
                        pass
        except Exception:
            pass
        if pid_file_pid and pid_file_pid not in killed:
            try:
                os.kill(pid_file_pid, signal.SIGTERM)
            except Exception:
                pass
    return killed

def stop_telegram_daemon(pid_file: str) -> bool:
    """Stop the Telegram daemon.

    Kills the PID from the .pid file AND any orphaned processes running
    'workflow_runtime telegram daemon' that were missed by the file tracker.
    """
    pid_file_pid: int | None = None
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r", encoding="utf-8") as f:
                pid_file_pid = int(f.read().strip())
        except Exception:
            pass
    # Kill ALL real processes (including orphans not in .pid file)
    kill_all_telegram_processes(pid_file_pid)
    # Always remove the pid file
    try:
        if os.path.exists(pid_file):
            os.remove(pid_file)
    except Exception:
        pass
    return True

def telegram_autostart_target(daemon_script: str, log_file: str) -> str:
    import platform
    system = platform.system()
    if system == "Darwin":
        return os.path.expanduser("~/Library/LaunchAgents/net.aiwf.telegram-daemon.plist")
    if system == "Windows":
        return "AIWF Telegram Daemon"
    return os.path.expanduser("~/.config/systemd/user/aiwf-telegram-daemon.service")

def is_telegram_autostart_enabled(daemon_script: str, log_file: str) -> bool:
    target = telegram_autostart_target(daemon_script, log_file)
    if target == "AIWF Telegram Daemon":
        if _is_outside_workflow_gateway():
            return False
        import subprocess
        res = subprocess.run(["schtasks", "/Query", "/TN", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0
    return os.path.exists(target)

def enable_telegram_autostart(daemon_script: str, log_file: str) -> str:
    import platform
    import subprocess
    system = platform.system()
    py = sys.executable
    if system == "Darwin":
        target = telegram_autostart_target(daemon_script, log_file)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>net.aiwf.telegram-daemon</string>
  <key>ProgramArguments</key>
  <array>
    <string>{py}</string>
    <string>{daemon_script}</string>
    <string>daemon</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>{log_file}</string>
  <key>StandardErrorPath</key><string>{log_file}</string>
</dict>
</plist>
'''
        with open(target, "w", encoding="utf-8") as f:
            f.write(plist)
        _uid = os.getuid() if hasattr(os, 'getuid') else 0
        subprocess.run(['launchctl', 'bootstrap', f'gui/{_uid}', target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return target
    if system == "Windows":
        target = telegram_autostart_target(daemon_script, log_file)
        cmd = f'"{py}" "{daemon_script}" daemon'
        try:
            subprocess.run(["schtasks", "/Create", "/TN", target, "/TR", cmd, "/SC", "ONLOGON", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception as e:
            print(f"[WARN] Failed to create schtasks (requires Administrator privileges). Task might not be registered. Error: {e}", file=sys.stderr)
        return target

    target = telegram_autostart_target(daemon_script, log_file)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    service = f"""[Unit]
Description=AIWF Telegram Shared Daemon

[Service]
ExecStart={py} {daemon_script} daemon
Restart=always
StandardOutput=append:{log_file}
StandardError=append:{log_file}

[Install]
WantedBy=default.target
"""
    with open(target, "w", encoding="utf-8") as f:
        f.write(service)
    subprocess.run(["systemctl", "--user", "daemon-reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["systemctl", "--user", "enable", "aiwf-telegram-daemon.service"], check=True)
    return target

def disable_telegram_autostart(daemon_script: str, log_file: str) -> str:
    import platform
    import subprocess
    system = platform.system()
    target = telegram_autostart_target(daemon_script, log_file)
    if system == "Darwin":
        _uid = os.getuid() if hasattr(os, 'getuid') else 0
        subprocess.run(['launchctl', 'bootout', f'gui/{_uid}', target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(target):
            os.remove(target)
        return target
    if system == "Windows":
        subprocess.run(["schtasks", "/Delete", "/TN", target, "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return target
    subprocess.run(["systemctl", "--user", "disable", "aiwf-telegram-daemon.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(target):
        os.remove(target)
    return target

def start_runtime_bus_daemon() -> tuple[bool, int | None, str]:
    workspace_root = _resolve_aiwf_project_root()
    try:
        state = RuntimeDaemonState(workspace_root=workspace_root)
    except TypeError:
        # Keep compatibility with lightweight state doubles and older adapters
        # that still expose the zero-argument constructor.
        state = RuntimeDaemonState()
    current = state.inspect()
    if current.get("active"):
        return False, int(cast(int, current.get("pid") or 0)), "already_running"

    log_file = os.path.expanduser("~/.aiwf/runtime.log")

    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    log_out = open(log_file, "a", encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONPATH"] = _runtime_pythonpath_root() + os.pathsep + env.get("PYTHONPATH", "")
    env["AIWF_PROJECT_ROOT"] = workspace_root
    if os.name == "nt":
        create_no_window = 0x08000000
        detached_process = 0x00000008
        proc = subprocess.Popen(
            [sys.executable, "-m", "workflow_runtime", "runtime", "daemon"],
            stdout=log_out,
            stderr=log_out,
            stdin=subprocess.DEVNULL,
            creationflags=create_no_window | detached_process,
            close_fds=True,
            env=env,
            cwd=workspace_root,
        )
    else:
        proc = subprocess.Popen(
            [sys.executable, "-m", "workflow_runtime", "runtime", "daemon"],
            stdout=log_out,
            stderr=log_out,
            preexec_fn=os.setpgrp,
            env=env,
            cwd=workspace_root,
        )
    log_out.close()
    state.write_started(proc.pid)
    return True, proc.pid, "started"

def stop_runtime_bus_daemon(pid_file: str | None = None) -> tuple[bool, int | None]:
    pid_file = pid_file or os.path.expanduser("~/.aiwf/runtime.pid")
    pid = None
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r", encoding="utf-8") as f:
                pid = int(f.read().strip())
        except Exception:
            pid = None
    if pid:
        try:
            if os.name == "nt":
                import ctypes
                handle = ctypes.windll.kernel32.OpenProcess(1, False, pid)
                if handle:
                    ctypes.windll.kernel32.TerminateProcess(handle, 0)
                    ctypes.windll.kernel32.CloseHandle(handle)
            else:
                os.kill(pid, 15)
        except Exception:
            pass
    RuntimeDaemonState(root=os.path.dirname(pid_file)).clear_stale()
    return bool(pid), pid

def restart_runtime_bus_daemon() -> tuple[bool, int | None, str]:
    stop_runtime_bus_daemon()
    return start_runtime_bus_daemon()

def runtime_bus_autostart_target() -> str:
    import platform
    system = platform.system()
    if system == "Darwin":
        return os.path.expanduser("~/Library/LaunchAgents/net.aiwf.runtime.plist")
    if system == "Windows":
        return "AIWF Runtime Daemon"
    return os.path.expanduser("~/.config/systemd/user/aiwf-runtime.service")

def runtime_bus_startup_folder_target() -> str:
    startup = os.path.join(
        os.environ.get("APPDATA", os.path.expanduser("~")),
        "Microsoft",
        "Windows",
        "Start Menu",
        "Programs",
        "Startup",
    )
    return os.path.join(startup, "AIWF Runtime Daemon.cmd")


def runtime_bus_legacy_launcher_target() -> str:
    return os.path.expanduser("~/.aiwf/runtime-daemon.cmd")


def runtime_bus_registration_marker() -> str:
    return os.path.expanduser("~/.aiwf/runtime-supervisor-registration.json")


def _windows_runtime_task_exists() -> bool:
    result = subprocess.run(
        ["schtasks", "/Query", "/TN", "AIWF Runtime Daemon"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def runtime_bus_autostart_diagnostics() -> dict[str, Any]:
    """Describe canonical and legacy registrations for AI/IDE parsers."""
    target = runtime_bus_autostart_target()
    startup = runtime_bus_startup_folder_target() if platform.system() == "Windows" else None
    legacy = runtime_bus_legacy_launcher_target() if platform.system() == "Windows" else None
    task_registered = (
        _windows_runtime_task_exists()
        if target == "AIWF Runtime Daemon"
        else os.path.exists(target)
    )
    fallback_marker = os.path.exists(runtime_bus_registration_marker())
    canonical_enabled = task_registered and not fallback_marker
    startup_enabled = bool(startup and os.path.exists(startup))
    canonical_owner = target if canonical_enabled else startup if startup_enabled else target
    duplicate_candidates = (startup, legacy) if canonical_enabled else (legacy,)
    duplicates = [path for path in duplicate_candidates if path and os.path.exists(path)]
    owners = [canonical_owner] if canonical_enabled or startup_enabled else []
    owners.extend(duplicates)
    conflict = {
        "conflict_type": "duplicate_autostart" if len(owners) > 1 else "none",
        "owners": owners,
        "resolution": "keep canonical OS supervisor and retire legacy launchers" if len(owners) > 1 else "none",
        "severity": "medium" if len(owners) > 1 else "none",
    }
    return {
        "canonical_target": canonical_owner,
        "canonical_enabled": canonical_enabled or startup_enabled,
        "registration": "scheduled_task" if canonical_enabled else "startup_folder_fallback" if startup_enabled else "none",
        "retired_registrations": [target] if task_registered and fallback_marker else [],
        "legacy_targets": duplicates,
        "duplicate_count": len(duplicates),
        "conflict": conflict,
        "enabled": canonical_enabled or startup_enabled,
    }

def is_runtime_bus_autostart_enabled() -> bool:
    return bool(runtime_bus_autostart_diagnostics()["enabled"])

def enable_runtime_bus_autostart() -> str:
    system = platform.system()
    log_file = os.path.expanduser("~/.aiwf/runtime.log")
    py = sys.executable
    target = runtime_bus_autostart_target()

    if system == "Darwin":
        import plistlib
        os.makedirs(os.path.dirname(target), exist_ok=True)
        plist = {
            "Label": "net.aiwf.runtime",
            "ProgramArguments": [py, "-m", "workflow_runtime", "runtime", "daemon"],
            "RunAtLoad": True,
            "KeepAlive": True,
            "StandardOutPath": log_file,
            "StandardErrorPath": log_file,
        }
        with open(target, "wb") as f:
            plistlib.dump(plist, f)
        return target

    if system == "Windows":
        cwd = _resolve_aiwf_project_root()
        launcher = os.path.expanduser("~/.aiwf/runtime-daemon.ps1")
        stop_marker = os.path.expanduser("~/.aiwf/runtime-stop.request")
        os.makedirs(os.path.dirname(launcher), exist_ok=True)
        if os.path.exists(stop_marker):
            os.remove(stop_marker)
        with open(launcher, "w", encoding="utf-8") as f:
            f.write(f'Set-Location -LiteralPath "{cwd}"\n')
            f.write(f'$env:PYTHONPATH = "{_runtime_pythonpath_root()};" + $env:PYTHONPATH\n')
            f.write(f'$env:AIWF_PROJECT_ROOT = "{cwd}"\n')
            f.write(f'$stopMarker = "{stop_marker}"\n')
            f.write('$restartCount = 0\n')
            f.write('while (-not (Test-Path -LiteralPath $stopMarker)) {\n')
            f.write(f'  & "{py}" -m workflow_runtime runtime daemon >> "{log_file}" 2>&1\n')
            f.write('  if (Test-Path -LiteralPath $stopMarker) { break }\n')
            f.write('  $restartCount = [Math]::Min($restartCount + 1, 6)\n')
            f.write('  Start-Sleep -Seconds ([Math]::Min(60, [Math]::Pow(2, $restartCount)))\n')
            f.write('}\n')
        cmd = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{launcher}"'
        try:
            subprocess.run(["schtasks", "/Create", "/TN", target, "/TR", cmd, "/SC", "ONLOGON", "/F"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            try:
                if os.path.exists(runtime_bus_registration_marker()):
                    os.remove(runtime_bus_registration_marker())
            except OSError:
                pass
        except subprocess.CalledProcessError as e:
            detail = (e.stderr or e.stdout or str(e)).strip()
            if "Access is denied" in detail:
                fallback = runtime_bus_startup_folder_target()
                os.makedirs(os.path.dirname(fallback), exist_ok=True)
                with open(fallback, "w", encoding="utf-8", newline="\n") as startup_file:
                    startup_file.write("@echo off\n")
                    startup_file.write(f' powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{launcher}"\n')
                with open(runtime_bus_registration_marker(), "w", encoding="utf-8") as marker_file:
                    json.dump({"registration": "startup_folder_fallback", "canonical_launcher": fallback}, marker_file)
                registration = "Startup Folder fallback"
                for stale in (runtime_bus_legacy_launcher_target(),):
                    try:
                        if os.path.exists(stale):
                            os.remove(stale)
                    except OSError:
                        pass
                print(f"[WARN] Scheduled Task access denied; installed canonical {registration}.", file=sys.stderr)
                return fallback
            raise RuntimeError(f"Failed to create Windows scheduled task '{target}': {detail}") from e
        # A single scheduled task owns the supervisor. Startup Folder and the
        # old global .cmd launcher are migration leftovers, never fallbacks.
        for stale in (runtime_bus_startup_folder_target(), runtime_bus_legacy_launcher_target()):
            try:
                if os.path.exists(stale):
                    os.remove(stale)
            except OSError:
                pass
        return target

    os.makedirs(os.path.dirname(target), exist_ok=True)
    service = f"""[Unit]
Description=AIWF Runtime Daemon

[Service]
ExecStart={py} -m workflow_runtime runtime daemon
Restart=always
StandardOutput=append:{log_file}
StandardError=append:{log_file}

[Install]
WantedBy=default.target
"""
    with open(target, "w", encoding="utf-8") as f:
        f.write(service)
    subprocess.run(["systemctl", "--user", "daemon-reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["systemctl", "--user", "enable", "aiwf-runtime.service"], check=True)
    return target

def disable_runtime_bus_autostart() -> str:
    import platform
    system = platform.system()
    target = runtime_bus_autostart_target()
    if system == "Windows":
        stop_marker = os.path.expanduser("~/.aiwf/runtime-stop.request")
        os.makedirs(os.path.dirname(stop_marker), exist_ok=True)
        Path(stop_marker).touch()
        try:
            if os.path.exists(runtime_bus_registration_marker()):
                os.remove(runtime_bus_registration_marker())
        except OSError:
            pass
        subprocess.run(["schtasks", "/Delete", "/TN", target, "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for stale in (runtime_bus_startup_folder_target(), runtime_bus_legacy_launcher_target()):
            try:
                if os.path.exists(stale):
                    os.remove(stale)
            except OSError:
                pass
        return target
    if system == "Linux":
        subprocess.run(["systemctl", "--user", "disable", "aiwf-runtime.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(target):
        os.remove(target)
    return target

# Functions below have been extracted to provider_context.py for 500-line compliance.
# Re-exported here for backward compatibility.
from workflow_runtime.presentation.cli.commands._impl.provider.provider_context import (  # noqa: E402, F401
    ensure_project_registered_from_config, get_current_project_context,
    has_global_telegram_token, print_project_context, process_runtime_bus_once,
    refresh_git_state_cache, refresh_initialize_dependencies)

__all__ = [
    "ensure_project_registered_from_config",
    "get_current_project_context",
    "has_global_telegram_token",
    "print_project_context",
    "process_runtime_bus_once",
    "refresh_git_state_cache",
    "refresh_initialize_dependencies"
]
