# test_project_memory.py
import unittest
import os
import shutil
import sys
import json
from unittest.mock import patch

# Thêm đường dẫn để import các module
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(TEST_DIR, "..", "scripts"))
sys.path.append(os.path.join(TEST_DIR, "..", "..", "..", "runtime", "scripts", "project_memory"))

class TestProjectMemoryEngine(unittest.TestCase):
    def setUp(self):
        # Thiết lập thư mục giả lập dự án
        self.test_root = os.path.join(TEST_DIR, "temp_test_project")
        os.makedirs(self.test_root, exist_ok=True)
        
        # Nạp trực tiếp các module nghiệp vụ
        import common
        import config
        import filesystem
        import git_diff
        import scanner
        import analyzer
        import sqlite_writer
        import search
        import bootstrap
        import update
        
        # Monkey patch get_project_root của từng module về thư mục test
        self.mock_func = lambda: self.test_root
        common.get_project_root = self.mock_func
        config.get_project_root = self.mock_func
        filesystem.get_project_root = self.mock_func
        git_diff.get_project_root = self.mock_func
        scanner.get_project_root = self.mock_func
        analyzer.get_project_root = self.mock_func
        sqlite_writer.get_project_root = self.mock_func
        search.get_project_root = self.mock_func
        bootstrap.get_project_root = self.mock_func
        update.get_project_root = self.mock_func
        
        # Enforce offline status for git tests
        git_diff.is_git_repository = lambda *args, **kwargs: False
        git_diff.get_uncommitted_files = lambda *args, **kwargs: []
        git_diff.get_changed_files = lambda *args, **kwargs: []
        
        # Tạo cấu hình bộ nhớ giả lập
        self.agents_dir = os.path.join(self.test_root, ".agents")

        os.makedirs(self.agents_dir, exist_ok=True)
        
        self.mem_config = {
            "project_id": "test-project",
            "memory_root": ".agents/memory",
            "vector_provider": "qdrant",
            "vector_collection": "test-project",
            "qmd_index": ".agents/memory/qmd.index"
        }
        with open(os.path.join(self.agents_dir, "memory.config.json"), "w", encoding="utf-8") as f:
            json.dump(self.mem_config, f)

    def tearDown(self):
        # Khôi phục các hàm nếu cần thiết
        # Xóa thư mục test
        if os.path.exists(self.test_root):
            shutil.rmtree(self.test_root)



    def test_bootstrap_empty_project(self):
        from bootstrap import run_bootstrap
        import config
        
        # Tạo một vài file mã nguồn giả lập
        os.makedirs(os.path.join(self.test_root, "src"), exist_ok=True)
        with open(os.path.join(self.test_root, "src", "main.py"), "w", encoding="utf-8") as f:
            _ = f.write("def hello():\n    print('hello')\n")
            
        # Chạy bootstrap
        res = run_bootstrap()
        self.assertEqual(res["status"], "success")
        
        # Kiểm tra sự hiện diện của các tệp tri thức
        mem_paths = config.get_memory_paths(self.mem_config)
        self.assertTrue(os.path.exists(mem_paths["summary"]))
        self.assertTrue(os.path.exists(os.path.join(mem_paths["architecture_dir"], "overview.md")))
        self.assertTrue(os.path.exists(os.path.join(mem_paths["memory_root"], "indexes", "file-map.json")))

    def test_update_incremental_timestamp(self):
        from bootstrap import run_bootstrap
        from update import run_update
        
        # Khởi tạo bộ nhớ trước
        run_bootstrap()
        
        # Giả lập thay đổi tệp tin bằng cách sửa file main.py và cập nhật timestamp
        src_dir = os.path.join(self.test_root, "src")
        os.makedirs(src_dir, exist_ok=True)
        main_py = os.path.join(src_dir, "main.py")
        
        # Đợi và ghi file mới
        with open(main_py, "w", encoding="utf-8") as f:
            _ = f.write("def hello_world():\n    print('hello world')\n")
            
        # Ép thời gian sửa đổi (mtime) của tệp này tăng thêm 10 giây
        import time
        future_time = time.time() + 10.0
        os.utime(main_py, (future_time, future_time))
            
        # Chạy update (dự án test không có git nên sẽ fallback sang timestamp)
        res = run_update()
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["data"]["files_changed_count"], 1)


    def test_rag_search_local_fallback(self):
        from bootstrap import run_bootstrap
        import config
        from search import RAGSearcher
        
        run_bootstrap()
        
        # Ghi một lỗi giả lập vào known-problems
        mem_paths = config.get_memory_paths(self.mem_config)
        with open(mem_paths["known_problems"], "w", encoding="utf-8") as f:
            f.write("# Known Problems\n\n## Visualizer Bug\n- **Problem**: Connection lost during sync.\n- **Fix**: Reconnect automatically.\n")
            
        # Tìm kiếm
        searcher = RAGSearcher()
        res = searcher.execute_search("connection")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["retrieval_level"], "Level 1 — Local Keyword Match")
        self.assertTrue(len(res["results"]) > 0)
        self.assertIn("Visualizer Bug", res["results"][0]["text"])


if __name__ == "__main__":
    unittest.main()
