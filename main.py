#!/usr/bin/env python3
"""Entry point for running the Swing Trading Streamlit App"""

import sys
import os

# Ensure we can import from app directory
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Run with streamlit CLI
exec(open(os.path.join(app_dir, "app", "main.py")).read())
