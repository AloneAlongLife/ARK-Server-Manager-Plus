from glob import glob
from queue import Queue
from modules import Thread, get_ip, thread_name, process_info
from opencc import OpenCC
from rcon import Client
from time import sleep
from os.path import join, abspath, isdir
from os import system, makedirs
from shutil import copyfile
from datetime import datetime
from psutil import Process, NoSuchProcess

BACKSLASH = "\\"
CC = OpenCC("s2tw")

START_WITH = (
    "SERVER:",
    "管理員指令"
)
IN_STR = (
    "被自動摧毀了！",
    "has entered your zone.",
    "馴養了 一隻",
    " Souls were destroyed by ",
    " Soul was destroyed by ",
    " 擊殺!",
    " 已死亡!",
    " killed!",
    "你的部落 killed ",
    " killed ，擊殺者：",
    " 認養了 ",
    " 摧毀了你的 ",
    " 拆除了",
    " 放生了 '",
    "你的部落馴養了一隻"
)

savedict = {}

def is_alive(path: str) -> bool:
    alive_list = process_info("ShooterGameServer.exe")
    if alive_list != None:
        try:
            return join(abspath(path), "ShooterGame\\Binaries\\Win64\\ShooterGameServer.exe") in [Process(data.get("PID")).exe() for data in alive_list]
        except NoSuchProcess:
            return False
    else:
        return False

def server_status(cmd: bool, rcon: bool) -> bool | None:
    if cmd:
        if rcon:
            return True
        else:
            return None
    else:
        return False

def remove_message(message: str) -> bool:
    if message.startswith(START_WITH):
        return False
    for test_str in IN_STR:
        if test_str in message:
            return False
    return True

