import os
import sys

# Get the absolute path of the project root directory (one level up from tests)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add both the project root and src directory to PYTHONPATH
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))
