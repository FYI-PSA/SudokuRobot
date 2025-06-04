#  the more higher level stuff starts at line 70 ish
import sys

from log_man import give_me_loggers

print, print_error, shutdown_logging = give_me_loggers()

import gc
import os

import psutil

print("NUCLEAR MODE. WILL KILL ANY OTHER RUNNING PYTHON INSTANCE.")
me = os.getpid()
if os.name == 'nt':
    PYTHON_NAME = 'python.exe'
else:
    PYTHON_NAME = 'python'
pythons = [p for p in psutil.process_iter() if p.name() == PYTHON_NAME]
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
if os.name == 'nt':
    LOCK = '\\'.join(LOCK.split('/'))
    KEY = '\\'.join(KEY.split('/'))
else:
    LOCK = '/'.join(LOCK.split('\\'))
    KEY = '/'.join(KEY.split('\\'))

if FILE in os.listdir(LOCK):
    print("Turns out an instance *was* indeed already running...")
    os.remove(KEY)
    sys.exit(55)  # Based on Microsoft Documentation, I don't know what else to make this based off.
else:
    key_file = open(KEY, 'wb')  # pylint: disable=R1732
    key_file.write(b'\x00')
    key_file.close()

gc.collect()

import atexit


def exit_handler() -> None:
    if FILE in os.listdir(LOCK):
        os.remove(KEY)
        print("Removed file lock")
    else:
        print("No lock while quitting.")
    shutdown_logging()


atexit.register(exit_handler)

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

print('importing the important stuff')

import asyncio
import socket
import threading
import time
from http import HTTPStatus

from telegram import InputMediaPhoto
from telegram.error import Conflict
from telegram.ext import (Application, ApplicationBuilder, CommandHandler,
                          Defaults, MessageHandler, filters)


def bind_port():
    host = '0.0.0.0'
    port_ = os.getenv('PORT')
    if port_ is None:
        port = "8080"
    else:
        port = port_
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f'Binding the socket to port {port} and to {host}.')
    sock.bind((host, int(port)))
    return sock


global stop_listening  # pylint: disable=W0604
stop_listening = False  # pylint: disable=C0103


def sock_listener(sock):
    global stop_listening
    print('Listener on the socket is starting now.')
    # while (not sock._closed) and (not stop_listening):
    # apparently ._closed is private so it most likely won't work how I expect it to.
    while not stop_listening:
        sock.listen(10)
        connection, _address = sock.accept()  # pylint: disable=W0612
        with connection:
            # print(f'Received connection by {address}')
            # data = connection.recv(1024).decode('utf-8')
            http_ver = 'HTTP/1.1'
            status = 'OK'  # https://docs.python.org/3/library/http.html#http-status-codes
            status_http = getattr(HTTPStatus, status, 'OK')  # third one is the default if the 'status' is wrong.
            status_value = f'{status_http.value} {status_http.phrase}'  # type: ignore
            content_type = 'text/html'
            data = 'If you can read this, the bot is online! You can close this.'
            body = f'<HTML><body> <h1>{data}</h1> </body></HTML>'
            response = (f"{http_ver} {status_value}\r\nContent-Type: {content_type}\r\n\r\n{body}").encode('utf-8')
            connection.sendall(response)
    print('Socket was closed.')


async def start(update, context):
    text_block: str = (
        "Send me a screenshot or any other image of a Sudoku puzzle and I will solve it for you.\n"
        "You can use /generate_easy to create an easy difficulty Sudoku puzzle\n"
        "You can use /generate_hard to create a hard difficulty Sudoku puzzle\n"
        "You can use /generate to create a medium difficulty Sudoku puzzle\n"
        )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_block)
    print("Someone started the bot!")
    user = update.message.from_user
    user_profile = f'Name: {user.first_name} - {user.last_name}   |   Username: {user.username}   |   Id: {user.id}'
    print(f"User info:\n{user_profile}")


async def help(update, context):
    help_text_block: str = (
        "If the bot stops working, you should visit\n"
        "https://sudokurobot.onrender.com/\n"
        "Then wait for around 1 or 2 minutes and the bot will start working.\n"
        "(The page will change when the bot starts, and it will inform you of that, no worries!)"
        )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text_block)
    use_start_text_block: str = (
        "If you want to know how to use the bot, use /start"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=use_start_text_block)
    user = update.message.from_user
    user_profile = f'Name: {user.first_name} - {user.last_name}   |   Username: {user.username}   |   Id: {user.id}'
    print(f"User info:\n{user_profile}")


