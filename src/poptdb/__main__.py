"""
Blueprint Domain Type DB Populator

"""
import logging
import logging.config
import sys
import os
import argparse
from pathlib import Path
from poptdb.types_domain import TypesDomain
from poptdb import version
import atexit

_logpath = Path("pop_typesdb.log")
_progname = 'Blueprint Type Populator'

def clean_up():
    """Normal and exception exit activities"""
    _logpath.unlink(missing_ok=True)


def get_logger():
    """Initiate the logger"""
    log_conf_path = Path(__file__).parent / 'log.conf'  # Logging configuration is in this file
    logging.config.fileConfig(fname=log_conf_path, disable_existing_loggers=False)
    return logging.getLogger(__name__)  # Create a logger for this module


# Configure the expected parameters and actions for the argparse module
def parse(cl_input):
    parser = argparse.ArgumentParser(description=_progname)
    parser.add_argument('-t', '--types', action='store',
                        help='Path to the types yaml file')
    parser.add_argument('-D', '--debug', action='store_true',
                        help='Debug mode'),
    parser.add_argument('-L', '--log', action='store_true',
                        help='Generate a diagnostic log file')
    parser.add_argument('-V', '--version', action='store_true',
                        help='Print the current version of the repo populator')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose messages')
    return parser.parse_args(cl_input)


def main():
    # Start logging
    logger = get_logger()
    logger.info(f'{_progname} version: {version}')

    # Parse the command line args
    args = parse(sys.argv[1:])

    if args.version:
        # Just print the version and quit
        print(f'{_progname} version: {version}')
        sys.exit(0)

    if not args.log:
        # If no log file is requested, remove the log file before termination
        atexit.register(clean_up)

    # Types path specified
    if args.types:
        types_path = Path(args.types).resolve()
        t = TypesDomain()
        t.initialize(types_path=types_path)

    logger.info("No problemo")  # We didn't die on an exception, basically
    if args.verbose:
        print("\nNo problemo")

    logging.shutdown()

if __name__ == "__main__":
    main()
