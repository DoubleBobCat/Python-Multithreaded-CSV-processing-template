# FILE
import config
import custom_func
# MODULE
import pandas as pd
import time
import os
import sys
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
from typing import Tuple
from prettytable import PrettyTable
import queue
import threading
from typing import Any


# [OK]
def signal_handler(sig, frame):
    """Process stop signal"""
    config.force_exit = True
    print("\nGet Exit signal, Exiting...")
    sys.exit(1)


# [OK]
def update_progress(file_name: str, argA: Any, argB: Any = False) -> None:
    # [OK]
    def update_progressA(file_name: str, process_add: int, data: str) -> None:
        """Update progress data"""
        # Update Process
        with config.status_data_lock:
            now_processed_count = config.status_data_dict[file_name]["processed_count"] + process_add
            config.status_data_dict[file_name].update({
                "processed_count": now_processed_count,
                "data": data
            })
        # Print
        print_progress_table()

    # [OK]
    def update_progressB(file_name: str, upate_data: dict, enforce: bool) -> None:
        # Update Process
        with config.status_data_lock:
            config.status_data_dict[file_name].update(upate_data)
        # Print
        print_progress_table(enforce)

    if type(argA) == int:
        update_progressA(file_name, argA, argB)
    elif type(argA) == dict:
        update_progressB(file_name, argA, argB)
    else:
        print(
            f"ERROR: UnExcept Exception in update_progress({file_name},{argA},{argB})")
        config.force_exit = True
        exit(2)
    # Check Exit
    if config.force_exit:
        sys.exit(1)


# [OK]
def update_progress_queue():
    """Update progress data queue"""
    while not config.force_exit:
        try:
            args = config.update_progress_queue.get(timeout=0.5)
            if args is None:
                break
            update_progress(*args)
        except queue.Empty:
            continue


# [OK]
def clear_screen():
    """Clean Bash Screen in different platform"""
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        os.system('clear')
    elif sys.platform.startswith('win32'):
        os.system('cls')


# [OK]
def format_time2str(seconds: float) -> str:
    """Format time to str"""
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


# [OK]
def format_progress_times(elapsed_time: float, remaining_time: float) -> Tuple[str, str]:
    """Format elapsed time& remaining time"""
    return format_time2str(elapsed_time), format_time2str(remaining_time)


# [OK]
def print_progress_table(enforce: bool = False) -> None:
    """Print Progress table"""
    now_time = time.time()

    with config.print_lock:
        if ((now_time - config.last_print) > config.BASIC_CONFIG["PRINT_INTERVAL_SECONDS"]) or enforce:
            # Init Progress table
            clear_screen()
            tb = PrettyTable(["File", "Processed", "Total",
                              "Elapsed", "Remaining", "Data", "Status"])
            with config.status_data_lock:
                # Add info to table
                for file_name, file_status_data in config.status_data_dict.items():
                    # Calculate elapsed time& remaining time
                    elapsed_time = now_time - file_status_data["start_time"]
                    this_elapsed_time = now_time - \
                        file_status_data["this_start_time"]

                    if (file_status_data["status"] != 3) and (file_status_data["status"] != -1):
                        # Calculate Processing ETH
                        processed_count = file_status_data["processed_count"]
                        all_count = file_status_data["all_count"]
                        if processed_count > 0:
                            remaining_time = (this_elapsed_time / processed_count) * \
                                (all_count - processed_count)
                        else:
                            remaining_time = 0
                        elapsed_str, remaining_str = format_progress_times(
                            elapsed_time, remaining_time)
                    else:
                        # Calculate Finished
                        elapsed_str = file_status_data["finished_elapsed_time_str"]
                        remaining_str = "00:00:00"

                    # Add line to table
                    tb.add_row([
                        file_name,
                        file_status_data["processed_count"],
                        file_status_data["all_count"],
                        elapsed_str,
                        remaining_str,
                        file_status_data["data"],
                        config.BASIC_CONFIG["STATUS_CODE"][file_status_data["status"]]
                    ])
            print(tb)
            config.last_print = time.time()


