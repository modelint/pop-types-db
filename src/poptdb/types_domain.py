""" types_domain.py -- The Types Domain"""

# System
import logging
from pathlib import Path
import yaml
from typing import Any
from contextlib import redirect_stdout

def load_types(path: str | Path) -> dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class TypesDomain:
    """
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TypesDomain, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Avoid reinitialization if already initialized
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.types_path = None

    def initialize(self, types_path: Path):
        self.types_path = types_path
        tparse = load_types(types_path)
        pass





