#!/usr/bin/env python3
"""Quick run script for the GitHub Backlog Generator."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from github_backlog_generator.cli import main

if __name__ == '__main__':
    main()