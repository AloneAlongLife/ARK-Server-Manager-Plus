from queue import Queue
import discord
import asyncio

class Custom_Client(discord.client.Client):
    def __init__(self, global_setting, config, *args, **kargs) -> None:
        self.self_queue: Queue = global_setting["queues"]["Discord"]
        self.ark_queue: Queue = global_setting["queues"]["ARK"]
        self.web_queue: Queue = global_setting["queues"]["Web"]
        self.log_queue: Queue = global_setting["queues"]["Log"]
        self.main: Queue = global_setting["queues"]["Main"]
        self.config = config
        print(args)
        print(kargs)
        super().__init__(*args, **kargs)

    async def on_ready(self):
        for channel_id in self.config["chat_channel"].values():
            self.channel = self.get_channel(channel_id)
            await self.channel.send("Bot啟動完成")
            print("Bot啟動完成")

        self.loop.create_task(self.request_bk())

    async def request_bk(self):
        while True:
            if not self.self_queue.empty():
                queue_data = self.self_queue.get()
                if queue_data.get("key") in self.config["chat_channel"].keys():
                    channel = self.get_channel(self.config["chat_channel"][queue_data["content"]["key"]])
                    display_name = queue_data["content"]["display_name"]
                    raw_message = queue_data["content"]["message"]
                    if queue_data["type"] == "message":
                        if " (" in raw_message and "): " in raw_message:
                            user = raw_message[raw_message.find(" (")+2:raw_message.find("): ")]
                            message = raw_message[raw_message.find(")")+3:]
                        else:
                            user = "System"
                            message = raw_message
                        await channel.send(f"[{display_name}][{user}]:{message}")
                    if queue_data["type"] == "admin-message":
                        await channel.send(f"<@&{self.config['admin_role']}>{raw_message}")
                    elif queue_data["type"] == "command-reply":
                        await queue_data["user"].send(f"[{display_name}]{raw_message}")
            await asyncio.sleep(0.05)

    async def on_message(self, message: discord.Message):
        if message.author != self.user and message.channel.id in [id for id in self.config["chat_channel"].values()]:
            if message.content.startswith(f"{self.config['prefix']}c") and self.config["admin_role"] in [role.id for role in message.author.roles]:
                command = message.content[3:]
                key = self.config["chat_channel"].keys()[list(self.config["chat_channel"].values()).index(message.channel.id)]
                self.ark_queue.put(
                    {
                        "type": "command",
                        "content": f"{key} {command}",
                        "thread": "discord",
                        "user": message.author
                    }
                )
            # else:
            #     resp = f"[Discord][{message.author.display_name}]:{message.content}"
            #     print(resp)
            #     in_queue.put(resp)
    
    def run(self, *args, **kwargs):
        return super().run(self.config["token"], *args, **kwargs)