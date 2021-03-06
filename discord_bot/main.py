from queue import Queue
from modules import thread_name
import discord
import asyncio

class Custom_Client(discord.client.Client):
    def __init__(self, global_setting, config, *args, **kargs) -> None:
        super().__init__(*args, **kargs)
        self.self_queue: Queue = global_setting["queues"]["Discord"]
        self.ark_queue: Queue = global_setting["queues"]["ARK"]
        self.web_queue: Queue = global_setting["queues"]["Web"]
        self.log_queue: Queue = global_setting["queues"]["Log"]
        self.main: Queue = global_setting["queues"]["Main"]
        self.config = config

    async def on_ready(self):
        for channel_id in self.config["chat_channel"].values():
            self.channel = self.get_channel(channel_id)
            await self.channel.send("Bot啟動完成")
            self.log_queue.put(f"{thread_name()}Bot啟動完成")

        self.loop.create_task(self.request_bk())

    async def request_bk(self):
        while True:
            if not self.self_queue.empty():
                queue_data = self.self_queue.get()
                if queue_data["content"].get("key") in self.config["chat_channel"].keys():
                    channel = self.get_channel(self.config["chat_channel"][queue_data["content"]["key"]])
                    display_name = queue_data["content"]["display_name"]
                    raw_message = queue_data["content"]["message"]
                    self.log_queue.put(f"{thread_name()}Receive Message:{raw_message}")
                    if queue_data["type"] == "message":
                        if " (" in raw_message and "): " in raw_message:
                            user = raw_message[raw_message.find(" (")+2:raw_message.find("): ")]
                            message = raw_message[raw_message.find(")")+3:]
                        else:
                            user = "System"
                            message = raw_message
                        if message.startswith(f"[{display_name}]"):
                            message = message[len(f"[{display_name}]"):]
                        await channel.send(f"[{display_name}][{user}]:{message}")
                    if queue_data["type"] == "admin-message":
                        await channel.send(f"<@&{self.config['admin_role']}>{raw_message}")
                    elif queue_data["type"] == "command-reply":
                        message = raw_message
                        if message.startswith(f"[{display_name}]"):
                            message = message[len(f"[{display_name}]"):]
                        await queue_data["user"].send(f"[{display_name}]{raw_message}")
            await asyncio.sleep(0.05)

    async def on_message(self, message: discord.Message):
        if message.author != self.user and message.channel.id in [id for id in self.config["chat_channel"].values()]:
            self.log_queue.put(f"{thread_name()}Receive Message: {message.content}")
            if message.content.startswith(f"{self.config['prefix']}c") and self.config["admin_role"] in [role.id for role in message.author.roles]:
                command = message.content[3:]
                if command.startswith("del "):
                    command = command[4:]
                    await message.delete()
                key = list(self.config["chat_channel"].keys())[list(self.config["chat_channel"].values()).index(message.channel.id)]
                self.ark_queue.put(
                    {
                        "type": "command",
                        "content": f"{key} {command}",
                        "thread": "discord",
                        "user": message.author
                    }
                )
            elif message.content.startswith(f"{self.config['prefix']}m") and self.config["admin_role"] in [role.id for role in message.author.roles]:
                command = message.content[3:]
                if command.startswith("del "):
                    command = command[4:]
                    await message.delete()
                self.main.put(
                    {
                        "type": "command",
                        "content": command,
                        "thread": "discord",
                        "user": message.author
                    }
                )
            elif self.config["admin_role"] in [role.id for role in message.author.roles]:
                if command.startswith(f"{self.config['prefix']}del "):
                    command = command[5:]
                    await message.delete()
                key = list(self.config["chat_channel"].keys())[list(self.config["chat_channel"].values()).index(message.channel.id)]
                self.ark_queue.put(
                    {
                        "type": "command",
                        "content": f"{key} Broadcast {command}",
                        "thread": "discord",
                        "user": message.author
                    }
                )
    
    def run(self, *args, **kwargs):
        return super().run(self.config["token"], *args, **kwargs)