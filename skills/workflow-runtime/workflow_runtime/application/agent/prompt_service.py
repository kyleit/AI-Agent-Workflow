from workflow_runtime.domain.agent.value_objects import SystemPrompt


class PromptService:
    """Application service for building and formatting system prompts with context variables."""

    NATURAL_AIWF_CONTRACT = (
        "AIWF NATURAL PROMPT CONTRACT: Treat this task as if the user invoked "
        "`/aiwf <task>`, even when `/aiwf` is not present. Run initialize-workflow "
        "and workflow-coordinator first. No blueprint - no code."
    )

    SUPPORTED_PLACEHOLDERS: tuple[str, ...] = (
        "<BLUEPRINT_PATH>",
        "<PLAN_PATH>",
        "<SPEC_PATH>",
        "<AUDITOR_REPORT_PATH>",
        "<MANAGER_REPORT_PATH>",
    )

    def create_system_prompt(self, template_str: str, version: str = "1.0.0") -> SystemPrompt:
        """Instantiates a validated SystemPrompt value object."""
        return SystemPrompt(template_str=template_str, version=version)

    def build_system_prompt(self, template_str: str, version: str = "1.0.0") -> SystemPrompt:
        """Alias for create_system_prompt."""
        return self.create_system_prompt(template_str=template_str, version=version)

    def inject_context(self, prompt_str: str, replacements: dict[str, str]) -> str:
        """Substitutes context placeholders into the prompt string."""
        res = prompt_str
        for k, v in replacements.items():
            res = res.replace(k, str(v))
            if not k.startswith("<"):
                res = res.replace(f"<{k}>", str(v))
            if not k.startswith("{"):
                res = res.replace(f"{{{k}}}", str(v))
        return res

    def format_task(self, task_description: str) -> str:
        """Formats plain text task specification."""
        if not task_description:
            return ""
        clean_task = task_description.strip()
        normalized_task = clean_task if clean_task.lower().startswith(("/aiwf", "@aiwf", "aiwf ")) else f"/aiwf {clean_task}"
        return f"### AIWF Natural Prompt Contract\n{self.NATURAL_AIWF_CONTRACT}\n\n### Current Task\n{normalized_task}"

    def assemble_prompt(
        self,
        system_prompt: SystemPrompt,
        task_description: str,
        replacements: dict[str, str] | None = None,
    ) -> str:
        """Substitutes context placeholders and appends task description.

        Args:
            system_prompt: Base SystemPrompt value object.
            task_description: Plain text task specification.
            replacements: Key-value map of placeholder substitutions.

        Returns:
            Fully assembled prompt string ready for LLM consumption.
        """
        base_prompt = self.inject_context(system_prompt.template_str, replacements or {})
        formatted_task = self.format_task(task_description)
        if formatted_task:
            return f"{base_prompt.strip()}\n\n{formatted_task}"
        return base_prompt.strip()
