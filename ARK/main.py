from queue import Queue

class ARK_Server_Manager:
    def __init__(self, global_setting: dict, config: dict) -> None:
        self.self_queue: Queue = global_setting["queues"]["ARK"]
        self.discord_queue: Queue = global_setting["queues"]["Discord"]
        self.web_queue: Queue = global_setting["queues"]["Web"]
        self.log_queue: Queue = global_setting["queues"]["Log"]
        self.main: Queue = global_setting["queues"]["Main"]

    def run(self):
        pass