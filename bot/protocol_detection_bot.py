import os
import telebot
import requests
import cv2
from pdf2image import convert_from_path

import keys  # файл с ключами
from page_recognition.page_rec import page_recognition as page_rec
from page_recognition.page_rec import get_path_to_output as set_path_to_output

URL = 'https://api.telegram.org/bot'
PATH_TO_TMP = '../tmp'
PATH_TO_IMG = PATH_TO_TMP + '/images/'
PATH_TO_PDF = PATH_TO_TMP + '/pdf/'
PATH_TO_CSV = PATH_TO_TMP + '/csv/'
PATH_TO_OUTPUT = ''

num_of_sheet = 0


def create_dir(path: str):
    if os.path.exists(path):
        pass
    else:
        os.mkdir(path)


def create_infrastructure():
    create_dir(PATH_TO_TMP)
    create_dir(PATH_TO_CSV)
    create_dir(PATH_TO_IMG)
    create_dir(PATH_TO_PDF)


def send_file(file: str, type: str, chat_id: str):
    files = {type: open(file, 'rb')}
    requests.post(f'{URL}{keys.BOT_TOKEN}/sendDocument?chat_id={chat_id}', files=files)
    # заполнить гугл док и выплинуть ссылку


bot = telebot.TeleBot(keys.BOT_TOKEN)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        create_infrastructure()
        src = PATH_TO_PDF + message.document.file_name

        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)

        images = convert_from_path(src)

        global PATH_TO_IMG
        for i in range(len(images)):
            # Save pages as images in the pdf
            images[i].save(PATH_TO_IMG + 'img' + str(i) + '.jpg', 'JPEG')

        os.remove(src)

        images = os.listdir(PATH_TO_IMG)
        global num_of_sheet
        global PATH_TO_CSV
        global PATH_TO_OUTPUT
        for img in images:
            num_of_sheet += 1
            PATH_TO_OUTPUT = PATH_TO_CSV + str(num_of_sheet) + '.csv'
            set_path_to_output(PATH_TO_OUTPUT)
            csv = page_rec(cv2.imread(os.path.abspath(PATH_TO_IMG + img), 0))
            # send_to_telegram
            send_file(PATH_TO_OUTPUT, 'document', message.from_user.id)
            # send_to_google-sheets


            os.remove(os.path.abspath(PATH_TO_IMG + img))

        tables = os.listdir(PATH_TO_CSV)
        for csv in tables:
            os.remove(os.path.abspath(PATH_TO_CSV + csv))


bot.infinity_polling()
