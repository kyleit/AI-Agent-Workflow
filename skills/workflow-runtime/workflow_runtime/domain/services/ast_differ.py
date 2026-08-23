from __future__ import annotations

from workflow_runtime.domain.entities.ast import ASTNode
from workflow_runtime.domain.entities.patch import PatchOp
from workflow_runtime.domain.exceptions import InvalidPatchError


class ASTDifferService:
    def diff_ast(self, old_ast: ASTNode, new_ast: ASTNode) -> list[PatchOp]:
        patches: list[PatchOp] = []
        if old_ast.id != new_ast.id:
            patches.append(PatchOp(op="replace", path="/id", value=new_ast.id))

        for k, v in new_ast.properties.items():
            if k not in old_ast.properties or old_ast.properties[k] != v:
                patches.append(PatchOp(op="add" if k not in old_ast.properties else "replace", path=f"/properties/{k}", value=v))

        for k in old_ast.properties.keys():
            if k not in new_ast.properties:
                patches.append(PatchOp(op="remove", path=f"/properties/{k}"))

        return patches

    def apply_patch(self, target_ast: ASTNode, patches: list[PatchOp]) -> ASTNode:
        for patch in patches:
            parts = patch.path.strip("/").split("/")
            if not parts or not parts[0]:
                raise InvalidPatchError(f"Invalid path {patch.path}")

            if parts[0] == "id" and patch.op == "replace":
                target_ast.id = str(patch.value or "")
            elif parts[0] == "properties" and len(parts) == 2:
                prop = parts[1]
                if patch.op in ["add", "replace"]:
                    target_ast.properties[prop] = patch.value
                elif patch.op == "remove":
                    target_ast.properties.pop(prop, None)
            else:
                raise InvalidPatchError(f"Unsupported patch op {patch.op} on path {patch.path}")

        return target_ast


__all__ = ["ASTDifferService"]
