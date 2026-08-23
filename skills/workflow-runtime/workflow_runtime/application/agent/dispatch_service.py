from __future__ import annotations

import concurrent.futures
import importlib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from workflow_runtime.application.agent.prompt_service import PromptService
from workflow_runtime.application.agent.role_service import RoleService
from workflow_runtime.application.ports.agy_port import IAGYPort


@dataclass(frozen=True)
class DispatchRequest:
    role_id: str
    task_description: str
    replacements: dict[str, str] = field(default_factory=dict[str, str])
    model: str = "gemini-3.6-flash-high"
    effort: str | None = None
    timeout_seconds: int = 300
    dry_run: bool = False


@dataclass(frozen=True)
class DispatchResult:
    status: str
    exit_code: int
    stdout: str
    stderr: str
    payload: dict[str, Any] = field(default_factory=dict[str, Any])


class AgentDispatchService:
    """Application service managing thread-safe asynchronous background agent dispatching."""

    def __init__(
        self,
        role_service: RoleService | None = None,
        prompt_service: PromptService | None = None,
        agy_adapter: IAGYPort | None = None,
        max_workers: int = 4,
    ) -> None:
        self.role_service = role_service or RoleService()
        self.prompt_service = prompt_service or PromptService()
        if agy_adapter is None:
            from workflow_runtime.application.ports.locator import (
                InfrastructureLocator)
            if getattr(InfrastructureLocator, "AgyAdapter", None) is not None:
                adapter_cls: Any = getattr(InfrastructureLocator, "AgyAdapter")
                agy_adapter = cast(IAGYPort, adapter_cls())
            else:
                mod = importlib.import_module("workflow_runtime.infrastructure.agy.agy_adapter")
                adapter_cls: Any = getattr(mod, "AGYAdapter")
                agy_adapter = cast(IAGYPort, adapter_cls())
        self.agy_adapter: IAGYPort = agy_adapter
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def get_agent_file(self, role_id: str) -> Path:
        agents_dir = self.role_service.agents_dir
        candidate = agents_dir / f"{role_id}.md"
        if candidate.exists():
            return candidate

        for f in agents_dir.glob("*.md"):
            if f.name.lower() == "readme.md":
                continue
            if f.stem == role_id:
                return f

        all_roles = self.role_service.list_all_roles()
        for agent_def in all_roles:
            if agent_def.role_id.value == role_id or agent_def.agent_id == role_id:
                target = agents_dir / f"{agent_def.agent_id}.md"
                if target.exists():
                    return target

        raise FileNotFoundError(f"Agent role definition for '{role_id}' not found in {agents_dir}")

    def build_dispatch_payload(
        self,
        role_id: str,
        task_description: str,
        replacements: dict[str, str] | None = None,
        model: str = "gemini-3.6-flash-high",
        effort: str | None = None,
    ) -> dict[str, Any]:
        md_path = self.get_agent_file(role_id)
        parsed = self.role_service.parse_frontmatter(md_path)
        sys_prompt_str = str(parsed.get("agy_system_prompt", ""))

        sys_prompt = self.prompt_service.create_system_prompt(sys_prompt_str)
        full_prompt = self.prompt_service.assemble_prompt(
            sys_prompt, task_description, replacements or {}
        )

        raw_meta = parsed.get("metadata")
        meta = cast(dict[str, Any], raw_meta) if isinstance(raw_meta, dict) else {}

        return {
            "role": role_id,
            "agent_file": str(md_path),
            "model": model,
            "effort": effort,
            "prompt": full_prompt,
            "metadata": meta,
        }

    def dispatch_agent(
        self,
        role: str,
        task: str,
        model: str | None = None,
        dry_run: bool = False,
        effort: str | None = None,
        timeout_seconds: int = 300,
        replacements: dict[str, str] | None = None,
    ) -> DispatchResult:
        model_name = model or "gemini-3.6-flash-high"
        payload = self.build_dispatch_payload(
            role_id=role,
            task_description=task,
            replacements=replacements,
            model=model_name,
            effort=effort,
        )

        command_args = self.agy_adapter.build_command(
            role_name=role,
            prompt=str(payload["prompt"]),
            model=model_name,
            effort=effort,
            timeout_seconds=timeout_seconds,
            add_dir=".",
        )

        exit_code, stdout, stderr = self.agy_adapter.execute_dispatch(
            command_args=command_args,
            dry_run=dry_run,
            timeout_seconds=timeout_seconds,
        )

        status = "SUCCESS" if exit_code == 0 else "FAILED"
        return DispatchResult(
            status=status,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            payload=payload,
        )

    def dispatch_async(
        self,
        role_id: str,
        task_fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> concurrent.futures.Future[Any]:
        return self._executor.submit(task_fn, *args, **kwargs)

    def get_active_worker_count(self) -> int:
        threads_raw: Any = getattr(self._executor, "_threads", None)
        if isinstance(threads_raw, (set, list, tuple)):
            threads_list = list(cast(Any, threads_raw))
            return len(threads_list)
        return 0

    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait)


__all__ = [
    "DispatchRequest",
    "DispatchResult",
    "AgentDispatchService",
]
