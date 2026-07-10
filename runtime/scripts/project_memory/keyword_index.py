# keyword_index.py
import os
import re

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", 
    "any", "are", "arent", "as", "at", "be", "because", "been", "before", "being", 
    "below", "between", "both", "but", "by", "cant", "cannot", "could", "couldnt", 
    "did", "didnt", "do", "does", "doesnt", "doing", "dont", "down", "during", 
    "each", "few", "for", "from", "further", "had", "hadnt", "has", "hasnt", 
    "have", "havent", "having", "he", "hed", "hell", "hes", "her", "here", 
    "heres", "hers", "herself", "him", "himself", "his", "how", "hows", "i", 
    "id", "ill", "im", "ive", "if", "in", "into", "is", "isnt", "it", "its", 
    "itself", "lets", "me", "more", "most", "mustnt", "my", "myself", "no", 
    "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", 
    "our", "ours", "ourselves", "out", "over", "own", "same", "shant", "she", 
    "shed", "shell", "shes", "should", "shouldnt", "so", "some", "such", "than", 
    "that", "thats", "the", "their", "theirs", "them", "themselves", "then", 
    "there", "theres", "these", "they", "theyd", "theyll", "theyre", "theyve", 
    "this", "those", "through", "to", "too", "under", "until", "up", "very", 
    "was", "wasnt", "we", "wed", "well", "were", "weve", "werent", "what", 
    "whats", "when", "whens", "where", "wheres", "which", "while", "who", 
    "whos", "whom", "why", "whys", "with", "wont", "would", "wouldnt", "you", 
    "youd", "youll", "youre", "youve", "your", "yours", "yourself", "yourselves"
}

def extract_keywords(query: str) -> list[str]:
    """Tách query thành các từ khóa sạch (không gồm stop words)."""
    words = re.findall(r"\b[a-zA-Z0-9_-]+\b", query.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 1]

def search_in_markdown(file_path: str, keywords: list[str]) -> list[dict]:
    """Tìm kiếm từ khóa trong tệp tin và trả về các đoạn tương thích."""
    if not os.path.exists(file_path):
        return []
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return []
        
    # Chia nhỏ theo đoạn văn hoặc tiêu đề
    paragraphs = re.split(r"\n\n+", content)
    matches = []
    
    for idx, para in enumerate(paragraphs):
        para_clean = para.lower()
        score = 0
        for kw in keywords:
            if kw in para_clean:
                score += 1
                
        if score > 0:
            matches.append({
                "file": file_path,
                "paragraph_index": idx,
                "text": para.strip(),
                "score": score
            })
            
    # Sắp xếp theo score giảm dần
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches
