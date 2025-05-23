#  the more higher level stuff starts at line 70 ish
import logging


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
print = logging.info


import os, sys, subprocess
import psutil


print("NUCLEAR MODE. WILL KILL ANY OTHER RUNNING PYTHON INSTANCE.")
me = os.getpid()
if os.name == 'nt':
    procname = 'python.exe'
else:
    procname = 'python'
pythons = [p for p in psutil.process_iter() if p.name() == procname]
# print(pythons)
# print(me)
# print("^ yup")
if len(pythons) > 1:
    for proc in pythons:
        if proc.pid == me:
            continue
        print(f"An instance with {proc.pid} went down!")
        proc.kill()


FILE = 'ONLY_ONE_PYTHON_LOCK'
DIR = '~/'
LOCK = os.path.expanduser(DIR)
KEY = os.path.expanduser(DIR+FILE)


if FILE in os.listdir(LOCK):  # this is now just left purely cosmetic
    print("Turns out an instance *was* indeed already running...")
    os.remove(KEY)
    exit(55)  # Based on Microsoft Documentation, I don't know what else to make this based off.
else:
    subprocess.call(['touch', KEY])


import atexit


def exit_handler():
    if FILE in os.listdir(LOCK):
        os.remove(KEY)
    else:
        print(f"no lock while quitting.")


atexit.register(exit_handler)


os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


import socket
import threading
# import requests
import time
import asyncio
from http import HTTPStatus
from telegram import Update, InputFile, InputMediaPhoto
from telegram.error import Conflict
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import gc


def bind_port():
    HOST = '0.0.0.0'
    port_ = os.getenv('PORT')
    if port_ is None:
        PORT = "8080"
    else:
        PORT = port_
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f'Binding the socket to port {PORT} and to {HOST}.')
    sock.bind((HOST, int(PORT)))
    return sock


def sock_listener(sock):
    print('Listener on the socket is starting now.')
    while not sock._closed:
        sock.listen(10)
        connection, address = sock.accept()
        with connection:
            # print(f'Recieved connection by {address}')
            # data = connection.recv(1024).decode('utf-8')
            http_ver = 'HTTP/1.1'
            status = 'OK'  # https://docs.python.org/3/library/http.html#http-status-codes
            status_http = getattr(HTTPStatus, status, 'OK')  # third one is the default if the 'status' is wrong.
            status_value = f'{status_http.value} {status_http.phrase}'
            content_type = 'text/html'
            data = 'If you can read this, the bot is online! You can close this.'
            body = f'<HTML><body> <h1>{data}</h1> </body></HTML>'
            response = (f"{http_ver} {status_value}\r\nContent-Type: {content_type}\r\n\r\n{body}").encode('utf-8')
            connection.sendall(response)
    print('Socket was closed.')


