from __future__ import annotations

from typing import Any

"""Commands: knowledge, search"""

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class KnowledgeCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "knowledge",
            category="knowledge",
            help="RAG vector knowledge base: index, query, status, rebuild",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("knowledge", help=self.meta().help)
        p.add_argument(
            "action",
            nargs="?",
            choices=["index", "query", "status", "rebuild", "clear", "export"],
            help="Knowledge action",
        )
        p.add_argument("--query", help="Semantic search query")
        p.add_argument("--limit", type=int, default=5,
                       help="Max results (default: 5)")
        p.add_argument("--provider",
                       choices=["qdrant", "sqlite", "memory"],
                       help="Vector store provider")
        p.add_argument("--collection", help="Collection/index name")
        p.add_argument("--format", choices=["json", "text"], default="text")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_knowledge_action
        do_knowledge_action(args)

    def print_help(self) -> None: self._parser.print_help()


class SearchCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "search",
            category="knowledge",
            help="Query RAG vector knowledge base (shorthand for 'knowledge query')",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("search", help=self.meta().help)
        p.add_argument("query", nargs="?", help="Search query string")
        p.add_argument("--query", dest="query_flag",
                       help="Search query (flag form)")
        p.add_argument("--limit", type=int, default=5)
        p.add_argument("--provider", help="Vector store provider")
        p.add_argument("--format", choices=["json", "text"], default="text")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_search_action
        do_search_action(args)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [KnowledgeCommand(), SearchCommand()]