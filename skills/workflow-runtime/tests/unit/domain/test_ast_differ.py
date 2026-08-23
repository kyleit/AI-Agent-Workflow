import pytest
from workflow_runtime.domain.entities.ast import ASTNode
from workflow_runtime.domain.entities.patch import PatchOp
from workflow_runtime.domain.services.ast_differ import ASTDifferService
from workflow_runtime.domain.exceptions import InvalidPatchError

def test_ast_differ_replace_add_remove():
    old_ast = ASTNode(id="node1", type="Frame", properties={"color": "red", "x": 10}, children=[])
    new_ast = ASTNode(id="node1", type="Frame", properties={"color": "blue", "y": 20}, children=[])
    
    differ = ASTDifferService()
    patches = differ.diff_ast(old_ast, new_ast)
    
    assert len(patches) == 3
    
    # Apply patch back
    patched_ast = differ.apply_patch(old_ast, patches)
    assert patched_ast.properties["color"] == "blue"
    assert "x" not in patched_ast.properties
    assert patched_ast.properties["y"] == 20

def test_invalid_patch():
    ast = ASTNode(id="1", type="Frame", properties={}, children=[])
    differ = ASTDifferService()
    with pytest.raises(InvalidPatchError):
        differ.apply_patch(ast, [PatchOp(op="remove", path="/invalid_path/123")])
