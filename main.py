from telethon.sync import TelegramClient, events
import time, json
import asyncio, aiofiles
import aiosqlite, random
import logging, datetime
import os

if not os.path.exists('logs'):
    os.makedirs('logs')

log_format = '%(asctime)s - %(levelname)s %(message)s'

today = datetime.date.today()
day = today.day
month = today.month
year = today.year
logging.basicConfig(filename=f'logs/{year}-{day}-{month}-main.log', level=logging.INFO, format=log_format)



def check (e):
    return True



async def runClient(client, token):
    await client.start(bot_token = token)

    answer = "Hello, I am a bot, if you want to put new event type /add message YYYY-MM-DD HH:MM:SS"
    print("start")
    async def show_tasks(event):
        for usr_id, task, date, type in messages:
            if  event.peer_id.user_id == usr_id:
                print("you have " + task + "has task on " + str(datetime.datetime.fromtimestamp(date)))
                await event.reply("you have '" + task + "' task on " + str(datetime.datetime.fromtimestamp(date)))


    @client.on(events.NewMessage(incoming=True, func=check))
    async def handler(event):
        if (event.message.text[0:4] == "/add"):
            try:
                task = ' '.join(event.message.text.split(" ")[1:-2])
                print(task)
                date = event.message.text.split(" ")[-2:]

                datetime_object = datetime.datetime.strptime(' '.join(date), '%Y-%m-%d %H:%M:%S')
                sec_date = datetime_object.timestamp()
                hour_before = datetime.datetime.fromtimestamp(sec_date - 60 * 60)
                messages.append( (event.peer_id.user_id, task, sec_date, "event") ) 
                await event.reply(task)
                await event.reply(str(hour_before))  
            except Exception as exc:
                print(exc)
                await event.reply("wrong format") 
        elif (event.message.text[0:5] == "/show"):
            print("start show")
            await show_tasks(event)
            print("start2")
        else:
            print(event.message.text[0:4])
            await event.reply(answer)
        if enable:
            logging.info(f'Account answered to {event.chat_id}')



    await client.run_until_disconnected()

async def main():
    async with aiofiles.open('config.json', 'r') as file_data:
        data = await file_data.read()
    data = json.loads(data)
    id = data['API_ID']
    hash = data['API_HASH']
    token = data['TOKEN']
    global enable
    enable = data['logging']['enable'] == "true"
    global messages
    messages = []
    await asyncio.gather(runClient(TelegramClient('bot', id, hash), token))


if __name__ == "__main__":
    asyncio.run(main())