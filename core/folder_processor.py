import os
from typing import List

def get_files_from_folder(folder_path: str, extensions: List[str]) -> List[str]:
    """Recursively finds files with specific extensions in a folder."""
    file_list = []
    if not os.path.exists(folder_path):
        return []
        
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if any(file.lower().endswith(ext.lower()) for ext in extensions):
                file_list.append(os.path.join(root, file))
    return file_list
