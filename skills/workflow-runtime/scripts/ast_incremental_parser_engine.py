# ast_incremental_parser_engine.py
import ast
import sqlite3
import os

class ASTIncrementalParser:
    """
    FEAT-097: AST Incremental Parser Engine
    Indexes code symbols and definitions incrementally into SQLite database.
    """
    def __init__(self, db_path: str = ".agents/runtime/codedb.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS symbols (
                    file_path TEXT,
                    symbol_name TEXT,
                    symbol_type TEXT,
                    line_no INTEGER,
                    PRIMARY KEY (file_path, symbol_name)
                );
            """)
            conn.commit()
        finally:
            conn.close()

    def parse_file(self, file_path: str) -> None:
        if not os.path.exists(file_path):
            return
            
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
            
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return
            
        conn = sqlite3.connect(self.db_path)
        try:
            # Clean old symbols for this file (incremental update)
            conn.execute("DELETE FROM symbols WHERE file_path = ?;", (file_path,))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    conn.execute(
                        "INSERT OR REPLACE INTO symbols VALUES (?, ?, ?, ?);",
                        (file_path, node.name, "function", node.lineno)
                    )
                elif isinstance(node, ast.ClassDef):
                    conn.execute(
                        "INSERT OR REPLACE INTO symbols VALUES (?, ?, ?, ?);",
                        (file_path, node.name, "class", node.lineno)
                    )
            conn.commit()
        finally:
            conn.close()
