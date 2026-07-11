# File path: tests/unit/test_ports_manager.py
import unittest
import socket
from vir_runtime.sandbox.ports import PortManager

class TestPortsManager(unittest.TestCase):
    def test_find_available_port(self):
        port = PortManager.find_available_port()
        self.assertIsInstance(port, int)
        self.assertGreater(port, 0)

    def test_is_port_in_use(self):
        port = PortManager.find_available_port()
        # Port should not be in use initially
        self.assertFalse(PortManager.is_port_in_use(port))

        # Bind to port to simulate it being in use
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", port))
            s.listen(1)
            self.assertTrue(PortManager.is_port_in_use(port))
        finally:
            s.close()

if __name__ == "__main__":
    unittest.main()
