# MODULE
import threading
from typing import Dict, Any
import time

# ------------------ Init Const ------------------ #
BASIC_CONFIG = {
    "DATA_SOURCE_DIR": '../csv_simple/',
    "DATA_OUTPUT_DIR": '../csv_filted/',
    "DATA_FILE_RENAME_FILE": None,
    "DATA_ROW_RENAME_FILE": None,
    "DATA_COL_RENAME_FILE": None,
    "TRACK_SWITH": True,
    "INFO_LOG_SWITCH": False,
    "ERROR_LOG_SWITCH": True,
    "LOG_OUTPUT_DIR": None,
    "PRINT_INTERVAL_SECONDS": 2,
    "ROW_SHARD_COUNT": 1,
    "COL_SHARD_COUNT": 4,
    "FRAME_EDGE": {
        "ROW_START": 0,
        "ROW_END": 0,
        "COL_START": 0,
        "COL_END": 0
    },
    "STATUS_CODE": {
        0: "Pre Processing",
        1: "Processing",
        2: "Post Processing",
        3: "Finished"
    }
}

RUN_CONFIG = {
    "BASE_ORDER": {'A': 1, 'T': 2, 'U': 3, 'C': 4, 'G': 5, '*': 6}
}

if BASIC_CONFIG["LOG_OUTPUT_DIR"] == None:
    INFO_FILE = BASIC_CONFIG["DATA_OUT_DIR"] + 'INFO.log' \
        if BASIC_CONFIG["INFO_LOG_SWITCH"] else None
    ERROR_FILE = BASIC_CONFIG["DATA_OUT_DIR"] + 'ERROR.log' \
        if BASIC_CONFIG["ERROR_LOG_SWITCH"] else None
else:
    INFO_FILE = BASIC_CONFIG["LOG_OUTPUT_DIR"] + 'INFO.log' \
        if BASIC_CONFIG["INFO_LOG_SWITCH"] else None
    ERROR_FILE = BASIC_CONFIG["LOG_OUTPUT_DIR"] + 'ERROR.log' \
        if BASIC_CONFIG["ERROR_LOG_SWITCH"] else None


# ------------------ Init Global Var ------------------ #
INFO_FILE_f = None
ERROR_FILE_f = None
DATA_FILE_RENAME_FILE_df = None
DATA_ROW_RENAME_FILE_df = None
DATA_COL_RENAME_FILE_df = None
force_exit = False
INFO_FILE_f_lock = threading.Lock()
ERROR_FILE_f_lock = threading.Lock()

status_data_dict: Dict[str, Dict[str, Any]] = {}
status_data_lock = threading.Lock()
last_print = time.time()
print_lock = threading.Lock()
