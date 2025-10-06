"""Main package initialization."""

import sys
from pathlib import Path

# Add src directory to Python path for proper imports
src_dir = Path(__file__).parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))