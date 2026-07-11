import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from plugin_marketplace_engine import PluginMarketplaceEngine

def test_marketplace():
    mp = PluginMarketplaceEngine()
    assert mp.install_plugin("SkillX", "VALID_SIGNATURE") is True
    assert mp.install_plugin("SkillY", "INVALID_SIGNATURE") is False