# [OK]
def get_shard(begin: int, end: int, shard_count: int) -> list:
    """Shard "shard_count" shardes from "begin" to "end", num begin at 0"""
    # Init
    Sharding = []
    count = end - begin + 1

    # Calculate items count per chunk
    if shard_count > 1:
        if (count % shard_count) == 0:
            per_chunk = count // shard_count
        else:
            per_chunk = count // shard_count + 1
    else:
        per_chunk = count

    # Shard
    for i in range(shard_count):
        chunk_begin = begin + i * per_chunk
        chunk_end = min(begin + (i + 1) * per_chunk - 1, end)

        if chunk_begin > chunk_end:
            # Wtf, Real Need This IF?
            continue

        Sharding.append((chunk_begin, chunk_end))
    return Sharding


# [OK]
def process_csv_file(input_path, output_path):
    """Use Muilty Threades Process CSV File"""
    # Read DataFrame
    df = pd.read_csv(input_path)
    file_name = os.path.basename(input_path)

    # Echo
    INFO_str = f"INFO: Begin Process {file_name}"
    print(INFO_str)
    if config.INFO_FILE != None:
        with config.INFO_FILE_f_lock:
            config.INFO_FILE_f.write(INFO_str + "\n")

    # Get DF basic info
    column_names = df.columns
    row_count = len(df.index)
    col_count = len(column_names)
    act_row_count = (
        row_count -
        config.BASIC_CONFIG["FRAME_EDGE"]["ROW_START"] -
        config.BASIC_CONFIG["FRAME_EDGE"]["ROW_END"]
    )
    act_col_count = (
        col_count -
        config.BASIC_CONFIG["FRAME_EDGE"]["COL_START"] -
        config.BASIC_CONFIG["FRAME_EDGE"]["COL_END"]
    )
    all_count = act_row_count * act_col_count

    # Init Processing tracker
    if config.BASIC_CONFIG["TRACK_SWITCH"]:
        with config.status_data_lock:
            config.status_data_dict[file_name] = {
                "start_time": time.time(),
                "this_start_time": time.time(),
                "finished_elapsed_time_str": None,
                "processed_count": 0,
                "all_count": all_count,
                "data": "\\",
                "status": 0
            }
        print_progress_table(True)

    # Pre Processing
    df = custom_func.pre_processing(
        df, file_name, column_names, all_count, False)

    # Shard DataFrame
    row_chunk_list = get_shard(
        config.BASIC_CONFIG["FRAME_EDGE"]["ROW_START"],
        row_count - config.BASIC_CONFIG["FRAME_EDGE"]["ROW_END"] - 1,
        config.BASIC_CONFIG["ROW_SHARD_COUNT"]
    )
    col_chunk_list = get_shard(
        config.BASIC_CONFIG["FRAME_EDGE"]["COL_START"],
        col_count - config.BASIC_CONFIG["FRAME_EDGE"]["COL_END"] - 1,
        config.BASIC_CONFIG["COL_SHARD_COUNT"]
    )

    # Begin Processing
    with ThreadPoolExecutor(max_workers=config.CSV_PROCESS_MAX_THREAD) as executor:
        try:
            # Init Thread Pool
            thread_pool = []

            # Init output dataframe
            processed_df = df.copy()

            # Update tracker info
            if config.BASIC_CONFIG["TRACK_SWITCH"]:
                config.update_progress_queue.put((
                    file_name,
                    {
                        "processed_count": 0,
                        "this_start_time": time.time(),
                        "status": 1
                    }
                ))
            # Add Thread to pool
            for row_begin, row_end in row_chunk_list:
                for col_begin, col_end in col_chunk_list:
                    df_shard = df.iloc[row_begin:row_end +
                                       1, col_begin:col_end+1]
                    future = executor.submit(
                        custom_func.processing,
                        df_shard,
                        file_name,
                        {
                            "row_begin": row_begin,
                            "row_end": row_end,
                            "col_begin": col_begin,
                            "col_end": col_end
                        },
                        column_names
                    )
                    thread_pool.append(future)

            # Finished
            for future in as_completed(thread_pool):
                processed_shard = future.result()
                row_idx = processed_shard.index.intersection(
                    processed_df.index)
                col_idx = processed_shard.columns.intersection(
                    processed_df.columns)
                if not row_idx.empty and not col_idx.empty:
                    processed_df.loc[row_idx,
                                     col_idx] = processed_shard.loc[row_idx, col_idx]

            # Update tracker info
            if config.BASIC_CONFIG["TRACK_SWITCH"]:
                config.update_progress_queue.put((
                    file_name,
                    {
                        "processed_count": 0,
                        "this_start_time": time.time(),
                        "status": 2
                    }
                ))
            # Post Process
            processed_df = custom_func.post_processing(
                processed_df, None, False)

            # Save DataFrame
            processed_df.to_csv(output_path, index=False)
            # Update tracker info
            if config.BASIC_CONFIG["TRACK_SWITCH"]:
                this_time = time.time()
                config.update_progress_queue.put((
                    file_name,
                    {
                        "this_start_time": this_time,
                        "finished_elapsed_time_str": format_time2str(
                            this_time -
                            config.status_data_dict[file_name]["start_time"]
                        ),
                        "processed_count": all_count,
                        "data": "\\",
                        "status": 3
                    },
                    True
                ))

        except Exception as e:
            ERROR_str = f"Error processing {file_name}: {e}"
            print(ERROR_str)
            if config.ERROR_FILE != None:
                with config.ERROR_FILE_f_lock:
                    config.ERROR_FILE_f.write(ERROR_str + "\n")
            return


