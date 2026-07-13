# skill_migration.py
import json
import warnings
from typing import Any, Dict, List, Optional
from runtime_sdk import RuntimeSDKv3

class SkillValidationError(Exception):
    pass

class SkillManifestV3:
    def __init__(
        self,
        skill_id: str,
        version: str,
        capabilities: List[str],
        required_permissions: List[str],
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
        tool_requirements: List[str],
        runtime_requirements: Dict[str, Any]
    ) -> None:
        self.skill_id = skill_id
        self.version = version
        self.capabilities = capabilities
        self.required_permissions = required_permissions
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.tool_requirements = tool_requirements
        self.runtime_requirements = runtime_requirements

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "version": self.version,
            "capabilities": self.capabilities,
            "required_permissions": self.required_permissions,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "tool_requirements": self.tool_requirements,
            "runtime_requirements": self.runtime_requirements
        }

def validate_skill_manifest(manifest_dict: Dict[str, Any]) -> SkillManifestV3:
    required_keys = {
        "skill_id", "version", "capabilities", "required_permissions",
        "input_schema", "output_schema", "tool_requirements", "runtime_requirements"
    }
    for key in required_keys:
        if key not in manifest_dict:
            raise SkillValidationError(f"Missing required manifest field: '{key}'")
            
    return SkillManifestV3(
        skill_id=manifest_dict["skill_id"],
        version=manifest_dict["version"],
        capabilities=manifest_dict["capabilities"],
        required_permissions=manifest_dict["required_permissions"],
        input_schema=manifest_dict["input_schema"],
        output_schema=manifest_dict["output_schema"],
        tool_requirements=manifest_dict["tool_requirements"],
        runtime_requirements=manifest_dict["runtime_requirements"]
    )

class LegacySkillAdapter:
    def __init__(self, skill_id: str, sdk_v3: RuntimeSDKv3) -> None:
        self.skill_id = skill_id
        self.sdk = sdk_v3

    async def execute_legacy_flow(self, session_id: str, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Issue warning
        warnings.warn(
            f"Skill '{self.skill_id}' is running in legacy compatibility mode. Please upgrade to Skill Contract v3.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Emit legacy execution start event in event store
        await self.sdk._send_request(
            "submit_task",
            {
                "task_id": task_id,
                "session_id": session_id,
                "agent_id": "agent-legacy-adapter"
            }
        )
        
        # Emulate executing legacy logic and return result
        result = {"status": "success", "legacy_output": "migrated_execution_complete"}
        
        # Record output result
        if self.sdk.api_server:
            self.sdk.api_server.record_event(
                session_id,
                "skill.execution_completed",
                {"skill_id": self.skill_id, "result": result}
            )
            
        return result
