# File path: tests/unit/test_sprint0_skeletons.py
import unittest
import os
import json
from vir_runtime.core.api import RuntimeAPIFacade
from vir_runtime.core.bus import WildcardEventBus

class TestSprint0Skeletons(unittest.TestCase):
    def test_api_facade(self):
        api = RuntimeAPIFacade()
        self.assertTrue(api.launch_browser({}))
        self.assertEqual(api.capture_screenshot(), b"")
        self.assertEqual(api.get_perf_metrics()["fps"], 60)

    def test_wildcard_event_bus(self):
        bus = WildcardEventBus()
        received = []
        
        def cb(topic, payload):
            received.append((topic, payload))
            
        bus.subscribe("test_topic", cb)
        bus.publish("test_topic", {"val": 123})
        
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][0], "test_topic")
        self.assertEqual(received[0][1]["val"], 123)

    def test_contracts_and_schemas_exist(self):
        contract_path = os.path.join("docs", "designs", "contracts", "runtime_request_contract.json")
        schema_path = os.path.join("docs", "designs", "schemas", "config_schema.json")
        
        self.assertTrue(os.path.exists(contract_path))
        self.assertTrue(os.path.exists(schema_path))
        
        with open(contract_path, "r", encoding="utf-8") as f:
            contract = json.load(f)
        self.assertEqual(contract["$contract"], "vir/runtime_request/v1")

if __name__ == "__main__":
    unittest.main()