class ARK_Server_Manager:
    def __init__(self, global_setting: dict, config: dict) -> None:
        self.self_queue: Queue = global_setting["queues"]["ARK"]
        self.discord_queue: Queue = global_setting["queues"]["Discord"]
        self.web_queue: Queue = global_setting["queues"]["Web"]
        self.log_queue: Queue = global_setting["queues"]["Log"]
        self.main: Queue = global_setting["queues"]["Main"]
        self.time_dalta = global_setting["time_delta"]
        self.config = config

    def rcon_session(self, config: dict, request: Queue, response: Queue):
        global savedict
        while True:
            try:
                with Client(config["ip"], config["port"], timeout=60, passwd=config["password"]) as client:
                    response.put(
                        {
                            "type": "status",
                            "content": "connect"
                        }
                    )
                    self.log_queue.put(f"{thread_name()}[RCON]RCON Connected.")
                    while True:
                        if not request.empty():
                            data = request.get()
                            if data["type"] == "command":
                                command = data["content"]
                                self.log_queue.put(f"{thread_name()}[RCON]Receive Command: {command}")
                                resp = client.run(command)
                                self.log_queue.put(f"{thread_name()}[RCON]Command Reply To \"{command}\": {resp}")
                                data["type"] = "command-reply"
                                data["content"] = resp
                                response.put(data)
                                # if data.get("thread") == "save":
                                #     savedict[config["key"]] = True
                                #     self.log_queue.put(f"RCON: {savedict}")
                        raw_chat = client.run("GetChat")[:-3]
                        if "Server received, But no response!" not in raw_chat:
                            content_list = raw_chat.split("\n")
                            for string in [content for content in content_list if content != ""]:
                                self.log_queue.put(f"{thread_name()}[RCON]{string}")
                                conv_string = CC.convert(string)
                                if (remove_message(conv_string)): 
                                    if conv_string.startswith("部落"):
                                        tribe = string[2:string.find(", ID ")]
                                        if string.find("\">") != -1: string = string[string.find("\">") + 2:-4]
                                        else: string = string.split(": ")[2][:-1]
                                        if conv_string.startswith("部落成員 "): string = string[5:]
                                        if conv_string.startswith("你的部落"): string = string[4:]
                                        string = f"<{tribe}>{string}"
                                    response.put(
                                        {
                                            "type": "chat",
                                            "content": string
                                        }
                                    )
                        sleep(0.05)
            except SystemExit:
                break
            except:
                sleep(5)
                try:
                    with Client(config["ip"], config["port"], timeout=10, passwd=config["password"]) as client:
                        pass
                except:
                    response.put(
                        {
                            "type": "status",
                            "content": "disconnect"
                        }
                    )
                    self.log_queue.put(f"{thread_name()}[RCON]RCON Disconnected.")
                    while True:
                        try:
                            with Client(config["ip"], config["port"], timeout=5, passwd=config["password"]) as client:
                                break
                        except:
                            sleep(0.05)

    def timestamp(self):
        return (datetime.utcnow() + self.time_dalta).strftime('%Y_%m_%d %H-%M-%S')

    def stop(self, config, server, times=5, restart=False):
        global savedict
        if restart == False:
            restart = 0
        elif restart == True:
            restart = 1
        else:
            restart = 2
        for i in range(times):
            if (times-i <= 5) or (times-i <= 30 and times-i % 5 == 0):
                message = f"""[{config['name']}]伺服器將於{times-i}分鐘後{['關閉', '重啟', '存檔'][restart]}。\n[{config['name']}]Server will {['shutdown', 'restart', 'save'][restart]} in {times-i} min."""
                self.discord_queue.put({"type": "message", "content": {"message": message, "key": server, "display_name": config["name"]}, "thread": "ark"})
                config["queues"]["request"].put({"type": "command", "content": f"Broadcast {message}"})
            sleep(60)
        message = f"[{config['name']}]儲存中...\n[{config['name']}]Saving..."
        self.discord_queue.put({"type": "message", "content": {"message": message, "key": server, "display_name": config["name"]}, "thread": "ark"})
        config["queues"]["request"].put({"type": "command", "content": f"Broadcast {message}"})
        with open("classlist") as class_file:
            class_list = class_file.read().split("\n")
        # config["queues"]["request"].put({"type": "command", "content": "Slomo 0.1"})
        class_list_2 = []
        for classname in class_list:
            if classname not in class_list_2:
                class_list_2.append(classname)
                config["queues"]["request"].put({"type": "command", "content": f"DestroyWildDinoClasses \"{classname}\" 1"})
        class_list_2.sort()
        with open("classlist", mode="w", encoding="utf-8") as class_file:
            class_file.write("\n".join(class_list_2))
            class_file.close()
        if restart != 2:
            config["queues"]["request"].put({"type": "command", "content": "DestroyWildDinos"})
        # config["queues"]["request"].put({"type": "command", "content": "Slomo 1"})
        config["queues"]["request"].put({"type": "command", "content": "SaveWorld", "thread": "save"})
        saved_count = 0
        # while not savedict[server]:
        #     print(f"Save: {savedict}")
        #     sleep(1)
        #     saved_count += 1
        #     if saved_count > 3600:
        #         self.discord_queue.put({"type": "admin-message", "content": {"message": "儲存失敗。", "key": server, "display_name": config["name"]}, "thread": "ark"})
        #         return
        if restart == 2:
            sleep(360)
        else:
            config["queues"]["request"].put({"type": "command", "content": "DoExit"})
            while is_alive(config["path"]):
                sleep(1)
        if not isdir(join(config['path'], 'ShooterGame\\Backup\\SavedArks')):
            makedirs(join(config['path'], 'ShooterGame\\Backup\\SavedArks'))
        save_path = join(config["path"], f"ShooterGame{BACKSLASH}Saved{BACKSLASH}SavedArks{BACKSLASH}{config['map_name']}.ark")
        backup_path = join(config["path"], f"ShooterGame{BACKSLASH}Backup{BACKSLASH}SavedArks{BACKSLASH}{config['map_name']}_{self.timestamp()}.ark")
        copyfile(save_path, backup_path)
        if restart == 1:
            sleep(5)
            self.self_queue.put(
                {
                    "type": "command",
                    "content": f"{config['key']} start",
                    "thread": "ark"
                }
            )
        elif restart == 2:
            self.discord_queue.put({"type": "message", "content": {"message": "儲存完成。", "key": server, "display_name": config["name"]}, "thread": "ark"})

    def run(self):
        global savedict
        ip = get_ip()
        data = {}
        for key in self.config.keys():
            data[key] = {
                "key": key,
                "name": self.config[key]["name"],
                "map_name": self.config[key]["map_name"],
                "path": abspath(self.config[key]["path"]),
                "queues": {
                    "request": Queue(),
                    "response": Queue()
                },
                "config": {
                    "ip": ip,
                    "port": self.config[key]["port"],
                    "password": self.config[key].get("password"),
                },
                "status": False,
                "rcon": False,
                "last_status": False,
                "temp_thread": Thread(),
            }
            data[key]["thread"] = Thread(target=self.rcon_session, name=data[key]["name"], args=(data[key]["config"], data[key]["queues"]["request"], data[key]["queues"]["response"]))
            data[key]["thread"].start()
        while True:
            if not self.self_queue.empty():
                queue_data: dict = self.self_queue.get()
                if queue_data["type"] == "command":
                    self.log_queue.put(f"{thread_name()}Receive Command: {queue_data['content']}")
                    target = queue_data["content"].split(" ")[0]
                    if target not in data.keys():
                        for key in data.keys():
                            value = data[key]
                            if target.lower() == value["name"].lower():
                                target = key
                                break
                    if target in data.keys():
                        command = queue_data["content"].replace(f"{target} ", "")
                        value = data[target]
                        if value["temp_thread"].is_alive():
                            value["temp_thread"].join(5)
                        if command == "start":
                            if not is_alive(value["path"]) and not value["temp_thread"].is_alive():
                                system("start cmd /c \"" + join(value['path'], 'ShooterGame\\Saved\\Config\\WindowsServer\\RunServer.cmd') + "\"")
                                status_message = f"[{value['name']}]伺服器已啟動。"
                                self.log_queue.put(f"{thread_name()}{status_message}")
                                self.discord_queue.put(
                                    {
                                        "type": "admin-message",
                                        "content": {
                                            "message": status_message,
                                            "key": target,
                                            "display_name": value["name"]
                                        },
                                        "thread": "ark"
                                    }
                                )
                        elif command.startswith("restart"):
                            try:
                                r_time = abs(int(command.split(" ")[1]))
                            except:
                                r_time = 5
                            if is_alive(value["path"]) and not value["temp_thread"].is_alive():
                                savedict[target] = False
                                value["temp_thread"] = Thread(target=self.stop, name=f"ARK-temp-thread-{target}", args=(value, target, r_time, True))
                                value["temp_thread"].start()
                        elif command.startswith("stop"):
                            try:
                                r_time = abs(int(command.split(" ")[1]))
                            except:
                                r_time = 5
                            if is_alive(value["path"]) and not value["temp_thread"].is_alive():
                                savedict[target] = False
                                value["temp_thread"] = Thread(target=self.stop, name=f"ARK-temp-thread-{target}", args=(value, target, r_time, False))
                                value["temp_thread"].start()
                        elif command.startswith("save") and not command.startswith("saveworld"):
                            try:
                                r_time = abs(int(command.split(" ")[1]))
                            except:
                                r_time = 5
                            if is_alive(value["path"]) and not value["temp_thread"].is_alive():
                                savedict[target] = False
                                value["temp_thread"] = Thread(target=self.stop, name=f"ARK-temp-thread-{target}", args=(value, target, r_time, None))
                                value["temp_thread"].start()
                        else:
                            queue_data["content"] = command
                            value["queues"]["request"].put(queue_data)
                elif queue_data["type"] == "system":
                    if queue_data["content"] == "stop":
                        while True:
                            for thread in [value["thread"] for value in data.values()] + [value["temp_thread"] for value in data.values()]:
                                if thread.is_alive():
                                    thread.stop()
                            for thread in [value["thread"] for value in data.values()] + [value["temp_thread"] for value in data.values()]:
                                try:
                                    thread.join(timeout=1)
                                except RuntimeError:
                                    pass
                            if True not in [thread.is_alive() for thread in [value["thread"] for value in data.values()] + [value["temp_thread"] for value in data.values()]]:
                                break
                            sleep(0.05)
                        self.main.put(
                            {
                                "type": "system",
                                "content": "thread stopped",
                                "thread": "ark"
                            }
                        )
            for key in data.keys():
                value = data[key]
                status = server_status(value["status"], value["rcon"])
                if status == None and value["last_status"] == False:
                    status = False
                if is_alive(value["path"]) != value["status"]:
                    value["status"] = is_alive(value["path"])
                if not value["queues"]["response"].empty():
                    queue_data = value["queues"]["response"].get()
                    if queue_data["type"] == "command-reply":
                        if queue_data.get("thread") == "main":
                            pass
                        elif queue_data.get("thread") == "discord":
                            queue_data["content"] = {
                                "message": queue_data["content"],
                                "key": key,
                                "display_name": value["name"]
                            }
                            self.discord_queue.put(queue_data)
                        elif queue_data.get("thread") == "web":
                            self.web_queue.put(queue_data)
                    elif queue_data["type"] == "chat":
                        message = f"[{value['name']}]{queue_data['content']}"
                        self.log_queue.put(message)
                        self.discord_queue.put(
                            {
                                "type": "message",
                                "content": {
                                    "message": message,
                                    "key": key,
                                    "display_name": value["name"]
                                },
                                "thread": "ark"
                            }
                        )
                    elif queue_data["type"] == "status":
                        if queue_data["content"] == "connect":
                            value["rcon"] = True
                        elif queue_data["content"] == "disconnect":
                            value["rcon"] = False
                if server_status(value["status"], value["rcon"]) != status:
                    sleep(10)
                    if server_status(value["status"], value["rcon"]) != status:
                        value["last_status"] = status
                        last_status = value["last_status"]
                        status = server_status(value["status"], value["rcon"])
                        status_message = ""
                        if status == True:
                            if last_status == False:
                                status_message = f"[{value['name']}]伺服器已啟動完成。"
                            else:
                                status_message = f"[{value['name']}]伺服器已重新連線。"
                        elif status == None:
                            if last_status == False:
                                status_message = ""
                            else:
                                status_message = f"[{value['name']}]伺服器無回應。"
                        elif status == False:
                            status_message = f"[{value['name']}]伺服器已關閉。"
                            while not value["queues"]["request"].empty():
                                value["queues"]["request"].get()
                        if status_message != "":
                            self.log_queue.put(f"{thread_name()}{status_message}")
                            self.discord_queue.put(
                                {
                                    "type": "admin-message",
                                    "content": {
                                        "message": status_message,
                                        "key": key,
                                        "display_name": value["name"]
                                    },
                                    "thread": "ark"
                                }
                            )
            sleep(0.05)
    # "C:\asmdata\Servers\Server3\ShooterGame\Binaries\Win64\ShooterGameServer.exe"