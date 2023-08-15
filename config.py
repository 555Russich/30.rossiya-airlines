import sys
from pathlib import Path

from my_logging import get_logger

if getattr(sys, 'frozen', False):
    DIR_PROJECT = Path(sys.executable).parent
else:
    DIR_PROJECT = Path(__file__).resolve().parent

DIR_REPORTS = DIR_PROJECT / 'Reports'
DIR_REPORTS.mkdir(exist_ok=True)

FILEPATH_LOGGER = DIR_PROJECT / 'rossiya_airlines.log'
FILEPATH_DEFAULT_AUTH = DIR_PROJECT / 'default_auth.txt'
FILEPATH_CA = DIR_PROJECT / 'chain.pem'
if not FILEPATH_CA.exists():
    raise LookupError(f'{FILEPATH_CA=} not exists')

get_logger(FILEPATH_LOGGER)
