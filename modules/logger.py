from datetime import datetime
from queue import Queue
from os.path import join, isdir
from os import mkdir
from time import sleep

def logger(
    setting: dict
) -> None:
    LOG_DIR = join(setting["data_path"], "log")
    if not isdir(LOG_DIR):
        mkdir(LOG_DIR)

    while True:
        log_queue: Queue = setting["queues"]["Log"]
        if not log_queue.empty():
            now_time: datetime = datetime.utcnow() + setting["time_delta"]
            file_name = now_time.strftime('%Y-%m-%d.txt')
            time_stamp = now_time.strftime('[%H:%M:%S]')
            content = f"{time_stamp}{log_queue.get()}"
            print(content)
            with open(join(LOG_DIR, file_name), mode="a", encoding="utf-8") as log_file:
                log_file.write(f"{content}\n")
                log_file.close()
        sleep(0.05)