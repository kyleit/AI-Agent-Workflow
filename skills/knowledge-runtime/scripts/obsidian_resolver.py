# obsidian_resolver.py
import os

class ObsidianSectionResolver:
    def __init__(self, vault_path: str = "."):
        self.vault_path = os.path.abspath(vault_path)

    def extract_section(self, file_path: str, heading: str) -> str:
        full_path = os.path.abspath(os.path.join(self.vault_path, file_path))
        if not full_path.startswith(self.vault_path):
            raise PermissionError("Access denied: path is outside vault sandbox.")
            
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if not heading:
            return content
            
        # Parse content by headings
        lines = content.splitlines()
        section_lines = []
        capture = False
        target_level = 0
        
        # Normalize heading for match
        norm_target = heading.strip().lower().lstrip("#").strip()
        
        for line in lines:
            if line.startswith("#"):
                # Heading detected
                level = len(line) - len(line.lstrip("#"))
                norm_heading = line.lstrip("#").strip().lower()
                
                if capture:
                    if level <= target_level:
                        # Found heading at same or higher level, stop capturing
                        break
                    else:
                        section_lines.append(line)
                elif norm_heading == norm_target:
                    capture = True
                    target_level = level
                    section_lines.append(line)
            elif capture:
                section_lines.append(line)
                
        if not capture:
            # Fallback to whole file if heading is not found
            return content
            
        return "\n".join(section_lines)
