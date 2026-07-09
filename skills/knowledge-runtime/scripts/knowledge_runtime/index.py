import re

class KnowledgeIndexer:
    def __init__(self):
        pass

    def extract_backlinks(self, text: str) -> list[str]:
        # Matches wiki links like [[Some Note]]
        return re.findall(r"\[\[([^\]]+)\]\]", text)

    def extract_lessons(self, text: str) -> list[str]:
        # Matches lists under lessons learned or similar sections
        lessons = []
        pattern = re.compile(r"-\s+(Bài học|Lesson|Kinh nghiệm):\s*(.*)", re.IGNORECASE)
        for match in pattern.finditer(text):
            lessons.append(match.group(2).strip())
        return lessons
