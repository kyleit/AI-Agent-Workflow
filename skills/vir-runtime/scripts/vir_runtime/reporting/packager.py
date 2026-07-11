# File path: vir_runtime/reporting/packager.py
import zipfile
import os
from typing import List

class ZipPackager:
    @staticmethod
    def create_session_zip(session_id: str, file_paths: List[str], output_zip_path: str) -> None:
        """Compile reports and screenshots as a standard zip archive payload."""
        print(f"[ZipPackager] Compiling session zip for session {session_id} to: {output_zip_path}")
        
        # Verify parent directories exist
        parent_dir = os.path.dirname(output_zip_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for path in file_paths:
                if os.path.exists(path):
                    # Add to zip, preserving relative basename structure
                    zip_file.write(path, os.path.basename(path))
                else:
                    print(f"[ZipPackager] Warning: File not found during packaging: {path}")
        print(f"[ZipPackager] Zip compile complete.")
