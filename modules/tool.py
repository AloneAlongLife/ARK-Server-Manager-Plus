import msvcrt, time, sys
from threading import current_thread

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