print('importing the heart of the project including Keras, which will take a while...')
import servermain
from tilereader import \
    grayscale_numpy_tiles_list_to_predicted_integer_list as \
    predict_grayscale_func
from tilereader import load_model

AImodel = load_model()
print('AI model loaded.')


def get_bot_token() -> str:
    try:
        token = os.getenv('BOT_TOKEN')
        if token is None:
            with open('/etc/secrets/BOT_TOKEN.txt', 'rb') as file:
                token = file.read().decode('utf-8').strip()
    except (PermissionError, UnicodeDecodeError) as err:
        raise Exception("Token not found. Either set BOT_TOKEN in environment, or have the BOT_TOKEN.txt file in /etc/secrets/") from err
    token = str(token).strip()
    return token


def get_admin_id() -> int:
    try:
        admin_id = os.getenv('ADMIN_ID')
        if admin_id is None:
            with open('/etc/secrets/ADMIN_ID.txt', 'rb') as file:
                admin_id = file.read().decode('utf-8').strip()
    except (PermissionError, UnicodeDecodeError) as err:
        raise Exception("Admin's ID not found. Either set ADMIN_ID in environment, or have the ADMIN_ID.txt file in /etc/secrets/") from err
    try:
        admin_id = int(str(admin_id).strip())
    except ValueError as err:
        raise Exception("Admin's ID is supposed to be the integer user ID") from err
    return admin_id


async def respond_messages(update, context):
    message = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Use /help to learn about what to do if facing an issue.\nUse /start to learn how to use the bot.")
    # response = requests.get('https://sudokucodehost-tgbot.onrender.com/')
    # print(f"Site response: {response}")
    print(f"User: {update.message.from_user.username} | Message: {message}")


async def process_image(update, context):
    first_reply = await context.bot.send_message(chat_id=update.effective_chat.id, text="Solving...\nPlease wait, this may take up to a minute depending on the load on the server...", reply_to_message_id=update.message.message_id)

    print("Brb...")

    img_file_name = await save_attachment_to_file(update, context)
    await asyncio.sleep(1)
    img_file_name = str(img_file_name)
    print(f"Saved the file as {img_file_name}")
    asyncio_response_tuple_future = await servermain.async_servermain(
        ai_model=AImodel,
        filename=img_file_name,
        predict_grayscale_func=predict_grayscale_func
    )
    print(asyncio_response_tuple_future)
    (
        success,
        solved_grid_file_name,
        solved_image_file_name,
        solved_grid,
        possible_err_details,
        possible_err_name,
        possible_err_line
        ) = await asyncio_response_tuple_future

    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=first_reply.message_id)

    print("Yay! The heart beat and did its thing!")
    too_many_solutions_flag = False
    no_unique_solutions_flag = False
    ai_issue_flag = False
    if success and (possible_err_name is None):
        # await context.bot.send_message(chat_id=update.effective_chat.id, text="Excellent", reply_to_message_id=update.message.message_id)
        pass
    elif success and (possible_err_name == 'Too many solutions'):
        response: str = (
            'Your puzzle had more than 100 possible solutions!\n'
            'If your grid was not empty or you think the number of solutions is less than a hundred,\n'
            'please message the admin @FYI_PSA about this.'
            )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_to_message_id=update.message.message_id)
        # no return, do the rest of the code too.
        too_many_solutions_flag = True
        no_unique_solutions_flag = True
    elif success and (possible_err_name == 'Solutions not unique'):
        response: str = (
            "Your didn't have a unique solution.\n"
            "If you think the puzzle only has one unique solution,\n"
            "please message the admin @FYI_PSA about this."
            )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_to_message_id=update.message.message_id)
        # no return, do the rest of the code too.
        no_unique_solutions_flag = True
    elif success and not (possible_err_name is None):  # pylint: disable=C0325
        response: str = (
            "Solving the grid was done successfully, but there was an error while attempting to make it into an image.\n"
            "Please report the admin @FYI_PSA\n"
            "Sending your solved puzzle as a message instead."
            )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_to_message_id=update.message.message_id)
        gridstr = servermain.gridstring(solved_grid)
        print(gridstr)
        print(f"User: {update.message.from_user.username}   |   Failed: {possible_err_name}: {possible_err_line} : {possible_err_details}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=gridstr, reply_to_message_id=update.message.message_id)
        return
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"<b>I can't solve this.</b>\n\n{possible_err_details}", reply_to_message_id=update.message.message_id, parse_mode='HTML')
        ai_issue_flag = True
        print(f"User: {update.message.from_user.username}   |   Failed: {possible_err_name}: {possible_err_line} : {possible_err_details}")
        # don't raise, still go through with giving it an image.
        # raise Exception(f"{possible_err_name} : {possible_err_line} : {possible_err_details}")

    with open(solved_image_file_name, 'rb') as img_file:
        solved_image = img_file.read()
    with open(solved_grid_file_name, 'rb') as grd_file:
        solved_grid_image = grd_file.read()
    mediagroup = [InputMediaPhoto(media=solved_image), InputMediaPhoto(media=solved_grid_image)]

    if too_many_solutions_flag:
        captiontext: str = "Here's one of the possible solutions for your puzzle. It had more than 100 solutions!\nThe other image shows you the full grid without the rest of the image."
    elif no_unique_solutions_flag:
        captiontext: str = "Your puzzle had multiple unique solutions.\nHere's one of them, alongside an image of only the solved puzzle."
    elif ai_issue_flag:
        captiontext: str = "The image recognition failed, but the program attempted to solve it regardless.\nIf you see a mismatch between a number you provided and one in this grid, you will know that the AI digit recognition failed!"
    else:
        captiontext: str = "Solved!\nHere's the solved puzzle placed inside the original image, alongside a high quality image of only the solved grid."
    await context.bot.send_media_group(chat_id=update.effective_chat.id, media=mediagroup, caption=captiontext, reply_to_message_id=update.message.message_id)

    print(f"User: {update.message.from_user.username}   |   File name: {img_file_name}   |   Grid: {solved_grid}")
    gc.collect()
    os.remove(solved_grid_file_name)
    os.remove(solved_image_file_name)
    os.remove(img_file_name)


