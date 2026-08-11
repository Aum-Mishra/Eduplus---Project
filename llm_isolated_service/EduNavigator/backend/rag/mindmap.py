import json
from pathlib import Path
from typing import Dict, Any

def load_mindmap(filename: str) -> Dict[str, Any]:
    """Load a mindmap from JSON file."""
    try:
        mindmap_path = Path(__file__).resolve().parent.parent / "storage" / "Mindmaps" / filename
        if mindmap_path.exists():
            with open(mindmap_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading mindmap {filename}: {e}")
    
    # Return a fallback minimal graph
    return {
        "nodes": [{"id": "Error", "label": "Error loading mindmap", "group": 1}],
        "links": []
    }