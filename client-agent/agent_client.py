#!/usr/bin/env python3
# agent_client.py — entrypoint for PySide6 UI
from __future__ import annotations

import sys
from PySide6 import QtWidgets
from ui import run_app

def main() -> None:
    sys.exit(run_app())

if __name__ == "__main__":
    main()
