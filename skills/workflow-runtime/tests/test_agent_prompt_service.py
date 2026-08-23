from workflow_runtime.application.agent.prompt_service import PromptService

def test_plain_agent_task_is_normalized_to_aiwf_entrypoint():
    service = PromptService()
    prompt = service.assemble_prompt(service.create_system_prompt("Base system prompt"), "sửa cli")

    assert "AIWF NATURAL PROMPT CONTRACT" in prompt
    assert "No blueprint - no code" in prompt
    assert prompt.endswith("/aiwf sửa cli")


def test_explicit_aiwf_agent_task_is_not_double_prefixed():
    service = PromptService()
    prompt = service.assemble_prompt(service.create_system_prompt("Base system prompt"), "/aiwf sửa cli")

    assert prompt.endswith("/aiwf sửa cli")
    assert "/aiwf /aiwf" not in prompt
