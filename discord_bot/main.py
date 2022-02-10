from queue import Queue
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
            print("Bot啟動完成")

        self.loop.create_task(self.send_message_bk())
        self.loop.create_task(self.response_bk())

    async def send_message_bk(self):
        while True:
            if not self.self_queue.empty():
                _content = ""
                data = out_queue.get()
                if " (" in raw_message and "): " in raw_message:
                    user = raw_message[raw_message.find(" (")+2:raw_message.find("): ")]
                    content = raw_message[raw_message.find(")")+3:]
                else:
                    user = "System"
                    content = raw_message
                await self.channel.send(_content[:-1])
                print(_content[:-1])
            await asyncio.sleep(0.1)

    async def response_bk(self):
        while True:
            if not response_queue.empty():
                try:
                    data = response_queue.get()
                    if data == "Shutdown_S":
                        await self.channel.send(f"<@&{SETTING['admin']}> 關閉成功。")
                    elif data == "Restart":
                        await self.channel.send(f"<@&{SETTING['admin']}> 開啟中。")
                    elif data[0] == "Shutdown_F":
                        await self.channel.send(f"<@&{SETTING['admin']}> 關閉失敗，錯誤訊息:`{data[1]}`")
                    elif len(data) == 2:
                        await data[1].send(f"[{SETTING['name']}]{data[0]}")
                except:
                    pass
            await asyncio.sleep(0.1)

    async def on_message(self, message: discord.Message):
        if message.author != self.user and message.channel.id == SETTING["channel"]:
            if message.content.startswith("$c") and SETTING['admin'] in [role.id for role in message.author.roles]:
                _command = message.content[3:]
                command_queue.put((_command, message.author))
                await message.delete()
                print(f"Send Command:{_command}")
            elif message.content == "$save" and SETTING['admin'] in [role.id for role in message.author.roles]:
                command_queue.put(("$save", message.author))
                await message.channel.send("存檔指令發送成功!")
                await message.delete()
                print("Send:Save")
            elif message.content == "$save_r" and SETTING['admin'] in [role.id for role in message.author.roles]:
                command_queue.put(("$save_r", message.author))
                await message.channel.send("存檔並重啟指令發送成功!")
                await message.delete()
                print("Send:Save_R")
            elif message.content == "$isa" and SETTING['admin'] in [role.id for role in message.author.roles]:
                command_queue.put(("$isa", message.author))
                await message.delete()
            elif message.content == "$start" and SETTING['admin'] in [role.id for role in message.author.roles]:
                os.system(f"start cmd /c \"C:\\asmdata\\Servers\\{SETTING['server']}\\ShooterGame\\Saved\\Config\\WindowsServer\\RunServer.cmd\"")
                await message.channel.send("啟動指令發送成功!")
                await message.delete()
                print("Send:Start")
            else:
                resp = f"[Discord][{message.author.display_name}]:{message.content}"
                print(resp)
                in_queue.put(resp)
    
    def run(self, *args, **kwargs):
        return super().run(self.config["token"], *args, **kwargs)