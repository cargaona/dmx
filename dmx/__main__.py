#!/usr/bin/env python3
"""Main entry point for dmx."""

import sys
import os
import warnings

# Suppress pygame-related warnings and messages
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
warnings.filterwarnings('ignore', category=RuntimeWarning, module='importlib._bootstrap')

from dmx.cli import main

if __name__ == "__main__":
    main()