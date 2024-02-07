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

async def initiateDB():
     async with aiosqlite.connect('ChatsAndAccounts.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
                        CREATE TABLE IF NOT EXISTS ChatsAndAccounts (
                            message_id TEXT PRIMARY KEY,
                            account_id TEXT,
                            message TEXT,
                            date number,
                            type TEXT    
                        )
                    ''')
        await conn.commit()
        global messages
        messages = await getData()
        print(messages)



async def deleteData(message_id):
    while True:
        try:
            async with aiosqlite.connect('ChatsAndAccounts.db') as conn:
                cursor = await conn.cursor()
                await cursor.execute('''DELETE FROM ChatsAndAccounts
                                      WHERE message_id = ?''',
                                     (message_id,))
                await conn.commit()
                break
        except Exception as error:
            print(error)
            logging.error(error)
            await asyncio.sleep(0.5)

async def addData(message_id, id, message, date, type):
    while True:
        try:
            async with aiosqlite.connect('ChatsAndAccounts.db') as conn:
                cursor = await conn.cursor()
                await cursor.execute('''INSERT INTO ChatsAndAccounts (message_id, account_id, message, date, type)
                                      VALUES (?, ?, ?, ?, ?)''',
                                     (message_id, str(id), message, int(date), type))
                await conn.commit()
                break
        except Exception as error:
            print(error)
            logging.error(error)
            await asyncio.sleep(0.5)



async def getData():
    while True:
        try:
            async with aiosqlite.connect('ChatsAndAccounts.db') as conn:
                cursor = await conn.cursor()
                await cursor.execute("SELECT message_id, account_id, message, date, type FROM ChatsAndAccounts")
                rows = await cursor.fetchall()
                return rows
        except:
            await asyncio.sleep(0.5)

def check (e):
    return True



async def runClient(client, token):
    await client.start(bot_token = token)

    answer = "Hello, I am a bot, if you want to put new event type /add message YYYY-MM-DD HH:MM:SS"
    print("start")
    async def show_tasks(event):
        print("hey", messages)
        for message_id, usr_id, task, date, type in messages:
            if  str(event.peer_id.user_id) == str(usr_id):
                await event.reply("you have '" + task + "' task on " + str(datetime.datetime.fromtimestamp(date)))


    @client.on(events.NewMessage(incoming=True, func=check))
    async def handler(event):
        if (event.message.text[0:4] == "/add"):
            try:
                task = ' '.join(event.message.text.split(" ")[1:-2])
                date = event.message.text.split(" ")[-2:]

                datetime_object = datetime.datetime.strptime(' '.join(date), '%Y-%m-%d %H:%M:%S')
                sec_date = datetime_object.timestamp()
                hour_before = datetime.datetime.fromtimestamp(sec_date - 60 * 60)
                messages.append( (event.message.id, event.peer_id.user_id, task, sec_date, "event") ) 
                await event.reply(task)
                await event.reply(str(hour_before))  
                await addData(event.message.id, event.peer_id.user_id, task, sec_date, "event")

            except Exception as exc:
                print(exc)
                await event.reply("wrong format") 
        elif (event.message.text[0:5] == "/show"):
            print("start show")
            await show_tasks(event)
        else:
            print(event.message.text[0:4])
            await event.reply(answer)
        if enable:
            logging.info(f'Account answered to {event.chat_id}')

    while True:
        now = int(time.time())
        for message_id, usr_id, message, date, type in messages[:]:
            if now > date:
                await deleteData(message_id)
                messages.remove((message_id, usr_id, message, date, type))
                await client.send_message(usr_id, message)
                print(messages)
            
        await asyncio.sleep(60)


    await client.run_until_disconnected()

async def main():
    await initiateDB()
    async with aiofiles.open('config.json', 'r') as file_data:
        data = await file_data.read()
    data = json.loads(data)
    id = data['API_ID']
    hash = data['API_HASH']
    token = data['TOKEN']
    global enable
    enable = data['logging']['enable'] == "true"
    await asyncio.gather(runClient(TelegramClient('bot', id, hash), token))


if __name__ == "__main__":
    asyncio.run(main())