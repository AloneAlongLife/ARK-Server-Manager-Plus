from queue import Queue

class Custom_Client:
    def __init__(self, global_setting, config) -> None:
        self.self_queue: Queue = global_setting["queues"]["Discord"]
        self.ark_queue: Queue = global_setting["queues"]["ARK"]
        self.web_queue: Queue = global_setting["queues"]["Web"]
        self.log_queue: Queue = global_setting["queues"]["Log"]
        self.main: Queue = global_setting["queues"]["Main"]