async def send_generated_modular(update, context, difficulty: str, first_response: str, caption: str):
    first_reply = await context.bot.send_message(chat_id=update.effective_chat.id, text=first_response, reply_to_message_id=update.message.message_id)
    print('Sent message.')
    files = os.listdir()
    file_counter = 0
    file_name = f"puzzle_{difficulty.lower()}_{file_counter}.png"
    while file_name in files:
        file_counter += 1
        file_name = f"puzzle_{difficulty.lower()}_{file_counter}.png"
    with open(file_name, 'wb') as temp_write_file:
        temp_write_file.write(b'\x00')
    gc.collect()
    print('Entering make_puzzle')
    asyncio_response_tuple_future = await servermain.make_puzzle_async(file_name, difficulty=difficulty)
    (
        puzzle_grid,
        puzzle_file_name,
        possible_error_message,
        possible_error_name,
        possible_error_line
    ) = await asyncio_response_tuple_future

    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=first_reply.message_id)

    if possible_error_message is not None:
        response: str = (
            "The puzzle was generated successfully, but there was an error while attempting to make it into an image.\n"
            "Please report the admin @FYI_PSA\n"
            "Sending your solved puzzle as a message instead."
            )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_to_message_id=update.message.message_id)
        gridstr: str = servermain.gridstring(puzzle_grid)
        gridstr = ''.join(['_' if item == '0' else item for item in gridstr])
        print(gridstr)
        print(f"User: {update.message.from_user.username}   |   Failed: {possible_error_name}: {possible_error_line} : {possible_error_message}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=gridstr, reply_to_message_id=update.message.message_id)
        return

    with open(puzzle_file_name, 'rb') as puzzle_file:
        puzzle_image = puzzle_file.read()

    mediagroup = [InputMediaPhoto(media=puzzle_image)]

    has_more_than_one_solution_flag = False
    # later make it one of the responses of make_puzzle
    # right now it won't happen ever because I'm not using diff < 0

    if has_more_than_one_solution_flag:
        captiontext: str = "!"
    else:
        captiontext: str = caption

    await context.bot.send_media_group(chat_id=update.effective_chat.id, media=mediagroup, caption=captiontext, parse_mode='HTML', reply_to_message_id=update.message.message_id)

    print(f"User: {update.message.from_user.username}   |   File name: {file_name}")

    gc.collect()

    os.remove(puzzle_file_name)


async def send_hard_generated(update, context):
    print('Entering send hard')
    first_response: str = "Generating and sending a difficult puzzle.\nThis process may take up to 3 minutes..."
    caption: str = "Difficulty: <b>HARD</b>"
    difficulty: str = "HARD"
    await send_generated_modular(update=update, context=context, difficulty=difficulty, first_response=first_response, caption=caption)


async def send_easy_generated(update, context):
    print('Entering send easy')
    first_response: str = "Generating and sending an easy puzzle.\nThis process may take up to 3 minutes..."
    caption: str = "Difficulty: <b>EASY</b>"
    difficulty: str = "EASY"
    await send_generated_modular(update=update, context=context, difficulty=difficulty, first_response=first_response, caption=caption)


async def send_medium_generated(update, context):
    print('Entering send medium')
    first_response: str = "Generating and sending a medium difficulty puzzle.\nThis process may take up to 3 minutes..."
    caption: str = "Difficulty: <b>MEDIUM</b>"
    difficulty: str = "MEDIUM"
    await send_generated_modular(update=update, context=context, difficulty=difficulty, first_response=first_response, caption=caption)


async def save_attachment_to_file(update, context) -> str:  # pylint: disable=W0613
    new_file = await update.message.effective_attachment[-1].get_file()
    new_file_name = await new_file.download_to_drive()
    return new_file_name


async def error_handler(update, context):  # pylint: disable=W0613
    err = context.error
    # print(f"You sneaky moron! Stop trying to error!")
    if isinstance(err, Conflict):
        print("Conflict happening. Peace time!\n")
        await asyncio.sleep(7.5)
        print("Is the conflict persisting after this?\n")
    else:
        print('\n\n')
        print_error(f"An unexpected exception, you should investigate: {err}")
        error = sys.exc_info()[-1]
        if error is None:
            print("Was not a exception from the code apparently.")
        else:
            print(f"Was indeed a valid exception, line {error.tb_lineno}")
        print('\n\n')


def get_or_create_eventloop() -> asyncio.AbstractEventLoop:
    try:
        print("Creating new event loop...")
        current_loop = asyncio.get_event_loop()
        return current_loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print("Set existing event loop")
        current_loop = asyncio.get_event_loop()
        return current_loop


async def notify_start(app: Application) -> None:
    await app.bot.send_message(get_admin_id(), text="The bot has started!")


async def notify_end(app: Application) -> None:
    await app.bot.send_message(get_admin_id(), text="The bot is shutting down.")


async def init_handler(app: Application) -> None:
    await notify_start(app)
    print("Informed admin of start.")


async def stop_handler(app: Application):
    await notify_end(app)
    print("Informed admin of shutdown")


def main():
    global stop_listening
    time.sleep(0.5)
    print("Main is now working!")

    sock = bind_port()
    sock_listener_thread = threading.Thread(target=sock_listener, args=(sock, ))
    sock_listener_thread.start()

    event_loop = get_or_create_eventloop()

    new_defaults = Defaults(block=False)

    application: Application = (
        ApplicationBuilder()
        .token(get_bot_token())
        .read_timeout(10)
        .write_timeout(10)
        .connect_timeout(10)
        .connection_pool_size(10)  # Handle 10 connections at once
        .concurrent_updates(True)
        .defaults(new_defaults)
        .post_init(init_handler)
        .post_stop(stop_handler)
        ).build()

    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)

    generate_hard_handler = CommandHandler('generate_hard', send_hard_generated)
    generate_easy_handler = CommandHandler('generate_easy', send_easy_generated)
    generate_medium_handler = CommandHandler('generate', send_medium_generated)

    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), respond_messages)
    image_handler = MessageHandler(filters.PHOTO & (filters.FORWARDED | ~filters.FORWARDED), process_image)

    # the order of these is important, otherwise if you put a general rule after a specific rule, the specific will be overridden
    application.add_handler(start_handler)
    application.add_handler(help_handler)

    application.add_handler(generate_hard_handler)
    application.add_handler(generate_easy_handler)
    application.add_handler(generate_medium_handler)

    application.add_handler(message_handler)
    application.add_handler(image_handler)

    application.add_error_handler(error_handler)

    event_loop = get_or_create_eventloop()

    application.run_polling()

    print("Mainloooop... dying... terminated...")
    try:
        event_loop.stop()
    except RuntimeError:
        # Means it's already dead.
        pass
    stop_listening = True
    sock_listener_thread.join()


if __name__ == '__main__':
    try:
        main()
        print("Mainloop looped.")
        sys.exit(0)
    except Exception as e:
        print("Generic exception? I don't know how to handle that.")
        print(f"Error type name: {type(e).__name__}")
        print(f"Error message  : {str(e)}")
        sys.exit(1)
