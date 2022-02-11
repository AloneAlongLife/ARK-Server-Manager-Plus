import msvcrt, time, sys
from threading import current_thread
from subprocess import Popen, PIPE
import requests
from datetime import datetime, timedelta

def get_ip():
    ip = requests.get('https://api.ipify.org').text
    return ip

def input_t(prompt: str="", timeout: float=10.0, timer=time.monotonic) -> tuple:
    sys.stdout.write(prompt)
    sys.stdout.flush()
    endtime = timer() + timeout
    result = []
    while timer() < endtime:
        if msvcrt.kbhit():
            input_char = msvcrt.getwche()
            if input_char == '\r':
                return ''.join(result), True
            elif input_char == '\b' and result:
                if result[-1] != '\b':
                    result.pop()
                else:
                    result.append(input_char)
            else:
                result.append(input_char)
        time.sleep(0.04)
    return ''.join(result), False

def backspace(s: str) -> str:
    chars = []
    for c in s:
        if c == '\b' and chars:
            chars.pop()
        else:
            chars.append(c)
    return ''.join(chars)

def thread_name() -> str:
    return f"[{current_thread().name.replace('Thread', '').capitalize()} Thread]"

def process_info(name: str="") -> list | None:
    raw_info = Popen(f"wmic process where name=\"{name}\" get name, executablepath, processid", shell=True, stdout=PIPE).stdout.read().decode("utf-8").split("\r\r\n")[:-2]
    if "ExecutablePath" in raw_info[0] and "Name" in raw_info[0] and "ProcessId" in raw_info[0]:
        s_path = raw_info[0].find("ExecutablePath")
        s_name = raw_info[0].find("Name")
        s_pid = raw_info[0].find("ProcessId")
        result = []
        for i in range(1, len(raw_info)):
            if raw_info[i][s_pid:].replace(" ", "") != "":
                result.append(
                    {
                        "Path": raw_info[i][s_path:s_name - 2],
                        "Name": raw_info[i][s_name:s_pid - 2],
                        "PID": int(raw_info[i][s_pid:].replace(" ", "")),
                    }
                )
        return result
    else:
        return None

def now_time(delta: timedelta | float) -> datetime:
    if type(delta) == timedelta:
        return datetime.utcnow() + delta
    else:
        return datetime.utcnow() + timedelta(hours=delta)
