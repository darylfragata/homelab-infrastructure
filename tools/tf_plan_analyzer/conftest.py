import sys
from pathlib import Path

# Ensure the project root is importable as top-level packages (models, parser,
# analyzers, risks, reporters, utils) regardless of pytest version/rootdir
# detection - mirrors how main.py itself is expected to be run.
sys.path.insert(0, str(Path(__file__).parent))
