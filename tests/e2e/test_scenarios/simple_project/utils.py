"""
Utility functions for the simple project
"""

import os
from pathlib import Path

def get_project_root():
    """Get the project root directory"""
    return Path(__file__).parent

def read_config_file(filename):
    """Read a configuration file"""
    config_path = get_project_root() / filename
    if config_path.exists():
        with open(config_path, 'r') as f:
            return f.read()
    return None

def list_files_in_directory(directory):
    """List all files in a directory"""
    directory_path = Path(directory)
    if directory_path.exists() and directory_path.is_dir():
        return [f.name for f in directory_path.iterdir() if f.is_file()]
    return []