async def start(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Send me a screenshot or any other image of a Sudoku puzzle!")
    print("Someone started the bot!")
    user = update.message.from_user
    user_profile = f'Name: {user.first_name} - {user.last_name}   |   Username: {user.username}   |   Id: {user.id}'
    print(f"User info:\n{user_profile}")


async def notifystart(app, adminid):
    await app.bot.send_message(chat_id=adminid, text="The bot has started!")


async def help(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"If the bot stops working, you should quickly visit\nhttps://sudokurobot.onrender.com/\nJust load the site, you don't need to stay on that page\nThen wait for around 1 minute and the bot will be working.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Send me a screenshot or any other image of a Sudoku puzzle!")
    user = update.message.from_user
    user_profile = f'Name: {user.first_name} - {user.last_name}   |   Username: {user.username}   |   Id: {user.id}'
    print(f"User info:\n{user_profile}")


import servermain
from tilereader import grayscale_numpy_tiles_list_to_predicted_integer_list as predict_grayscale_func, load_model as load_model
AImodel = load_model()
print('ai model loaded.')


def get_or_create_eventloop():
    try:
        print("Creating new loop...")
        return asyncio.get_event_loop()
    except Exception as e:
        print("Caught one: {e}")
        if "no current event loop" in str(e):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()
        else:
            print("failure...")
            raise ex


async def echo(update, context):
    message = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Use /help to learn about what to do if facing an issue.\nUse /start to learn how to use the bot.")
    # response = requests.get('https://sudokucodehost-tgbot.onrender.com/')
    # print(f"Site response: {response}")
    print(f"User: {update.message.from_user.username} | Message: {message}")


async def process_image(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Solving...\nPlease wait, this may take up to a minute depending on the load on the server...", reply_to_message_id=update.message.message_id)
    print("Brb...")
    
    img_file_name = await save_attachment_to_file(update, context)
    time.sleep(1)
    img_file_name = str(img_file_name)
    print(f"Saved the file as {img_file_name}")
    (success,
     solvedgridfilename,
     solvedimagefilename,
     solved_grid,
     possible_err_details,
     possible_err_name,
     possible_err_line ) = servermain.servermain(
         AImodel=AImodel,
         filename=img_file_name,
         predict_grayscale_func=predict_grayscale_func
     )

    print("yay i passed the server thing!")
    
    if success and (possible_err_name is None):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Excellent", reply_to_message_id=update.message.message_id)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"<b>I can't solve this.</b>\n\n{possible_err_details}", reply_to_message_id=update.message.message_id, parse_mode='HTML')
        
        print(f"User: {update.message.from_user.username}   |   Failed: {possible_err_name}: {possible_err_line} : {possible_err_details}")
        
        raise Exception(f"{possible_err_name} : {possible_err_line} : {possible_err_details}")
        return
        
    with open(solvedimagefilename, 'rb') as img_file:
        solvedimg = img_file.read()
    with open(solvedgridfilename, 'rb') as grd_file:
        solvedgrd = grd_file.read()
    mediagroup = [InputMediaPhoto(media=solvedimg), InputMediaPhoto(media=solvedgrd)]
    await context.bot.send_media_group(chat_id=update.effective_chat.id, media=mediagroup, caption="Solved!\nHere's the solved puzzle placed inside the original image, alongside a high quality image of only the solved grid.")
    
    print(f"User: {update.message.from_user.username}   |   File name: {img_file_name}   |   Grid: {solved_grid}")
    gc.collect()
    os.remove(solvedgridfilename)
    os.remove(solvedimagefilename)
    os.remove(img_file_name)


async def save_attachment_to_file(update, context):
    new_file = await update.message.effective_attachment[-1].get_file()
    file = await new_file.download_to_drive()    
    return file


async def error_handler(update, context):
    err = context.error
    # print(f"You sneaky moron! Stop trying to error!")
    if isinstance(err, Conflict):
        print("Conflict happening. Peace time!\n")
        time.sleep(10)
        print("Is the conflict persisting after this?\n")
    else:
        logging.info('\n\n')
        logging.error(f"An unexpected exception, you should investigate: {err}") 
        errline = sys.exc_info()[-1].tb_lineno
        print(f"Error line: {errline}")
        print('\n\n')


def main(token, adminid):
    time.sleep(0.1)
    
    sock = bind_port()
    sock_listener_thread = threading.Thread(target=sock_listener, args=(sock, ))
    sock_listener_thread.start()
    
    event_loop = get_or_create_eventloop()

    application = ApplicationBuilder().token(f"{token}").build()
    
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    image_handler = MessageHandler(filters.PHOTO & (filters.FORWARDED | ~filters.FORWARDED), process_image)

    # the order of these is important, otherwise if you put a general rule after a specific rule, the specific will be overridden 
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(echo_handler)
    application.add_handler(image_handler)

    application.add_error_handler(error_handler)

    event_loop.run_until_complete(notifystart(application, adminid))
    application.run_polling()
    
    print("Mainloooop... died??? HOW!?")
    sock_listener_thread.join()


if __name__ == '__main__':
    try:
        token = os.getenv('BOT_TOKEN') # github secrets
        adminid = os.getenv('ADMIN_ID')
        if token is None:
            with open('/etc/secrets/BOT_TOKEN.txt', 'r') as file:
                token = file.read().strip()
        if adminid is None:
            with open('/etc/secrets/ADMIN_ID.txt', 'r') as file:
                adminid = file.read().strip()
    except:
        raise Exception("Token or Admin's ID not found. Either set BOT_TOKEN / ADMIN_ID in environment, or have the BOT_TOKEN.txt or ADMIN_ID.txt file in /etc/secrets/")
    try:
        adminid = int(str(adminid).strip())
        token = str(token).strip()
    except:
        raise Exception("Wrong type!! Admin's ID is supposed to be the integer user ID")
    try:
        main(token, adminid)
        print("Mainloop looped.")
        exit(0)
    except Exception as e:
        print("Generic exception? I don't know how to handle that.")
        print(e)
        exit(1)
