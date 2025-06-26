"""
Helper utilities
"""

import json
import os
from datetime import datetime

def load_json_config(filepath):
    """Load JSON configuration file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def get_timestamp():
    """Get current timestamp"""
    return datetime.now().isoformat()

def ensure_directory(path):
    """Ensure directory exists"""
    os.makedirs(path, exist_ok=True)
    return path

def format_size(bytes_size):
    """Format bytes size to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"