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
     """
     function creates DB for scheduled messages if it isn't created
       and takes data from this DB
     """
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
    """
     Deletes event from DB
     """
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
    """
     Adds event to DB
     """
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
    """
     returns data saved in DB
     """
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



async def runClient(client, token, answer):
    """
     Main function that runs bot and has handlers for some events
     """
    await client.start(bot_token = token)
    
    print("start")
    async def show_tasks(event):
        for message_id, usr_id, task, date, type in messages:
            if  str(event.peer_id.user_id) == str(usr_id) and type == "event":
                await event.reply("you have '" + task + "' on " + str(datetime.datetime.fromtimestamp(date)))

 
    @client.on(events.NewMessage(incoming=True, func=check))
    async def handler(event):
        
        if (event.message.text[0:4] == "/add"):
            try:
                task = ' '.join(event.message.text.split(" ")[1:-2])
                date = event.message.text.split(" ")[-2:]

                datetime_object = datetime.datetime.strptime(' '.join(date), '%Y-%m-%d %H:%M:%S')
                sec_date = datetime_object.timestamp()
                if sec_date < int(time.time()):
                    await client.send_message(int(event.peer_id.user_id), "can't schedule in past")
                    raise ValueError("can't schedule in past")
                
                messages.append( (event.message.id, event.peer_id.user_id, task, sec_date, "event") ) 
                await addData(event.message.id, event.peer_id.user_id, task, sec_date, "event")
                
                if sec_date - 60 * 60 > int(time.time()):
                    messages.append( (event.message.id + sec_date - 60 * 60, event.peer_id.user_id, task + " in an hour", sec_date - 60 * 60, "notification") )
                    await addData (event.message.id + sec_date - 60 * 60, event.peer_id.user_id, task + " in an hour", sec_date - 60 * 60, "notification")
                    
                if sec_date - 2 * 60 * 60 > int(time.time()):
                    messages.append( (event.message.id + sec_date - 2 * 60 * 60, event.peer_id.user_id, task + " in 2 hours", sec_date - 2* 60 * 60, "notification") )  
                    await addData (event.message.id + sec_date - 2 * 60 * 60, event.peer_id.user_id, task + " in 2 hours", sec_date - 2 * 60 * 60, "notification")
            
                await event.reply("your event " + task + " is scheduled on " + str(' '.join(date)))  
            except Exception as exc:
                print(exc)
                await event.reply("wrong format") 
                logging.info(f'{event.chat_id} tried to add task with wrong format')
        elif (event.message.text[0:5] == "/show"):
            await show_tasks(event)
            logging.info(f'Showed tasks to {event.chat_id}')

        elif (event.message.text[0:7] == "/delete"):
            try:
                task = ' '.join(event.message.text.split(" ")[1:-2])
                date = event.message.text.split(" ")[-2:]

                datetime_object = datetime.datetime.strptime(' '.join(date), '%Y-%m-%d %H:%M:%S')
                sec_date = datetime_object.timestamp()

                for message_id, usr_id, message, date, type in messages[:]:
                    if task == message and date == sec_date:
                        await deleteData(message_id)
                        messages.remove((message_id, usr_id, message, date, type))
                        await client.send_message(int(usr_id), message + " deleted")
            except Exception as exc:
                print(exc)
                await event.reply("wrong format") 
                logging.info(f'{event.chat_id} tried to delete task with wrong format')
            
        else:
            await event.reply(answer)
        if enable:
            logging.info(f'Account answered to {event.chat_id}')

    while True:
        now = int(time.time())
        for message_id, usr_id, message, date, type in messages[:]:
            if now > date:
                await deleteData(message_id)
                messages.remove((message_id, usr_id, message, date, type))
                await client.send_message(int(usr_id), message)
            
        await asyncio.sleep(10)


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
    answer = data['answer']
    await asyncio.gather(runClient(TelegramClient('bot', id, hash), token, answer))


if __name__ == "__main__":
    asyncio.run(main())