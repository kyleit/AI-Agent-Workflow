# test_agents_merge.py
import unittest
import os
import shutil
import subprocess
import sys
import tempfile

class TestAgentsMerge(unittest.TestCase):
    def setUp(self):
        if sys.platform != "win32" and "powershell" in getattr(self, "_testMethodName", ""):
            self.skipTest("PowerShell only available on Windows")
            
        # Create a temporary sandbox directory
        self.test_dir = tempfile.mkdtemp()
        self.script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        
        # Prepare mock source files that the installer expects
        self.src_agents = os.path.join(self.script_dir, "AGENTS.md")
        self.src_rules = os.path.join(self.script_dir, "AI_RULES.md")
        self.src_manifest = os.path.join(self.script_dir, "MANIFEST.json")
        
        # We will run tests in the sandbox directory.
        # Initialize a git repo in sandbox because the installer requires it
        subprocess.run(["git", "init"], cwd=self.test_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Set dummy git config for commit (needed for clean git status checks)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.test_dir)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.test_dir)

        # Locate Git Bash if available on Windows, to avoid slow and hanging WSL bash
        bash_path = None
        for p in [
            "C:\\Program Files\\Git\\bin\\bash.exe",
            "C:\\Program Files\\Git\\usr\\bin\\bash.exe",
            os.path.expanduser("~\\AppData\\Local\\Programs\\Git\\bin\\bash.exe")
        ]:
            if os.path.exists(p):
                bash_path = p
                break
        
        if not bash_path:
            bash_path = shutil.which("bash")
            
        self.bash_path = bash_path
        self.has_bash = bash_path is not None
        
        self.bash_flavor = "gitbash"
        if self.has_bash:
            try:
                res = subprocess.run([self.bash_path, "-c", "if [ -d /mnt/c ]; then echo wsl; else echo gitbash; fi"], capture_output=True, text=True, timeout=5)
                self.bash_flavor = res.stdout.strip()
            except Exception:
                self.bash_flavor = "gitbash"

    def tearDown(self):
        # Clean up temporary sandbox directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _to_bash_path(self, path):
        path = path.replace("\\", "/")
        if len(path) > 1 and path[1] == ":":
            drive = path[0].lower()
            if self.bash_flavor == "wsl":
                path = f"/mnt/{drive}{path[2:]}"
            else:
                path = f"/{drive}{path[2:]}"
        return path

    def _run_install_powershell(self):
        install_script = os.path.join(self.script_dir, "install.ps1")
        res = subprocess.run([
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", install_script, "-Force"
        ], cwd=self.test_dir, capture_output=True, text=True)
        return res

    def _run_update_powershell(self):
        update_script = os.path.join(self.script_dir, "update.ps1")
        res = subprocess.run([
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", update_script, "-Force"
        ], cwd=self.test_dir, capture_output=True, text=True)
        return res

    def _run_install_bash(self):
        install_script = self._to_bash_path(os.path.join(self.script_dir, "install.sh"))
        res = subprocess.run([
            self.bash_path, install_script, "-f"
        ], cwd=self.test_dir, capture_output=True, text=True)
        return res

    def _run_update_bash(self):
        update_script = self._to_bash_path(os.path.join(self.script_dir, "update.sh"))
        res = subprocess.run([
            self.bash_path, update_script, "-f"
        ], cwd=self.test_dir, capture_output=True, text=True)
        return res

    # --- PowerShell tests ---
    def test_scenario_1_fresh_project_powershell(self):
        res = self._run_install_powershell()
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        
        agents_path = os.path.join(self.test_dir, ".agents", "AGENTS.md")
        self.assertTrue(os.path.exists(agents_path))
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("<!-- AIWF:RULES:BEGIN -->", content)
        self.assertIn("<!-- AIWF:RULES:END -->", content)

    def test_scenario_2_existing_agents_powershell(self):
        agents_path = os.path.join(self.test_dir, ".agents", "AGENTS.md")
        os.makedirs(os.path.dirname(agents_path), exist_ok=True)
        user_rules = "# User Custom Rules\n- Rule 1\n- Rule 2\n"
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(user_rules)
            
        res = self._run_install_powershell()
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("# User Custom Rules", content)
        self.assertIn("- Rule 1", content)
        self.assertIn("<!-- AIWF:RULES:BEGIN -->", content)
        self.assertIn("<!-- AIWF:RULES:END -->", content)

    def test_scenario_3_existing_managed_block_update_powershell(self):
        agents_path = os.path.join(self.test_dir, ".agents", "AGENTS.md")
        os.makedirs(os.path.dirname(agents_path), exist_ok=True)
        initial_content = (
            "# My Custom Rules\n\n"
            "<!-- AIWF:RULES:BEGIN -->\n"
            "Old rule blocks to be replaced\n"
            "<!-- AIWF:RULES:END -->\n\n"
            "# More custom rules"
        )
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(initial_content)
            
        self._run_install_powershell()
        res = self._run_update_powershell()
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("# My Custom Rules", content)
        self.assertIn("# More custom rules", content)
        self.assertNotIn("Old rule blocks to be replaced", content)
        self.assertIn("<!-- AIWF:RULES:BEGIN -->", content)
        self.assertIn("Load the workflow resources from:", content)
        self.assertIn("<!-- AIWF:RULES:END -->", content)

    def test_scenario_4_multiple_installs_powershell(self):
        self._run_install_powershell()
        self._run_install_powershell()
        self._run_install_powershell()
        
        agents_path = os.path.join(self.test_dir, ".agents", "AGENTS.md")
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertEqual(content.count("<!-- AIWF:RULES:BEGIN -->"), 1)
        self.assertEqual(content.count("<!-- AIWF:RULES:END -->"), 1)

    def test_scenario_5_corrupted_block_repair_powershell(self):
        agents_path = os.path.join(self.test_dir, ".agents", "AGENTS.md")
        os.makedirs(os.path.dirname(agents_path), exist_ok=True)
        initial_content = (
            "# My Custom Rules\n"
            "<!-- AIWF:RULES:BEGIN -->\n"
            "Dangling content without end tag"
        )
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(initial_content)
            
        res = self._run_install_powershell()
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("# My Custom Rules", content)
        self.assertEqual(content.count("<!-- AIWF:RULES:BEGIN -->"), 1)
        self.assertEqual(content.count("<!-- AIWF:RULES:END -->"), 1)

    def test_scenario_6_missing_both_tags_powershell(self):
        agents_path = os.path.join(self.test_dir, ".agents", "AGENTS.md")
        os.makedirs(os.path.dirname(agents_path), exist_ok=True)
        initial_content = "# My Custom Rules\nSome content without tags"
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(initial_content)
            
        res = self._run_install_powershell()
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("# My Custom Rules", content)
        self.assertIn("Some content without tags", content)
        self.assertIn("<!-- AIWF:RULES:BEGIN -->", content)
        self.assertIn("<!-- AIWF:RULES:END -->", content)

    def test_scenario_7_user_customization_outside_block_powershell(self):
        agents_path = os.path.join(self.test_dir, ".agents", "AGENTS.md")
        os.makedirs(os.path.dirname(agents_path), exist_ok=True)
        initial_content = (
            "<!-- AIWF:RULES:BEGIN -->\n"
            "rules\n"
            "<!-- AIWF:RULES:END -->\n"
            "User rule customized at bottom"
        )
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(initial_content)
            
        res = self._run_install_powershell()
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("User rule customized at bottom", content)
        self.assertIn("<!-- AIWF:RULES:BEGIN -->", content)

    # --- Bash tests (run only if bash is available) ---
    def test_scenario_1_fresh_project_bash(self):
        if not self.has_bash:
            self.skipTest("Bash shell not available")
            
        res = self._run_install_bash()
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        
        agents_path = os.path.join(self.test_dir, ".agents", "AGENTS.md")
        self.assertTrue(os.path.exists(agents_path))
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("<!-- AIWF:RULES:BEGIN -->", content)
        self.assertIn("<!-- AIWF:RULES:END -->", content)

    def test_scenario_2_existing_agents_bash(self):
        if not self.has_bash:
            self.skipTest("Bash shell not available")
            
        agents_path = os.path.join(self.test_dir, ".agents", "AGENTS.md")
        os.makedirs(os.path.dirname(agents_path), exist_ok=True)
        user_rules = "# User Custom Rules\n- Rule 1\n- Rule 2\n"
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(user_rules)
            
        res = self._run_install_bash()
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("# User Custom Rules", content)
        self.assertIn("- Rule 1", content)
        self.assertIn("<!-- AIWF:RULES:BEGIN -->", content)
        self.assertIn("<!-- AIWF:RULES:END -->", content)

    def test_scenario_3_existing_managed_block_update_bash(self):
        if not self.has_bash:
            self.skipTest("Bash shell not available")
            
        agents_path = os.path.join(self.test_dir, ".agents", "AGENTS.md")
        os.makedirs(os.path.dirname(agents_path), exist_ok=True)
        initial_content = (
            "# My Custom Rules\n\n"
            "<!-- AIWF:RULES:BEGIN -->\n"
            "Old rule blocks to be replaced\n"
            "<!-- AIWF:RULES:END -->\n\n"
            "# More custom rules"
        )
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(initial_content)
            
        self._run_install_bash()
        res = self._run_update_bash()
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("# My Custom Rules", content)
        self.assertIn("# More custom rules", content)
        self.assertNotIn("Old rule blocks to be replaced", content)
        self.assertIn("<!-- AIWF:RULES:BEGIN -->", content)
        self.assertIn("Load the workflow resources from:", content)
        self.assertIn("<!-- AIWF:RULES:END -->", content)

    def test_scenario_4_multiple_installs_bash(self):
        if not self.has_bash:
            self.skipTest("Bash shell not available")
            
        self._run_install_bash()
        self._run_install_bash()
        self._run_install_bash()
        
        agents_path = os.path.join(self.test_dir, ".agents", "AGENTS.md")
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertEqual(content.count("<!-- AIWF:RULES:BEGIN -->"), 1)
        self.assertEqual(content.count("<!-- AIWF:RULES:END -->"), 1)

    def test_scenario_5_corrupted_block_repair_bash(self):
        if not self.has_bash:
            self.skipTest("Bash shell not available")
            
        agents_path = os.path.join(self.test_dir, ".agents", "AGENTS.md")
        os.makedirs(os.path.dirname(agents_path), exist_ok=True)
        initial_content = (
            "# My Custom Rules\n"
            "<!-- AIWF:RULES:BEGIN -->\n"
            "Dangling content without end tag"
        )
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(initial_content)
            
        res = self._run_install_bash()
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("# My Custom Rules", content)
        self.assertEqual(content.count("<!-- AIWF:RULES:BEGIN -->"), 1)
        self.assertEqual(content.count("<!-- AIWF:RULES:END -->"), 1)

    def test_scenario_6_missing_both_tags_bash(self):
        if not self.has_bash:
            self.skipTest("Bash shell not available")
            
        agents_path = os.path.join(self.test_dir, ".agents", "AGENTS.md")
        os.makedirs(os.path.dirname(agents_path), exist_ok=True)
        initial_content = "# My Custom Rules\nSome content without tags"
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(initial_content)
            
        res = self._run_install_bash()
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("# My Custom Rules", content)
        self.assertIn("Some content without tags", content)
        self.assertIn("<!-- AIWF:RULES:BEGIN -->", content)
        self.assertIn("<!-- AIWF:RULES:END -->", content)

    def test_scenario_7_user_customization_outside_block_bash(self):
        if not self.has_bash:
            self.skipTest("Bash shell not available")
            
        agents_path = os.path.join(self.test_dir, ".agents", "AGENTS.md")
        os.makedirs(os.path.dirname(agents_path), exist_ok=True)
        initial_content = (
            "<!-- AIWF:RULES:BEGIN -->\n"
            "rules\n"
            "<!-- AIWF:RULES:END -->\n"
            "User rule customized at bottom"
        )
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(initial_content)
            
        res = self._run_install_bash()
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("User rule customized at bottom", content)
        self.assertIn("<!-- AIWF:RULES:BEGIN -->", content)

if __name__ == "__main__":
    unittest.main()
