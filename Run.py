from os import makedirs, system
import asyncio
from os.path import isdir, isfile, join
from queue import Queue
from time import sleep
from datetime import timedelta
from subprocess import Popen, PIPE

from modules import Thread, json, logger, input_t, backspace, thread_name
from ARK import ARK_Server_Manager
from discord_bot import Custom_Client
from web import Dashboard

EXAMPLE_CONFIG = {
    "global_config": {
        "data_dir": "data",
        "time_delta": 8
    },
    "ark_servers": {
        "Server1": {
            "path": "C:\\asmdata\\Servers\\Server1",
            "port": 0,
            "password": "",
            "name": "",
            "map_name": ""
        }
    },
    "discord_bot": {
        "token": "",
        "prefix": "$",
        "admin_role": 0,
        "chat_channel": {
            "Server1": 0
        }
    },
    "web_dashboard": {
        "host": "0.0.0.0",
        "port": 5001,
        "debug": True
    }
}

def config_reader() -> tuple:
    """
    讀取設置
    回傳 (`file_exist`, `config`)
    `file_exist`: 設置檔是否存在
    `config`: 設置
    """
    if isfile("config.json"):
        file_exist = True
        config = json.load("config.json")
    else:
        file_exist = False
        json.dump("config.json", EXAMPLE_CONFIG)
        config = None
    return file_exist, config

def flask_job(*args, **kargs):
    web_ui = Dashboard(*args, **kargs)
    web_ui.run(host="0.0.0.0", port=5001, debug=True)

def ark_job(*args, **kargs):
    asm = ARK_Server_Manager(*args, **kargs)
    asm.run()    

def discord_job(bot):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(bot.run())
    loop.run_forever()


def command_job(setting: dict):
    main_queue: Queue = setting["queues"]["Main"]
    command = ""
    while True:
        raw_command = input_t(timeout=1)
        command = backspace(command + raw_command[0])
        if raw_command[1]:
            main_queue.put(
                {
                    "type": "command",
                    "content": command,
                    "thread": "command"
                }
            )
            command = ""

if __name__ == "__main__":
    # 檢查是否有Git
    git_version = str(Popen("git --version", shell=True, stdout=PIPE).stdout.read())
    if "version" not in git_version.lower():
        print("Git不存在")
        print("請前往進行安裝")
        print("按下Enter結束...")
        input()
        exit()

    # 讀取設置
    raw_config = config_reader()
    file_exist = raw_config[0]
    config = raw_config[1]

    # 如果設置不存在，則提醒並終止程式
    if not file_exist:
        print("設置檔不存在 已自動產生")
        print("請前往更新設置檔: config.json")
        print("按下Enter結束...")
        input()
        exit()

    # 如果設置檔內容有誤，則提醒並終止程式
    try:
        GLOBAL_CONFIG = config["global_config"]
        ARK_SERVER = config["ark_servers"]
        DISCORD_BOT = config["discord_bot"]
        WEB_DASHBOARD = config["web_dashboard"]
    except KeyError:
        print("設置檔內容有誤")
        print("請前往更新設置檔: config.json")
        print("按下Enter結束...")
        input()
        exit()

    # 設置時區偏差
    TIME_DELTA = timedelta(hours=GLOBAL_CONFIG["time_delta"])

    # 產生儲存資料的資料夾
    DATA_PATH = GLOBAL_CONFIG["data_dir"].replace("\\", "/")
    if not isdir(DATA_PATH):
        makedirs(DATA_PATH)

    # 產生設定
    setting = {
        "data_path": DATA_PATH,
        "time_delta": TIME_DELTA,
        "queues": {
            "ARK": Queue(),
            "Discord": Queue(),
            "Web": Queue(),
            "Log": Queue(),
            "Main": Queue()
        }
    }

    # 產生各分支線程
    bot = Custom_Client(setting, DISCORD_BOT)
    threads = {
        "log_thread": Thread(target=logger, name="Logger", args=(setting,)),
        "command_thread": Thread(target=command_job, name="Command", args=(setting,)),
        "ARK_thread": Thread(target=ark_job, name="ARK", args=(setting, ARK_SERVER)),
        "discord_thread": Thread(target=discord_job, name="discord", args=(bot,)),
        "web_thread": Thread(target=flask_job, name="web", args=(setting, WEB_DASHBOARD))
    }
    for thread in threads.values():
        thread.start()

    main_queue: Queue = setting["queues"]["Main"]
    log_queue: Queue = setting["queues"]["Log"]
    ark_queue: Queue = setting["queues"]["ARK"]
    log_queue.put(f"{thread_name()}----------Start Up----------")
    log_queue.put(f"{thread_name()}Update...")
    git_pull = str(Popen("git pull", shell=True, stdout=PIPE).stdout.read())
    if "Already up to date" not in git_pull:
        main_queue.put(
            {
                "type": "command",
                "content": "restart",
                "thread": "main"
            }
        )
        log_queue.put(f"{thread_name()}Need to Restart.")
    log_queue.put(f"{thread_name()}Update Finish.")
    while True:
        if not main_queue.empty():
            queue_data: dict = main_queue.get()
            if queue_data.get("type") == "command":
                command = queue_data.get("content").lower()
                log_queue.put(f"{thread_name()}Receive Command: {command}")
        else:
            command = ""
        
        if command.startswith("$ark"):
            ark_queue.put(
                {
                    "type": "command",
                    "content": command.split(" ", 1),
                    "thread": "main"
                }
            )
        elif command == "restart":
            while True:
                for thread in threads.values():
                    if thread.is_alive() and thread.name != "Logger":
                        thread.stop()
                for thread in threads.values():
                    if thread.name != "Logger":
                        thread.join(timeout=1)
                while not log_queue.empty():
                    sleep(0.1)
                threads["log_thread"].stop()
                threads["log_thread"].join(timeout=1)
                if True not in [thread.is_alive() for thread in threads.values()]:
                    break
            system("start cmd /c Start.cmd")
            break
        elif command == "stop":
            while True:
                for thread in threads.values():
                    if thread.is_alive() and thread.name != "Logger":
                        thread.stop()
                for thread in threads.values():
                    if thread.name != "Logger":
                        thread.join(timeout=1)
                while not log_queue.empty():
                    sleep(0.1)
                threads["log_thread"].stop()
                threads["log_thread"].join(timeout=1)
                if True not in [thread.is_alive() for thread in threads.values()]:
                    break
            break
