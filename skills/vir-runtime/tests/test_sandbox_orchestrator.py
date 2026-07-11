# File path: tests/unit/test_sandbox_orchestrator.py
import unittest
import asyncio
from vir_runtime.sandbox.ports import PortManager
from vir_runtime.sandbox.orchestrator import SandboxOrchestrator, TargetStartupTimeoutError

class TestSandboxOrchestrator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.port_manager = PortManager()

    async def test_sandbox_startup_and_teardown(self):
        # Find a free port dynamically
        port = self.port_manager.find_available_port()
        
        # Start a local python server on the free port in the sandbox
        cmd = f"python -m http.server --bind 127.0.0.1 {port}"
        orchestrator = SandboxOrchestrator(build_command="", dev_command=cmd, startup_timeout=15.0)
        
        try:
            await orchestrator.start_sandbox(port)
            # Verify port is indeed in use
            self.assertTrue(self.port_manager.is_port_in_use(port))
        finally:
            orchestrator.stop_sandbox()
            # Wait a moment for process to release port
            await asyncio.sleep(0.5)
            # Verify port is free again
            self.assertFalse(self.port_manager.is_port_in_use(port))

    async def test_sandbox_timeout(self):
        # Startup a server that binds to a different port to trigger timeout probe failure
        port = self.port_manager.find_available_port()
        wrong_port = port + 1
        
        cmd = f"python -m http.server {wrong_port}"
        orchestrator = SandboxOrchestrator(build_command="", dev_command=cmd, startup_timeout=0.5)
        
        with self.assertRaises(TargetStartupTimeoutError):
            await orchestrator.start_sandbox(port)
            
        orchestrator.stop_sandbox()
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    unittest.main()
