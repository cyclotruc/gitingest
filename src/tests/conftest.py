import os
import sys

# Get the absolute path of the src directory
src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the path to PYTHONPATH
sys.path.insert(0, src_path) 