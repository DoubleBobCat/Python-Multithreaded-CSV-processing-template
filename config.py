# MODULE
import threading
from typing import Dict, Any
import time
import queue

# ------------------ Init Const ------------------ #
DEBUG_SWITCH = False

BASIC_CONFIG = {
    "DATA_SOURCE_DIR": '../../vcf_split/',
    "DATA_OUTPUT_DIR": '../../csv_first/',
    "DATA_FILE_RENAME_FILE": None,
    "DATA_ROW_RENAME_FILE": None,
    "DATA_COL_RENAME_FILE": None,
    "TRACK_SWITCH": True,
    "INFO_LOG_SWITCH": False,
    "ERROR_LOG_SWITCH": True,
    "LOG_OUTPUT_DIR": None,
    "PRINT_INTERVAL_SECONDS": 2,
    "ROW_SHARD_COUNT": 6,
    "COL_SHARD_COUNT": 1,
    "FILE_MAX_THREAD": 4,
    "CSV_PROCESS_MAX_THREAD": 6,
    "FRAME_EDGE": {
        "ROW_START": 0,
        "ROW_END": 0,
        "COL_START": 9,
        "COL_END": 0
    },
    "STATUS_CODE": {
        -1: "Ciallo~(∠・ω< )⌒★",
        0: "Pre Processing",
        1: "Processing",
        2: "Post Processing",
        3: "Finished"
    }
}

RUN_CONFIG = {
    "BASE_ORDER": {'A': 1, 'T': 2, 'U': 3, 'C': 4, 'G': 5, '*': 6, '-':7}
}

if BASIC_CONFIG["LOG_OUTPUT_DIR"] == None:
    INFO_FILE = BASIC_CONFIG["DATA_OUTPUT_DIR"] + 'INFO.log' \
        if BASIC_CONFIG["INFO_LOG_SWITCH"] else None
    ERROR_FILE = BASIC_CONFIG["DATA_OUTPUT_DIR"] + 'ERROR.log' \
        if BASIC_CONFIG["ERROR_LOG_SWITCH"] else None
else:
    INFO_FILE = BASIC_CONFIG["LOG_OUTPUT_DIR"] + 'INFO.log' \
        if BASIC_CONFIG["INFO_LOG_SWITCH"] else None
    ERROR_FILE = BASIC_CONFIG["LOG_OUTPUT_DIR"] + 'ERROR.log' \
        if BASIC_CONFIG["ERROR_LOG_SWITCH"] else None
    
if BASIC_CONFIG["FILE_MAX_THREAD"] == 0:
    FILE_MAX_THREAD = None
else:
    FILE_MAX_THREAD = BASIC_CONFIG["FILE_MAX_THREAD"]
if BASIC_CONFIG["CSV_PROCESS_MAX_THREAD"] == 0:
    CSV_PROCESS_MAX_THREAD = None
else:
    CSV_PROCESS_MAX_THREAD = BASIC_CONFIG["CSV_PROCESS_MAX_THREAD"]


# ------------------ Init Global Var ------------------ #
INFO_FILE_f = None
ERROR_FILE_f = None
DATA_FILE_RENAME_FILE_df = None
DATA_ROW_RENAME_FILE_df = None
DATA_COL_RENAME_FILE_df = None
force_exit = False
INFO_FILE_f_lock = threading.Lock()
ERROR_FILE_f_lock = threading.Lock()

update_progress_queue = queue.Queue()
status_data_dict: Dict[str, Dict[str, Any]] = {}
status_data_lock = threading.Lock()
last_print = time.time()
print_lock = threading.Lock()

# ------------------ Custom Var ------------------ #
base_ref = dict()
base_ref_lock = threading.Lock()