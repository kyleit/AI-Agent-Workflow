class QualityAnalyzer:
    def __init__(self, indexer):
        self.indexer = indexer

    def find_orphan_notes(self, docs_map: dict[str, str]) -> list[str]:
        # Identify notes that are never linked by any other note
        all_linked = set()
        for doc_name, content in docs_map.items():
            links = self.indexer.extract_backlinks(content)
            for l in links:
                all_linked.add(l.lower())
                
        orphans = []
        for doc_name in docs_map:
            # Strip extension and directory for comparison
            base_name = doc_name.split("/")[-1].replace(".md", "").lower()
            if base_name not in all_linked:
                orphans.append(doc_name)
        return orphans
