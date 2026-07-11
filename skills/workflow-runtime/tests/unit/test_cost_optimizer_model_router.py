import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from cost_optimizer_model_router import ModelRouter

def test_model_router():
    router = ModelRouter()
    assert router.route_task("HIGH") == "gemini-ultra"
    assert router.route_task("LOW") == "gemini-flash"
