import sys
import os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from ipc_websockets_sidecar_daemon import SidecarDaemon

@pytest.mark.asyncio
async def test_sidecar_daemon_lifecycle():
    daemon = SidecarDaemon()
    assert daemon.is_running is False
    await daemon.start()
    assert daemon.is_running is True
    await daemon.stop()
    assert daemon.is_running is False
