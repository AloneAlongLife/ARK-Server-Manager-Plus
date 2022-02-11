from queue import Queue
from modules import Thread, get_ip, thread_name, process_info
from opencc import OpenCC
from rcon import Client
from time import sleep
from os.path import join, abspath, isdir
from os import system, makedirs
from shutil import copyfile
from datetime import datetime

BACKSLASH = "\\"
CC = OpenCC("s2tw")

def is_alive(path: str) -> bool:
    alive_list = process_info("ShooterGameServer.exe")
    if alive_list != None:
        return join(abspath(path), "ShooterGame\\Binaries\\Win64\\ShooterGameServer.exe") in [data.get("Path") for data in alive_list]
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
                                resp = client.run(command)
                                self.log_queue.put(f"{thread_name()}[RCON]Receive Command: {command}")
                                self.log_queue.put(f"{thread_name()}[RCON]Command Reply: {resp}")
                            data["type"] = "command-reply"
                            data["content"] = resp
                            response.put(data)
                        raw_chat = client.run("GetChat")[:-3]
                        if "Server received, But no response!" not in raw_chat:
                            content_list = raw_chat.split("\n")
                            for string in [content for content in content_list if content != ""]:
                                self.log_queue.put(f"{thread_name()}[RCON]{string}")
                                if (not string.startswith(("SERVER:", "管理員指令"))) and ("has entered your zone." not in string): 
                                    if string.startswith("部落"):
                                        tribe = string[2:string.find(", ID ")]
                                        if string.find("\">") != -1: string = string[string.find("\">") + 2:-4]
                                        else: string = string.split(": ")[2][:-1]
                                        if string[:6] == "部落成員 ": string = string[6:]
                                        elif string[:5] == "你的部落":
                                            string = string[5:]
                                        string = f"<{tribe}>{string}"
                                    response.put(
                                        {
                                            "type": "chat",
                                            "content": string
                                        }
                                    )
                        sleep(0.05)
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
                        Client(config["ip"], config["port"], timeout=5).connect()
                        break
                    except:
                        sleep(0.05)

    def timestamp(self):
        return (datetime.utcnow() + self.time_dalta).strftime('%Y_%m_%d %H-%M-%S')

    def stop(self, config, server, times=5, restart=False):
        for i in range(times):
            message = f"""[{config['name']}]伺服器將於{times-i}分鐘後{['關閉', '重啟'][restart]}。
            [{config['name']}]Server will {['shutdown', 'restart'][restart]} in {times-i} min."""
            self.discord_queue.put({"type": "message", "content": {"message": message, "key": server, "display_name": config["name"]}, "thread": "ark"})
            config["queues"]["request"].put({"type": "command", "content": f"Broadcast {message}"})
            sleep(60)
        message = f"[{config['name']}]儲存中...\n[{config['name']}]Saving..."
        self.discord_queue.put({"type": "message", "content": {"message": message, "key": server, "display_name": config["name"]}, "thread": "ark"})
        config["queues"]["request"].put({"type": "command", "content": f"Broadcast {message}"})
        config["queues"]["request"].put({"type": "command", "content": "DestroyWildDinos"})
        config["queues"]["request"].put({"type": "command", "content": f"DoExit"})
        while is_alive(config["path"]):
            sleep(10)
        if not isdir(join(config['path'], 'ShooterGame\\Backup\\SavedArks')):
            makedirs(join(config['path'], 'ShooterGame\\Backup\\SavedArks'))
        save_path = join(config["path"], f"ShooterGame{BACKSLASH}Saved{BACKSLASH}SavedArks{BACKSLASH}{config['map_name']}.ark")
        backup_path = join(config["path"], f"ShooterGame{BACKSLASH}Backup{BACKSLASH}SavedArks{BACKSLASH}{config['map_name']}_{self.timestamp()}.ark")
        copyfile(save_path, backup_path)
        if restart:
            system("start cmd /c \"" + join(config['path'], 'ShooterGame\\Saved\\Config\\WindowsServer\\RunServer.cmd') + "\"")

    def run(self):
        ip = get_ip()
        data = {}
        for key in self.config.keys():
            data[key] = {
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
                "temp_thread": Thread()
            }
            data[key]["thread"] = Thread(target=self.rcon_session, name=data[key]["name"], args=(data[key]["config"], data[key]["queues"]["request"], data[key]["queues"]["response"]))
            data[key]["thread"].start()
        while True:
            if not self.self_queue.empty():
                queue_data: dict = self.self_queue.get()
                if queue_data["type"] == "command":
                    target = queue_data["content"].split(" ")[0]
                    if target not in data.keys():
                        for key in data.keys():
                            value = data[key]
                            if target.lower() == value["name"].lower():
                                target = key
                                break
                    if target in data.keys():
                        command = queue_data["content"].replace(f"{target} ", "")
                        self.log_queue.put(f"{thread_name()}Receive Command: {command}")
                        value = data[target]
                        if command == "start":
                            if not is_alive(value["path"]) and not value["temp_thread"].is_alive():
                                system("start cmd /c \"" + join(value['path'], 'ShooterGame\\Saved\\Config\\WindowsServer\\RunServer.cmd') + "\"")
                        elif command == "restart":
                            if is_alive(value["path"]) and not value["temp_thread"].is_alive():
                                value["temp_thread"] = Thread(target=self.stop, name=f"ARK-temp-thread-{target}", args=(value, target, 5, True))
                                value["temp_thread"].start()
                        elif command == "stop":
                            if is_alive(value["path"]) and not value["temp_thread"].is_alive():
                                value["temp_thread"] = Thread(target=self.stop, name=f"ARK-temp-thread-{target}", args=(value, target, 5, False))
                                value["temp_thread"].start()
                        else:
                            queue_data["content"] = command
                            value["queues"]["request"].put(queue_data)
            for key in data.keys():
                value = data[key]
                status = server_status(value["status"], value["rcon"])
                if is_alive(value["path"]) != value["status"]:
                    value["status"] = is_alive(value["path"])
                if not value["queues"]["response"].empty():
                    queue_data = value["queues"]["response"].get()
                    print(queue_data)
                    print(status)
                    if queue_data["type"] == "command-reply":
                        if queue_data["thread"] == "main":
                            pass
                        elif queue_data["thread"] == "discord":
                            queue_data["content"] = {
                                "message": queue_data["content"],
                                "key": key,
                                "display_name": value["name"]
                            }
                            self.discord_queue.put(queue_data)
                        elif queue_data["thread"] == "web":
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
                    status = server_status(value["status"], value["rcon"])
                    status_message = ""
                    if status == True:
                        status_message = f"[{value['name']}]伺服器已啟動。"
                    elif status == None:
                        status_message = f"[{value['name']}]伺服器無回應。"
                    elif status == False:
                        status_message = f"[{value['name']}]伺服器已關閉。"
                        while not value["queues"]["request"].empty():
                            value["queues"]["request"].get()
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