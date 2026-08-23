# test_safe_multi_agent_writes.py
import unittest
import os
import sys
import json
import shutil
import tempfile
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import safe_multi_agent_writes as smaw

class TestSafeMultiAgentWrites(unittest.TestCase):
    def setUp(self):
        self.temp_dir = os.path.abspath("./temp_test_concurrency")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.old_state_dir = smaw.STATE_DIR
        smaw.STATE_DIR = os.path.join(self.temp_dir, "state")
        os.makedirs(smaw.STATE_DIR, exist_ok=True)
        
    def tearDown(self):
        smaw.STATE_DIR = self.old_state_dir
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_execution_pattern_selection_mode_a(self):
        plan = smaw.AdaptiveTeamPlanner.plan_team(
            task_complexity="trivial",
            dependency_depth=1,
            independent_workstreams=1,
            shared_write_scope_count=0,
            estimated_coordination_cost=1.0,
            estimated_parallel_benefit=0.0,
            risk_level="low",
            specialized_roles=[],
            context_description="update a small config"
        )
        self.assertEqual(plan["execution_pattern"], "single_agent")
        self.assertEqual(plan["recommended_agent_count"], 1)
        self.assertEqual(plan["writer_count"], 1)

    def test_execution_pattern_selection_mode_b(self):
        plan = smaw.AdaptiveTeamPlanner.plan_team(
            task_complexity="medium",
            dependency_depth=2,
            independent_workstreams=1,
            shared_write_scope_count=2,
            estimated_coordination_cost=2.0,
            estimated_parallel_benefit=0.5,
            risk_level="medium",
            specialized_roles=["researcher", "coder"],
            context_description="audit codebase and refactor core modules"
        )
        self.assertEqual(plan["execution_pattern"], "multi_agent_research_single_writer")
        self.assertEqual(plan["writer_count"], 1)
        self.assertEqual(plan["recommended_agent_count"], 3)

    def test_execution_pattern_selection_mode_c(self):
        plan = smaw.AdaptiveTeamPlanner.plan_team(
            task_complexity="large",
            dependency_depth=1,
            independent_workstreams=3,
            shared_write_scope_count=0,
            estimated_coordination_cost=1.5,
            estimated_parallel_benefit=4.0,
            risk_level="low",
            specialized_roles=["coder"],
            context_description="implement independent features"
        )
        self.assertEqual(plan["execution_pattern"], "multi_writer_isolated")
        self.assertEqual(plan["writer_count"], 3)

    def test_release_single_agent_policy(self):
        plan = smaw.AdaptiveTeamPlanner.plan_team(
            task_complexity="small",
            dependency_depth=1,
            independent_workstreams=1,
            shared_write_scope_count=1,
            estimated_coordination_cost=1.0,
            estimated_parallel_benefit=0.0,
            risk_level="low",
            specialized_roles=["release_manager"],
            context_description="release v1.1.0: update changelog and tags"
        )
        self.assertEqual(plan["execution_pattern"], "single_agent")
        self.assertEqual(plan["recommended_agent_count"], 1)
        
        plan_high = smaw.AdaptiveTeamPlanner.plan_team(
            task_complexity="small",
            dependency_depth=1,
            independent_workstreams=1,
            shared_write_scope_count=1,
            estimated_coordination_cost=1.0,
            estimated_parallel_benefit=0.0,
            risk_level="high",
            specialized_roles=["release_manager"],
            context_description="release v1.1.0: update changelog and tags"
        )
        self.assertEqual(plan_high["execution_pattern"], "single_agent_with_verifier")
        self.assertEqual(plan_high["recommended_agent_count"], 2)
        self.assertEqual(plan_high["writer_count"], 1)
        self.assertEqual(plan_high["reviewer_count"], 1)

    def test_lease_acquisition_and_overlap(self):
        lease_a = smaw.LeaseManager.acquire_lease(
            owner_id="AGENT-A",
            scope="src/runtime",
            duration_seconds=100
        )
        self.assertEqual(lease_a["owner_id"], "AGENT-A")
        self.assertEqual(lease_a["fencing_token"], 1)
        
        with self.assertRaises(ValueError):
            smaw.LeaseManager.acquire_lease(
                owner_id="AGENT-B",
                scope="src/runtime/scheduler.py"
            )
            
        with self.assertRaises(ValueError):
            smaw.LeaseManager.acquire_lease(
                owner_id="AGENT-B",
                scope="."
            )
            
        lease_b = smaw.LeaseManager.acquire_lease(
            owner_id="AGENT-B",
            scope="src/frontend"
        )
        self.assertEqual(lease_b["owner_id"], "AGENT-B")
        
        renewed = smaw.LeaseManager.renew_lease(owner_id="AGENT-A", lease_id=lease_a["lease_id"])
        self.assertTrue(renewed)
        
        released = smaw.LeaseManager.release_lease(owner_id="AGENT-A", lease_id=lease_a["lease_id"])
        self.assertTrue(released)

    def test_optimistic_concurrency_control(self):
        target = os.path.join(self.temp_dir, "scheduler.py")
        with open(target, 'w', encoding='utf-8') as f:
            f.write("def schedule(): pass")
            
        state = smaw.ConcurrencyController.capture_base_state(target)
        expected_hash = state["base_hash"]
        
        lease = smaw.LeaseManager.acquire_lease(
            owner_id="AGENT-A",
            scope="temp_test_concurrency/scheduler.py"
        )
        
        success = smaw.AtomicWriter.atomic_replace(
            file_path=target,
            content="def schedule(): print('new')",
            expected_hash=expected_hash,
            owner_id="AGENT-A",
            fencing_token=lease["fencing_token"]
        )
        self.assertTrue(success)
        
        with self.assertRaises(ValueError):
            smaw.AtomicWriter.atomic_replace(
                file_path=target,
                content="def schedule(): print('newer')",
                expected_hash=expected_hash,
                owner_id="AGENT-A",
                fencing_token=lease["fencing_token"]
            )

    def test_stale_fencing_token(self):
        target = os.path.join(self.temp_dir, "scheduler.py")
        with open(target, 'w', encoding='utf-8') as f:
            f.write("pass")
            
        state = smaw.ConcurrencyController.capture_base_state(target)
        
        lease_a = smaw.LeaseManager.acquire_lease("AGENT-A", "temp_test_concurrency/scheduler.py")
        smaw.LeaseManager.release_lease("AGENT-A", lease_a["lease_id"])
        
        lease_b = smaw.LeaseManager.acquire_lease("AGENT-B", "temp_test_concurrency/scheduler.py")
        
        with self.assertRaises(ValueError):
            smaw.AtomicWriter.atomic_replace(
                file_path=target,
                content="write-b",
                expected_hash=state["base_hash"],
                owner_id="AGENT-A",
                fencing_token=lease_a["fencing_token"]
            )
            
        success = smaw.AtomicWriter.atomic_replace(
            file_path=target,
            content="write-b",
            expected_hash=state["base_hash"],
            owner_id="AGENT-B",
            fencing_token=lease_b["fencing_token"]
        )
        self.assertTrue(success)

    def test_path_traversal_rejection(self):
        with self.assertRaises(PermissionError):
            smaw.ConcurrencyController.validate_write(
                file_path="../outside_file.py",
                expected_hash="any",
                owner_id="AGENT-A",
                fencing_token=1
            )

    def test_integration_queue_and_rollback(self):
        patch_id = smaw.PatchIntegrationQueue.enqueue_patch(
            agent_id="AGENT-A",
            patch_content="FAIL_TEST patch content",
            base_commit="commit-1",
            changed_files=["src/scheduler.py"]
        )
        self.assertTrue(patch_id.startswith("patch-"))
        
        res = smaw.PatchIntegrationQueue.integrate_next("INTEGRATION-OWNER")
        self.assertEqual(res["status"], "failed")
        
        patch_overlap_id = smaw.PatchIntegrationQueue.enqueue_patch(
            agent_id="AGENT-B",
            patch_content="OVERLAP_CONFLICT content",
            base_commit="commit-1",
            changed_files=["src/scheduler.py"]
        )
        with self.assertRaises(ValueError):
            smaw.PatchIntegrationQueue.integrate_next("INTEGRATION-OWNER")

if __name__ == "__main__":
    unittest.main()
