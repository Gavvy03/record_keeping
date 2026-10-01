#!/usr/bin/env python3
"""Start the Streamlit app"""

import sys
try:
    import streamlit.web.cli as stcli
except ImportError:
    import streamlit.cli as stcli

if __name__ == "__main__":
    stcli.main(["run", "app/main.py"] + sys.argv[1:])

