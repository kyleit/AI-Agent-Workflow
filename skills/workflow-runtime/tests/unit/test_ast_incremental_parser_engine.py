import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from ast_incremental_parser_engine import ASTIncrementalParser
import sqlite3

def test_ast_parser_indexing(tmp_path):
    db_file = tmp_path / "codedb.db"
    code_file = tmp_path / "sample.py"
    
    with open(code_file, "w", encoding="utf-8") as f:
        f.write("def calculate_sum(a, b):\n    return a + b\n\nclass Engine:\n    pass")
        
    parser = ASTIncrementalParser(db_path=str(db_file))
    parser.parse_file(str(code_file))
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("SELECT symbol_name, symbol_type FROM symbols ORDER BY line_no;")
    rows = cursor.fetchall()
    
    assert len(rows) == 2
    assert rows[0] == ("calculate_sum", "function")
    assert rows[1] == ("Engine", "class")
    conn.close()
