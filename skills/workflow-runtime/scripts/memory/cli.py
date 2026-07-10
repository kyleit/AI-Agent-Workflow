# cli.py
import argparse
import json
import sys
import os

# Đảm bảo đường dẫn import hoạt động tốt
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bootstrap import run_bootstrap
from update import run_update
from search import RAGSearcher

def main():
    parser = argparse.ArgumentParser(description="AI Workflow Framework Memory CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Memory subcommands")
    
    # Subcommand bootstrap
    subparsers.add_parser("bootstrap", help="Bootstrap project memory from scratch")
    
    # Subcommand update
    update_parser = subparsers.add_parser("update", help="Synchronize memory incrementally")
    update_parser.add_argument("--full", action="store_true", help="Force a full rebuild")
    
    # Subcommand search
    search_parser = subparsers.add_parser("search", help="Query RAG or local memory")
    search_parser.add_argument("query", type=str, help="Search query string")
    
    args = parser.parse_args()
    
    if args.command == "bootstrap":
        res = run_bootstrap()
        print(json.dumps(res, indent=2))
        sys.exit(0 if res.get("status") == "success" else 1)
        
    elif args.command == "update":
        res = run_update(force_full=args.full)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res.get("status") == "success" else 1)
        
    elif args.command == "search":
        searcher = RAGSearcher()
        res = searcher.execute_search(args.query)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res.get("status") == "success" else 1)
        
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
