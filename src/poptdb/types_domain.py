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
        self.forward_types = list()
        self.inserted_types = set()

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
        self.pop_utility_types()
        self.print()
        Database.save(db=tdb, fname=f"{tdb}.ral")

    def print(self):
        """
        Print out the user domain schema
        """
        with open(f"{tdb}.txt", 'w') as f:
            with redirect_stdout(f):
                Relvar.printall(db=tdb)

    def pop_utility_types(self):
        """

        """
        utility_tr = "utility"
        for type_name, type_data in self.tparse['Utility Types'].items():

            # Create User Type and Inheritance
            Transaction.open(db=tdb, name=utility_tr)
            Relvar.insert(db=tdb, relvar="Type", tuples=[Type_i(Name=type_name), ], tr=utility_tr)
            Relvar.insert(db=tdb, relvar="User Type", tuples=[
                User_Type_i(Name=type_name, Category="utility")
            ], tr=utility_tr)
            # TODO: Process operator exclusion

            # Process either a single component or multi component type
            components = type_data.get("components")
            if components:
                pass  # TODO: Process multiple components
            else:
                # There's only one component in this User Type
                inherited_type = type_data["inherits"][0]
                constraint = type_data["inherits"][1:]
                if inherited_type not in self.inserted_types:
                    self.forward_types.append({type_name: type_data})
                    continue

                Relvar.insert(db=tdb, relvar="Inheritance", tuples=[
                    Inheritance_i(User_type=type_name, Inherited_type=inherited_type),
                ], tr=utility_tr)

                self.pop_component(user_type=type_name, inherited_type=inherited_type,
                                   constraint=constraint, tr=utility_tr)
            Transaction.execute(db=tdb, name=utility_tr)
            self.inserted_types.add(type_name)

    def pop_component(self, user_type: str, inherited_type: str, constraint, tr: str, comp_name: str = "value"):
        """

        :param user_type:
        :param inherited_type:
        :param constraint:
        :param comp_name:
        :param tr:
        """
        Relvar.insert(db=tdb, relvar="Component", tuples=[
            Component_i(Name=comp_name, User_type=user_type)
        ], tr=tr)
        Relvar.insert(db=tdb, relvar="Value Subset", tuples=[
            Value_Subset_i(Component=comp_name, User_type=user_type,
                           Constrained_type=inherited_type)
        ], tr=tr)
        match inherited_type:
            case 'String':
                Relvar.insert(db=tdb, relvar="Constraint", tuples=[
                    Constraint_i(Component=comp_name, User_type=user_type)
                ], tr=tr)
                Relvar.insert(db=tdb, relvar="Regular Expression", tuples=[
                    Regular_Expression_i(Component=comp_name, User_type=user_type,
                                         Regex=constraint)
                ], tr=tr)
            case 'Integer':
                Relvar.insert(db=tdb, relvar="Constraint", tuples=[
                    Constraint_i(Component=comp_name, User_type=user_type)
                ], tr=tr)
                Relvar.insert(db=tdb, relvar="Integer Range", tuples=[
                    Integer_Range_i(Component=comp_name, User_type=user_type)
                ], tr=tr)
                for r in constraint:
                    if (r[0] != 'min' and r[1] != 'max') and int(r[0]) > int(r[1]):
                        pass  # TODO: raise exception must be <=
                    Relvar.insert(db=tdb, relvar="Integer Subrange", tuples=[
                        Integer_Subrange_i(Component=comp_name, User_type=user_type,
                                           Min=r[0], Max=r[1])
                    ], tr=tr)

                    # TODO: inclusive / exclusive
                    pass
            case 'Rational':
                pass  # TODO: Rational Range
            case 'Boolean':
                pass  # TODO: General rule
            case _:
                pass  # TODO: Throw exception

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
            self.inserted_types.add(type_name)
            pass
        pass






