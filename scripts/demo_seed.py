"""Thin wrapper kept for the documented path:

    cd backend && uv run python ../scripts/demo_seed.py

The seed logic now lives in the backend package at src/scripts/seed_demo.py so it
can also run inside the backend Docker image (python -m src.scripts.seed_demo).
"""

import asyncio
import os
import sys

# Make the backend package importable when run from the repo root or backend/.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from src.scripts.seed_demo import main  # noqa: E402

if __name__ == "__main__":
    asyncio.run(main())
