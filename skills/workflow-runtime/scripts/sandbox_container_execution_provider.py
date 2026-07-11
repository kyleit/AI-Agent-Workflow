# sandbox_container_execution_provider.py
class SandboxContainerProvider:
    """
    FEAT-094: Sandbox Container Execution Provider
    Interfaces with Docker sandboxes.
    """
    def __init__(self):
        self.containers = {}

    def run_container(self, container_id: str, command: str) -> str:
        self.containers[container_id] = "RUNNING"
        return "Command executed inside sandbox"

    def stop_container(self, container_id: str) -> None:
        if container_id in self.containers:
            self.containers[container_id] = "STOPPED"
