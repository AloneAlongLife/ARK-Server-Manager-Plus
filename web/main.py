from flask import Flask
from queue import Queue

class Dashboard():
    app = Flask(__name__)
    def __init__(self, global_setting, config) -> None:
        self.self_queue: Queue = global_setting["queues"]["Web"]
        self.discord_queue: Queue = global_setting["queues"]["Discord"]
        self.ark_queue: Queue = global_setting["queues"]["ARK"]
        self.log_queue: Queue = global_setting["queues"]["Log"]
        self.main: Queue = global_setting["queues"]["Main"]

    def run(
        self,
        host: str | None = None,
        port: int | None = None,
        debug: bool | None = None,
    ):
        self.app.run(host, port, debug, use_reloader=False)