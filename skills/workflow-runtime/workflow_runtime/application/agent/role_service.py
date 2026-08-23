import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from workflow_runtime.domain.agent.entities import AgentDef
from workflow_runtime.domain.workflow.value_objects import RoleId


@dataclass(frozen=True)
class RoleSummary:
    role_id: str
    name: str
    description: str
    file_path: str
    has_system_prompt: bool


class RoleService:
    """Application service for discovering, parsing, and validating agent role definitions."""

    def __init__(self, agents_dir: Path | str | None = None) -> None:
        self.agents_dir = self.resolve_agents_dir(agents_dir)

    def resolve_agents_dir(self, candidate_path: Path | str | None = None) -> Path:
        """Resolves target agents directory using fallback candidates.

        Raises:
            FileNotFoundError: If no valid agents directory is found.
        """
        if candidate_path:
            p = Path(candidate_path)
            if p.exists() and p.is_dir():
                return p.resolve()
            raise FileNotFoundError(f"Specified agents directory does not exist: {candidate_path}")

        root_dir = Path.cwd()
        candidates: list[Path] = [
            root_dir / ".agents" / "agents",
            root_dir / "agents",
            root_dir / ".agents" / "skills" / "workflow-runtime" / "agents",
        ]

        # Traverse upwards to find .agents/agents
        curr = root_dir
        for _ in range(5):
            candidates.append(curr / ".agents" / "agents")
            candidates.append(curr / "agents")
            if curr.parent == curr:
                break
            curr = curr.parent

        for path in candidates:
            if path.exists() and path.is_dir():
                return path.resolve()

        raise FileNotFoundError(
            f"Could not locate valid agents directory from candidates: {[str(c) for c in candidates[:3]]}"
        )

    def load_registry(self) -> dict[str, Any]:
        """Reads registry.json from agents_dir if present."""
        reg_file = self.agents_dir / "registry.json"
        if not reg_file.exists():
            return {}
        try:
            return json.loads(reg_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def validate_role(self, role_id: str) -> bool:
        """Validates that a role ID exists in registry.json or as a markdown file."""
        if not role_id:
            return False
        clean_id = role_id.strip()
        reg = self.load_registry()
        if (
            reg
            and "agents" in reg
            and isinstance(reg["agents"], dict)
            and clean_id in reg["agents"]
        ):
            return True
        md_file = self.agents_dir / f"{clean_id}.md"
        if md_file.exists():
            return True
        for f in self.agents_dir.glob("*.md"):
            if f.name.lower() == "readme.md":
                continue
            if f.stem == clean_id:
                return True
        return False

    def list_roles(self) -> list[str]:
        """Returns list of registered role IDs."""
        reg = self.load_registry()
        if reg and "agents" in reg and isinstance(reg["agents"], dict):
            agents_dict = cast(dict[str, Any], reg["agents"])
            return sorted([str(k) for k in agents_dict.keys()])

        roles: list[str] = []
        for f in self.agents_dir.glob("*.md"):
            if f.name.lower() == "readme.md":
                continue
            roles.append(f.stem)
        return sorted(roles)

    def parse_frontmatter(self, md_path: Path) -> dict[str, Any]:
        """Extracts YAML frontmatter metadata block and system prompt from a markdown file."""
        if not md_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {md_path}")
        content = md_path.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm_text = parts[1]
                body_text = parts[2].strip()
                metadata = self._parse_yaml(fm_text)
                sys_prompt = metadata.get("agy_system_prompt")
                if not sys_prompt:
                    sys_prompt = body_text
                return {"metadata": metadata, "agy_system_prompt": str(sys_prompt).strip()}
        return {"metadata": {}, "agy_system_prompt": content.strip()}

    def _parse_yaml(self, text: str) -> dict[str, Any]:
        try:
            import yaml

            res = yaml.safe_load(text)
            if isinstance(res, dict):
                return cast(dict[str, Any], res)
        except Exception:
            pass

        result: dict[str, Any] = {}
        for line in text.splitlines():
            line_s = line.strip()
            if not line_s or line_s.startswith("#"):
                continue
            if ":" in line_s and not line_s.startswith("-"):
                key, val = line_s.split(":", 1)
                key = key.strip()
                val = val.strip()
                if (val.startswith('"') and val.endswith('"')) or (
                    val.startswith("'") and val.endswith("'")
                ):
                    val = val[1:-1]
                result[key] = val
        return result

    def load_role(self, md_path: Path) -> AgentDef:
        """Parses an agent markdown file into an AgentDef entity.

        Raises:
            ValueError: If required frontmatter fields (name, description) are missing.
        """
        parsed = self.parse_frontmatter(md_path)
        metadata: dict[str, Any] = cast(dict[str, Any], parsed.get("metadata", {})) if isinstance(parsed.get("metadata"), dict) else {}
        name = metadata.get("name") or metadata.get("id") or md_path.stem
        desc = metadata.get("description") or metadata.get("role") or ""

        if not name or not desc:
            raise ValueError(f"Required frontmatter fields (name/description) missing in {md_path}")

        role_id = RoleId(value=str(name))
        agent_id = str(metadata.get("id") or name)
        display_name = str(metadata.get("display_name") or name)

        return AgentDef(
            agent_id=agent_id,
            role_id=role_id,
            name=display_name,
            description=str(desc),
        )

    def list_all_roles(self) -> list[AgentDef]:
        """Scans the agents directory and returns AgentDef entities for all markdown files."""
        defs: list[AgentDef] = []
        for md_path in sorted(self.agents_dir.glob("*.md")):
            if md_path.name.lower() == "readme.md":
                continue
            try:
                defs.append(self.load_role(md_path))
            except ValueError:
                continue
        return defs

    def list_role_summaries(self) -> list[RoleSummary]:
        """Returns RoleSummary DTOs for all discovered role definitions."""
        summaries: list[RoleSummary] = []
        for md_path in sorted(self.agents_dir.glob("*.md")):
            if md_path.name.lower() == "readme.md":
                continue
            parsed = self.parse_frontmatter(md_path)
            meta: dict[str, Any] = cast(dict[str, Any], parsed.get("metadata", {})) if isinstance(parsed.get("metadata"), dict) else {}
            r_id = meta.get("id") or meta.get("name") or md_path.stem
            name = meta.get("display_name") or meta.get("name") or md_path.stem
            desc = meta.get("description") or meta.get("role") or ""
            has_prompt = bool(parsed.get("agy_system_prompt"))
            summaries.append(
                RoleSummary(
                    role_id=str(r_id),
                    name=str(name),
                    description=str(desc),
                    file_path=str(md_path),
                    has_system_prompt=has_prompt,
                )
            )
        return summaries

    def validate_routing_graph(self, routing_table: dict[str, list[str]]) -> list[str]:
        """Performs DFS cycle detection on agent handoff chains.

        Returns:
            List of diagnostic error strings (empty if graph is acyclic and valid).
        """
        errors: list[str] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str, path: list[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in routing_table.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path + [neighbor])
                elif neighbor in rec_stack:
                    cycle_str = " -> ".join(path + [neighbor])
                    errors.append(f"Cycle detected in handoff chain: {cycle_str}")
            rec_stack.remove(node)

        for node in routing_table:
            if node not in visited:
                dfs(node, [node])

        return errors
