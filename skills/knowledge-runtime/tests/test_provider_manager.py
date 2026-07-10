import os
import unittest
import shutil
import tempfile
import sys
import warnings

# Ensure package directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from knowledge_runtime import provider_manager

class TestProviderManager(unittest.TestCase):
    def setUp(self):
        # Create temp home directory for global config testing
        self.temp_dir = tempfile.mkdtemp()
        self.old_home = os.environ.get("HOME")
        os.environ["HOME"] = self.temp_dir
        
        # Windows compatibility
        self.old_userprofile = os.environ.get("USERPROFILE")
        os.environ["USERPROFILE"] = self.temp_dir
        
        # Temp project directory
        self.project_dir = os.path.join(self.temp_dir, "my_project")
        os.makedirs(self.project_dir, exist_ok=True)
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        if self.old_home is not None:
            os.environ["HOME"] = self.old_home
        if self.old_userprofile is not None:
            os.environ["USERPROFILE"] = self.old_userprofile

    def test_global_config_path(self):
        path = provider_manager.get_global_config_path()
        self.assertIn(".aiwf", path)
        self.assertTrue(path.endswith("providers.json"))

    def test_load_save_global_config(self):
        # Initial config should be empty
        cfg = provider_manager.load_global_config()
        self.assertEqual(cfg, {"providers": {}})
        
        # Save config
        test_cfg = {
            "providers": {
                "obsidian": {
                    "enabled": True,
                    "host": "localhost"
                }
            }
        }
        status = provider_manager.save_global_config(test_cfg)
        self.assertTrue(status)
        
        # Load it back
        loaded = provider_manager.load_global_config()
        self.assertEqual(loaded["providers"]["obsidian"]["host"], "localhost")

    def test_merge_and_overrides(self):
        # Setup global config
        global_cfg = {
            "providers": {
                "obsidian": {
                    "enabled": True,
                    "mode": "rest",
                    "host": "127.0.0.1",
                    "api_key": "global-secret"
                }
            }
        }
        provider_manager.save_global_config(global_cfg)
        
        # Setup project config
        proj_dir_agents = os.path.join(self.project_dir, ".agents")
        os.makedirs(proj_dir_agents, exist_ok=True)
        proj_cfg_path = os.path.join(proj_dir_agents, "memory.config.json")
        proj_cfg = {
            "providers": {
                "obsidian": {
                    "enabled": True,
                    "mode": "file-sync"
                }
            }
        }
        import json
        with open(proj_cfg_path, "w", encoding="utf-8") as f:
            json.dump(proj_cfg, f)
            
        # Resolve config
        resolved = provider_manager.resolve_provider_config("obsidian", project_root=self.project_dir)
        self.assertEqual(resolved["mode"], "file-sync") # overridden
        self.assertEqual(resolved["api_key"], "global-secret") # inherited
        self.assertEqual(resolved["host"], "127.0.0.1") # inherited

    def test_env_var_resolution(self):
        os.environ["TEST_API_KEY"] = "my-secret-env-value"
        global_cfg = {
            "providers": {
                "obsidian": {
                    "api_key": "${TEST_API_KEY}"
                }
            }
        }
        provider_manager.save_global_config(global_cfg)
        resolved = provider_manager.resolve_provider_config("obsidian")
        self.assertEqual(resolved["api_key"], "my-secret-env-value")

    def test_secret_masking(self):
        cfg = {
            "api_key": "supersecret",
            "host": "127.0.0.1",
            "nested": {
                "token": "nestedsecret"
            }
        }
        masked = provider_manager.mask_secrets(cfg)
        self.assertEqual(masked["api_key"], "********")
        self.assertEqual(masked["host"], "127.0.0.1")
        self.assertEqual(masked["nested"]["token"], "********")

    def test_enable_disable_provider(self):
        provider_manager.enable_provider("obsidian")
        cfg = provider_manager.load_global_config()
        self.assertTrue(cfg["providers"]["obsidian"]["enabled"])
        
        provider_manager.disable_provider("obsidian")
        cfg = provider_manager.load_global_config()
        self.assertFalse(cfg["providers"]["obsidian"]["enabled"])

    def test_provider_status_and_test(self):
        # No config
        res = provider_manager.test_provider("openai")
        self.assertEqual(res["status"], "failure")
        
        # With config but disabled
        global_cfg = {
            "providers": {
                "openai": {
                    "enabled": False,
                    "api_key": "some-key"
                }
            }
        }
        provider_manager.save_global_config(global_cfg)
        res = provider_manager.test_provider("openai")
        self.assertIn("disabled", res["message"])
        
        # Enabled and verified
        provider_manager.enable_provider("openai")
        res = provider_manager.test_provider("openai")
        self.assertEqual(res["status"], "success")

    def test_vault_root_resolution_and_provisioning(self):
        vault_root = os.path.join(self.temp_dir, "GlobalVault")
        os.makedirs(vault_root, exist_ok=True)
        
        global_cfg = {
            "providers": {
                "obsidian": {
                    "enabled": True,
                    "mode": "file-sync",
                    "vault_root": vault_root,
                    "project_folder_pattern": "Test-Vault-{project_slug}",
                    "create_if_missing": True,
                    "sync_structure": True
                }
            }
        }
        provider_manager.save_global_config(global_cfg)
        
        # Resolve
        resolved = provider_manager.resolve_obsidian_project_folder(project_root=self.project_dir)
        expected_folder = os.path.join(vault_root, "Test-Vault-My_Project")
        self.assertEqual(resolved, expected_folder)
        self.assertTrue(os.path.exists(resolved))
        
        # Verify structure
        for sd in ["Brainstorming", "Plans", "Blueprints", "ADR", "Memory", "Releases"]:
            self.assertTrue(os.path.exists(os.path.join(resolved, sd)))
            
        # Verify README.md exists
        self.assertTrue(os.path.exists(os.path.join(resolved, "README.md")))

    def test_vault_path_backward_compatibility(self):
        vault_root = os.path.join(self.temp_dir, "LegacyVault")
        os.makedirs(vault_root, exist_ok=True)
        
        global_cfg = {
            "providers": {
                "obsidian": {
                    "enabled": True,
                    "mode": "file-sync",
                    "vault_path": vault_root,
                    "create_if_missing": True,
                    "sync_structure": False
                }
            }
        }
        provider_manager.save_global_config(global_cfg)
        
        # Resolve should treat vault_path as vault_root and trigger warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            resolved = provider_manager.resolve_obsidian_project_folder(project_root=self.project_dir)
            self.assertEqual(len(w), 1)
            self.assertIn("deprecated", str(w[0].message))
            
        self.assertIn("AIWF-Knowledge-My_Project", resolved)

    def test_path_traversal_prevention(self):
        vault_root = os.path.join(self.temp_dir, "SecureVault")
        os.makedirs(vault_root, exist_ok=True)
        
        global_cfg = {
            "providers": {
                "obsidian": {
                    "enabled": True,
                    "mode": "file-sync",
                    "vault_root": vault_root,
                    "project_folder_pattern": "../TraversalFolder",
                    "create_if_missing": True,
                    "sync_structure": False
                }
            }
        }
        provider_manager.save_global_config(global_cfg)
        
        with self.assertRaises(ValueError):
            provider_manager.resolve_obsidian_project_folder(project_root=self.project_dir)

    def test_folder_conflict_detection(self):
        vault_root = os.path.join(self.temp_dir, "ConflictVault")
        os.makedirs(vault_root, exist_ok=True)
        
        # Create folder that looks like it belongs to project B
        other_project_folder = os.path.join(vault_root, "AIWF-Knowledge-project-b")
        os.makedirs(other_project_folder, exist_ok=True)
        with open(os.path.join(other_project_folder, "README.md"), "w", encoding="utf-8") as f:
            f.write("# Project Metadata\nProject Slug: project-b\n")
            
        # Configure project A to resolve to the same folder by overriding pattern
        global_cfg = {
            "providers": {
                "obsidian": {
                    "enabled": True,
                    "mode": "file-sync",
                    "vault_root": vault_root,
                    "project_folder_pattern": "AIWF-Knowledge-project-b",
                    "create_if_missing": True,
                    "sync_structure": False
                }
            }
        }
        provider_manager.save_global_config(global_cfg)
        
        # Resolve for project A should fail because it conflicts with project B's slug in README
        with self.assertRaises(ValueError) as context:
            provider_manager.resolve_obsidian_project_folder(project_root=self.project_dir)
        self.assertIn("Conflict", str(context.exception))

    def test_sync_obsidian_file_sync(self):
        vault_root = os.path.join(self.temp_dir, "SyncVault")
        os.makedirs(vault_root, exist_ok=True)
        
        global_cfg = {
            "providers": {
                "obsidian": {
                    "enabled": True,
                    "mode": "file-sync",
                    "vault_root": vault_root,
                    "create_if_missing": True,
                    "sync_structure": True
                }
            }
        }
        provider_manager.save_global_config(global_cfg)
        
        # Create mock source file in project
        docs_dir = os.path.join(self.project_dir, "docs", "brainstorming")
        os.makedirs(docs_dir, exist_ok=True)
        mock_file = os.path.join(docs_dir, "idea.md")
        with open(mock_file, "w", encoding="utf-8") as f:
            f.write("My Brainstorming Idea")
            
        # Sync
        res = provider_manager.sync_obsidian(project_root=self.project_dir)
        self.assertEqual(res["status"], "success")
        
        # Verify file copied to Obsidian vault
        obsidian_folder = provider_manager.resolve_obsidian_project_folder(project_root=self.project_dir)
        target_file = os.path.join(obsidian_folder, "Brainstorming", "idea.md")
        self.assertTrue(os.path.exists(target_file))
        with open(target_file, "r", encoding="utf-8") as f:
            self.assertIn("My Brainstorming Idea", f.read())

    def test_sync_obsidian_readonly(self):
        vault_root = os.path.join(self.temp_dir, "ReadonlyVault")
        os.makedirs(vault_root, exist_ok=True)
        
        global_cfg = {
            "providers": {
                "obsidian": {
                    "enabled": True,
                    "mode": "readonly",
                    "vault_root": vault_root,
                    "create_if_missing": True,
                    "sync_structure": False
                }
            }
        }
        provider_manager.save_global_config(global_cfg)
        
        # Create mock source file
        docs_dir = os.path.join(self.project_dir, "docs", "brainstorming")
        os.makedirs(docs_dir, exist_ok=True)
        mock_file = os.path.join(docs_dir, "idea.md")
        with open(mock_file, "w", encoding="utf-8") as f:
            f.write("My Readonly Idea")
            
        res = provider_manager.sync_obsidian(project_root=self.project_dir)
        self.assertIn("docs/brainstorming/idea.md", res["stats"]["skipped_readonly"])
        
        # File should not exist in Obsidian
        obsidian_folder = provider_manager.resolve_obsidian_project_folder(project_root=self.project_dir)
        target_file = os.path.join(obsidian_folder, "Brainstorming", "idea.md")
        self.assertFalse(os.path.exists(target_file))

    def test_sync_obsidian_bidirectional_conflict(self):
        vault_root = os.path.join(self.temp_dir, "BidiVault")
        os.makedirs(vault_root, exist_ok=True)
        
        global_cfg = {
            "providers": {
                "obsidian": {
                    "enabled": True,
                    "mode": "bidirectional",
                    "vault_root": vault_root,
                    "create_if_missing": True,
                    "sync_structure": True
                }
            }
        }
        provider_manager.save_global_config(global_cfg)
        
        # Create mock source file
        docs_dir = os.path.join(self.project_dir, "docs", "brainstorming")
        os.makedirs(docs_dir, exist_ok=True)
        mock_file = os.path.join(docs_dir, "idea.md")
        with open(mock_file, "w", encoding="utf-8") as f:
            f.write("A")
            
        # First sync to populate sync map
        provider_manager.sync_obsidian(project_root=self.project_dir)
        
        # Modify both sides
        with open(mock_file, "w", encoding="utf-8") as f:
            f.write("B_AIWF")
            
        obsidian_folder = provider_manager.resolve_obsidian_project_folder(project_root=self.project_dir)
        target_file = os.path.join(obsidian_folder, "Brainstorming", "idea.md")
        with open(target_file, "w", encoding="utf-8") as f:
            f.write("C_OBSIDIAN")
            
        # Second sync should detect conflict
        res = provider_manager.sync_obsidian(project_root=self.project_dir)
        self.assertIn("docs/brainstorming/idea.md", res["stats"]["conflicts"])
        
        # Verify conflict report generated
        conflict_report = os.path.join(self.project_dir, ".agents", "knowledge", "conflicts", "docs_brainstorming_idea.md.json")
        self.assertTrue(os.path.exists(conflict_report))

    def test_multiple_projects_same_vault_root(self):
        vault_root = os.path.join(self.temp_dir, "MultiProjectVault")
        os.makedirs(vault_root, exist_ok=True)
        
        global_cfg = {
            "providers": {
                "obsidian": {
                    "enabled": True,
                    "mode": "file-sync",
                    "vault_root": vault_root,
                    "create_if_missing": True,
                    "sync_structure": False
                }
            }
        }
        provider_manager.save_global_config(global_cfg)
        
        # Project A
        proj_a = os.path.join(self.temp_dir, "project_a")
        os.makedirs(proj_a, exist_ok=True)
        # Project B
        proj_b = os.path.join(self.temp_dir, "project_b")
        os.makedirs(proj_b, exist_ok=True)
        
        folder_a = provider_manager.resolve_obsidian_project_folder(project_root=proj_a)
        folder_b = provider_manager.resolve_obsidian_project_folder(project_root=proj_b)
        
        self.assertNotEqual(folder_a, folder_b)
        self.assertIn("Project_A", folder_a)
        self.assertIn("Project_B", folder_b)

if __name__ == "__main__":
    unittest.main()