# [OK]
def main():
    """Main Function"""
    # Print Runinfo
    print("INFO: Program Run Begin.")
    print("*** *** *** *** ***")

    # Set Stop Signal
    signal.signal(signal.SIGINT, signal_handler)

    # Init data progress thread
    processing_thread = threading.Thread(target=update_progress_queue)
    processing_thread.daemon = True
    processing_thread.start()

    # Ignore Unnecessary Warning
    warnings.simplefilter(action='ignore', category=FutureWarning)

    # Verify directory validity& Create output directory
    if not os.path.exists(config.BASIC_CONFIG["DATA_SOURCE_DIR"]):
        print(
            "Error: Directory "
            f"{config.BASIC_CONFIG["DATA_SOURCE_DIR"]}"
            " does not exist"
        )
        return 1
    os.makedirs(config.BASIC_CONFIG["DATA_OUTPUT_DIR"], exist_ok=True)

    # Process All CSV File
    csv_files = []
    for f in os.listdir(config.BASIC_CONFIG["DATA_SOURCE_DIR"]):
        if f.endswith('.csv'):
            csv_files.append(f)
            print(f"INFO: Found {f}")
    if not csv_files:
        print(
            "ERROR: No CSV files found in "
            f"{config.BASIC_CONFIG["DATA_SOURCE_DIR"]}"
        )
        return 0

    # Init log files
    if config.INFO_FILE != None:
        try:
            config.INFO_FILE_f = open(config.INFO_FILE, 'w+')
        except Exception as e:
            print(
                "Error: Can't open/create info log file "
                f"{config.INFO_FILE}"
                f" with {e}"
            )
            return 0
    if config.ERROR_FILE != None:
        try:
            config.ERROR_FILE_f = open(config.ERROR_FILE, 'w+')
        except Exception as e:
            print(
                "Error: Can't open/create error log file "
                f"{config.ERROR_FILE}"
                f" with {e}"
            )
            return 0

    # Init file rename files
    file_rename = None
    if config.BASIC_CONFIG["DATA_FILE_RENAME_FILE"] != None:
        try:
            config.DATA_FILE_RENAME_FILE_df = pd.read_csv(
                config.BASIC_CONFIG["DATA_FILE_RENAME_FILE"]
            )
            file_rename = \
                config.DATA_FILE_RENAME_FILE_df[["From", "To"]].to_dict(
                    orient='dict'
                )
        except Exception as e:
            ERROR_str = \
                "Error: Can't open file rename file " \
                f"{config.BASIC_CONFIG["DATA_FILE_RENAME_FILE"]}" \
                f" with {e}"
            print(ERROR_str)
            if config.ERROR_FILE != None:
                with config.ERROR_FILE_f_lock:
                    config.ERROR_FILE_f.write(ERROR_str + "\n")
            return 0

    # Print Found Files
    INFO_str = f"INFO: Found {len(csv_files)} CSV files to process"
    print(INFO_str)
    if config.INFO_FILE != None:
        with config.INFO_FILE_f_lock:
            config.INFO_FILE_f.write(INFO_str + "\n")
    print("*** *** *** *** ***")

    # Begin Processing
    with ThreadPoolExecutor(max_workers=config.FILE_MAX_THREAD) as executor:
        try:
            # Init Thread Pool
            thread_pool = []

            for file_name in csv_files:
                # Prepare parameters
                input_path = os.path.join(
                    config.BASIC_CONFIG["DATA_SOURCE_DIR"],
                    file_name
                )
                if file_rename == None:
                    output_path = os.path.join(
                        config.BASIC_CONFIG["DATA_OUTPUT_DIR"],
                        file_name
                    )
                else:
                    output_path = os.path.join(
                        config.BASIC_CONFIG["DATA_OUTPUT_DIR"],
                        file_rename[file_name]
                    )

                # Add Thread to pool
                thread_pool.append(executor.submit(
                    process_csv_file,
                    input_path,
                    output_path
                ))

            # Finished
            for future in as_completed(thread_pool):
                if config.force_exit:
                    break
                future.result()

            # Summary
            INFO_str = "INFO: All files processed successfully, Wating for summary."
            print(INFO_str)
            if config.BASIC_CONFIG["TRACK_SWITCH"]:
                while not config.update_progress_queue.empty:
                    continue
                with config.status_data_lock:
                    summary = {
                        "start_time": time.time(),
                        "this_start_time": 0,
                        "finished_elapsed_time_str": None,
                        "processed_count": 0,
                        "all_count": 0,
                        "data": "\\",
                        "status": -1
                    }
                    for file_name in config.status_data_dict.keys():
                        summary["start_time"] = min(
                            summary["start_time"],
                            config.status_data_dict[file_name]["start_time"]
                        )
                        summary["this_start_time"] = max(
                            summary["this_start_time"],
                            config.status_data_dict[file_name]["this_start_time"]
                        )
                        summary["all_count"] += config.status_data_dict[file_name]["all_count"]
                    summary["processed_count"] = summary["all_count"]
                    summary["finished_elapsed_time_str"] = format_time2str(
                        summary["this_start_time"] -
                        summary["start_time"]
                    )
                    config.status_data_dict["All"] = summary
                print_progress_table(True)

            INFO_str = "INFO: All files processed successfully."
            print(INFO_str)
            if config.INFO_FILE != None:
                with config.INFO_FILE_f_lock:
                    config.INFO_FILE_f.write(INFO_str + "\n")
            return 0

        except Exception as e:
            ERROR_str = f"ERROR: Error during processing with {e}"
            print(ERROR_str)
            if config.ERROR_FILE != None:
                with config.ERROR_FILE_f_lock:
                    config.ERROR_FILE_f.write(ERROR_str + "\n")
            return 1
        finally:
            executor.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    sys.exit(main())
