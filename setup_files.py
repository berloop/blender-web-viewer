#!/usr/bin/env python3
"""
File structure setup script for Blender Web Preview addon
Creates all the necessary directories and files
"""

import os
import shutil
import sys

# Define the base directory (where this script is located)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the directory structure
DIRECTORIES = [
    "server",
    "web",
    "web/css",
    "web/js",
    "web/assets"
]

# List of files to create and their contents
FILES = {
    "server/__init__.py": "# Server initialization file\n",
    "web/__init__.py": "# Web directory initialization file\n",
    "web/index.html": "# Will be replaced by actual HTML file\n",
    "web/css/style.css": "# Will be replaced by actual CSS file\n",
    "web/js/viewer.js": "# Will be replaced by actual JS file\n",
    "web/assets/__init__.py": "# Assets directory initialization file\n"
}

def create_directories():
    """Create the directory structure"""
    for directory in DIRECTORIES:
        dir_path = os.path.join(BASE_DIR, directory)
        if not os.path.exists(dir_path):
            print(f"Creating directory: {directory}")
            os.makedirs(dir_path)
        else:
            print(f"Directory already exists: {directory}")

def create_files():
    """Create necessary files"""
    for file_path, content in FILES.items():
        full_path = os.path.join(BASE_DIR, file_path)
        if not os.path.exists(full_path):
            print(f"Creating file: {file_path}")
            with open(full_path, 'w') as f:
                f.write(content)
        else:
            print(f"File already exists: {file_path}")

def copy_asset_files():
    """Copy asset files from script directory to addon directories"""
    # You can add additional file copying logic here if needed
    pass

def main():
    """Main function"""
    print("Setting up file structure for Blender Web Preview addon...")
    
    create_directories()
    create_files()
    copy_asset_files()
    
    print("File structure setup complete!")

if __name__ == "__main__":
    main()