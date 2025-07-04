""" types_domain.py -- The Types Domain"""

# System
import logging
from pathlib import Path
import yaml
from typing import Any
from contextlib import redirect_stdout
from collections import namedtuple


# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# Populate Types DB
from poptdb.typesdb_nt import *

tdb = "typesdb"

RangeExtent = namedtuple('RangeExtent', ['value', 'extent', 'exclusive'])

_logger = logging.getLogger(__name__)

def load_types(path: str | Path) -> dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def parse_range(range_str: str):
    range_str = range_str.strip()

    # Get exclusive flags from the brackets
    left = range_str[0]
    right = range_str[-1]
    min_exclusive = (left == '(')
    max_exclusive = (right == ')')

    # Extract and split the inner range
    inner = range_str[1:-1].strip()
    parts = [p.strip() for p in inner.split(',')]

    return [
        RangeExtent(value=parts[0], extent='min', exclusive=min_exclusive),
        RangeExtent(value=parts[1], extent='max', exclusive=max_exclusive),
    ]


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
        self.output_fname = "typesdb"  # If no name is specified at initialize
        self.tdb_path = Path(__file__).parent / 'typesdb.ral'  # Empty types database
        self.forward_types = list()
        self.inserted_types = set()

    def initialize(self, types_path: Path, output_fname: str):
        self.types_path = types_path
        self.tparse = load_types(types_path)
        self.output_fname = output_fname if output_fname else self.output_fname

        # Initiate a connection to the TclRAL database
        from pyral.database import Database  # Metamodel load or creates has already initialized the DB session
        _logger.info("Initializing TclRAL database connection")
        Database.open_session(tdb)

        # Start with an empty metamodel repository
        _logger.info("Loading Blueprint Types schema")
        Database.load(db=tdb, fname=str(self.tdb_path))

        self.pop_base_types()
        self.pop_utility_types()
        self.pop_domain_types()
        self.print()
        Database.save(db=tdb, fname=f"{self.output_fname}.ral")

    def print(self):
        """
        Print out the user domain schema
        """
        with open(f"{self.output_fname}.txt", 'w') as f:
            with redirect_stdout(f):
                Relvar.printall(db=tdb)



    def pop_domain_types(self):
        """

        """
        domain_tr = "domain"
        for type_name, type_data in self.tparse['Domain Types'].items():

            # Create User Type and Inheritance
            Transaction.open(db=tdb, name=domain_tr)
            Relvar.insert(db=tdb, relvar="Type", tuples=[Type_i(Name=type_name), ], tr=domain_tr)
            Relvar.insert(db=tdb, relvar="User Type", tuples=[
                User_Type_i(Name=type_name, Category="domain")
            ], tr=domain_tr)
            # TODO: Process operator exclusion

            # In most cases the type has only a single unnamed component and we just name it "value"
            num_components = len(type_data['components'])
            component_name = "value"
            if num_components == 0:
                pass  # TODO: must be at least one error
            elif num_components > 1:
                component_name = type_data["name"]

            for c in type_data['components']:
                self.pop_component(ut_name=type_name, c_name=component_name, c_parse=c, tr=domain_tr)
            ops = type_data.get('operators')
            if ops:
                for o in ops:
                    pass
            if self.forward_types:
                pass  # TODO: handle forward types
            Transaction.execute(db=tdb, name=domain_tr)
            self.inserted_types.add(type_name)

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

            # In most cases the type has only a single unnamed component and we just name it "value"
            num_components = len(type_data['components'])
            component_name = "value"
            if num_components == 0:
                pass  # TODO: must be at least one error
            elif num_components > 1:
                component_name = type_data["name"]

            for c in type_data['components']:
                self.pop_component(ut_name=type_name, c_name=component_name, c_parse=c, tr=utility_tr)
            ops = type_data.get('operators')
            if ops:
                add_ops = ops['add']
                if add_ops:
                    for o in add_ops:
                        Relvar.insert(db=tdb, relvar="Operator", tuples=[
                            Operator_i(Name=o, Type=type_name)
                        ], tr=utility_tr)
                x_ops = ops.get('exclude')
                if x_ops:
                    for o in x_ops:
                        pass
            if self.forward_types:
                pass  # TODO: handle forward types
            Transaction.execute(db=tdb, name=utility_tr)
            self.inserted_types.add(type_name)

    def pop_component(self, ut_name: str, c_name: str, c_parse, tr: str):
        """
        Insert component relations into the db

        :param ut_name:  Name of the User Type
        :param c_name:  Name of the component
        :param c_parse:  A parsed component record
        :param tr:  The open transaction for a User Type
        """
        inherited_type = c_parse["from"]
        if inherited_type not in self.inserted_types:
            # We can't inherit from this type yet, so we'll save it for a later pass
            self.forward_types.append({inherited_type: c_parse})
            return

        Relvar.insert(db=tdb, relvar="Inheritance", tuples=[
            Inheritance_i(User_type=ut_name, Inherited_type=inherited_type),
        ], tr=tr)

        Relvar.insert(db=tdb, relvar="Component", tuples=[
            Component_i(Name=c_name, User_type=ut_name)
        ], tr=tr)
        Relvar.insert(db=tdb, relvar="Value Subset", tuples=[
            Value_Subset_i(Component=c_name, User_type=ut_name,
                           Constrained_type=inherited_type)
        ], tr=tr)

        match inherited_type:
            case 'String':
                Relvar.insert(db=tdb, relvar="Constraint", tuples=[
                    Constraint_i(Component=c_name, User_type=ut_name)
                ], tr=tr)
                Relvar.insert(db=tdb, relvar="Regular Expression", tuples=[
                    Regular_Expression_i(Component=c_name, User_type=ut_name,
                                         Regex=c_parse["regex"])
                ], tr=tr)
                pass
            case 'Rational':
                rat_range = c_parse.get('range')
                if rat_range:
                    Relvar.insert(db=tdb, relvar="Constraint", tuples=[
                        Constraint_i(Component=c_name, User_type=ut_name)
                    ], tr=tr)
                    Relvar.insert(db=tdb, relvar="Rational Range", tuples=[
                        Rational_Range_i(Component=c_name, User_type=ut_name)
                    ], tr=tr)
                    for subrange in rat_range:
                        sr_parse = parse_range(subrange)
                        for extent in sr_parse:
                            if extent.value in {'min', 'max'}:
                                continue
                            Relvar.insert(db=tdb, relvar="Rational Extent", tuples=[
                                Integer_Extent_i(Component=c_name, User_type=ut_name, Value=float(extent.value),
                                                 Direction=extent.extent, Exclusive=extent.exclusive)
                            ], tr=tr)
                pass
            case 'Integer':
                int_range = c_parse.get('range')
                if int_range:
                    Relvar.insert(db=tdb, relvar="Constraint", tuples=[
                        Constraint_i(Component=c_name, User_type=ut_name)
                    ], tr=tr)
                    Relvar.insert(db=tdb, relvar="Integer Range", tuples=[
                        Integer_Range_i(Component=c_name, User_type=ut_name)
                    ], tr=tr)
                    for subrange in int_range:
                        sr_parse = parse_range(subrange)
                        for extent in sr_parse:
                            if extent.value in {'min', 'max'}:
                                continue
                            Relvar.insert(db=tdb, relvar="Integer Extent", tuples=[
                                Integer_Extent_i(Component=c_name, User_type=ut_name, Value=int(extent.value),
                                                 Direction=extent.extent, Exclusive=extent.exclusive)
                                          ], tr=tr)
                        pass

                pass
            case 'Boolean':
                symbols = c_parse.get('symbols')
                if symbols:
                    tsym, fsym = symbols
                    Relvar.insert(db=tdb, relvar="Constraint", tuples=[
                        Constraint_i(Component=c_name, User_type=ut_name)
                    ], tr=tr)
                    Relvar.insert(db=tdb, relvar="Boolean Symbol Pair", tuples=[
                        Boolean_Symbol_Pair_i(Component=c_name, User_type=ut_name, True_symbol=tsym, False_symbol=fsym)
                    ], tr=tr)
            case 'Symbol':
                pass
            case _:
                rule = c_parse.get('rule')
                if rule:
                    pass  # TODO: create rule

        pass

        #
        #             # TODO: inclusive / exclusive
        #             pass
        #     case 'Rational':
        #         pass  # TODO: Rational Range
        #     case 'Boolean':
        #         pass  # TODO: General rule
        #     case _:
        #         pass  # TODO: Throw exception

    def pop_base_types(self):
        basetr = "basetype"
        inserted_platforms = set()
        for type_name, type_data in self.tparse['Base Types'].items():
            Transaction.open(db=tdb, name=basetr)
            Relvar.insert(db=tdb, relvar="Type", tuples=[Type_i(Name=type_name),], tr=basetr)
            Relvar.insert(db=tdb, relvar="Base Type", tuples=[Base_Type_i(Name=type_name)], tr=basetr)
            for pname, physical_name in type_data["platforms"].items():
                # Insert the Platform tuple if it hasn't already been encountered
                if pname not in inserted_platforms:
                    Relvar.insert(db=tdb, relvar="Platform", tuples=[
                        Platform_i(Name=pname)
                    ], tr=basetr)
                    inserted_platforms.add(pname)
                Relvar.insert(db=tdb, relvar="Implementation", tuples=[
                    Implementation_i(Base_type=type_name, Platform=pname, Physical_type=physical_name)
                ], tr=basetr)
            operators = type_data.get("operators")
            if operators:
                for o in operators:
                    Relvar.insert(db=tdb, relvar="Operator", tuples=[
                        Operator_i(Name=o, Type=type_name)
                    ], tr=basetr)
            Transaction.execute(db=tdb, name=basetr)
            self.inserted_types.add(type_name)
            pass
        pass






