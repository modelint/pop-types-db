""" types_domain.py -- The Types Domain"""

# System
import logging
from pathlib import Path
import yaml
from typing import Any
from contextlib import redirect_stdout

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# Populate Types DB
from poptdb.typesdb_nt import *

_logger = logging.getLogger(__name__)

def load_types(path: str | Path) -> dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

tdb = "typesdb"


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
        self.tparse = None
        self.tdb_path = Path(__file__).parent / 'typesdb.ral'  # Empty types database

    def initialize(self, types_path: Path):
        self.types_path = types_path
        self.tparse = load_types(types_path)

        # Initiate a connection to the TclRAL database
        from pyral.database import Database  # Metamodel load or creates has already initialized the DB session
        _logger.info("Initializing TclRAL database connection")
        Database.open_session(tdb)

        # Start with an empty metamodel repository
        _logger.info("Loading Blueprint MBSE metamodel repository schema")
        Database.load(db=tdb, fname=str(self.tdb_path))

        self.pop_base_types()
        self.print()
        Database.save(db=tdb, fname=f"{tdb}.ral")

    def print(self):
        """
        Print out the user domain schema
        """
        with open(f"{tdb}.txt", 'w') as f:
            with redirect_stdout(f):
                Relvar.printall(db=tdb)


    def pop_base_types(self):
        basetr = "basetype"
        inserted_platforms = set()
        for type_name, platforms in self.tparse['Base Types'].items():
            Transaction.open(db=tdb, name=basetr)
            Relvar.insert(db=tdb, relvar="Type", tuples=[Type_i(Name=type_name),], tr=basetr)
            Relvar.insert(db=tdb, relvar="Base Type", tuples=[Base_Type_i(Name=type_name)], tr=basetr)
            for pname, physical_name in platforms.items():
                # Insert the Platform tuple if it hasn't already been encountered
                if pname not in inserted_platforms:
                    Relvar.insert(db=tdb, relvar="Platform", tuples=[
                        Platform_i(Name=pname)
                    ], tr=basetr)
                    inserted_platforms.add(pname)
                Relvar.insert(db=tdb, relvar="Implementation", tuples=[
                    Implementation_i(Base_type=type_name, Platform=pname, Physical_type=physical_name)
                ], tr=basetr)
            Transaction.execute(db=tdb, name=basetr)
            pass
        pass






