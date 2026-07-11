# File path: vir_runtime/sandbox/ports.py
import socket

class PortManager:
    @staticmethod
    def find_available_port() -> int:
        """Find a free localhost port using standard socket binding."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            port = s.getsockname()[1]
            return port

    @staticmethod
    def is_port_in_use(port: int) -> bool:
        """Check if a specific port is currently in use on localhost."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return False
            except socket.error:
                return True
