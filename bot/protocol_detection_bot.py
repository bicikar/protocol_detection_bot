import os
import telebot
import requests
from pdf2image import convert_from_path

import keys  # файл с ключами

URL = 'https://api.telegram.org/bot'


def create_infrastructure():
    if os.path.exists("../tmp"):
        pass
    else:
        os.mkdir("../tmp")
        os.mkdir("../tmp/pdf")
        os.mkdir("../tmp/images")
        os.mkdir("../tmp/tables")


def send_photo_file(img: str, chat_id: str):
    files = {'photo': open(img, 'rb')}
    requests.post(f'{URL}{keys.BOT_TOKEN}/sendPhoto?chat_id={chat_id}', files=files)


# TODO
def convert_img_to_csv(img: str) -> str:
    path_to_csv = ""
    return path_to_csv


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
        src = '../tmp/pdf' + message.document.file_name

        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)

        images = convert_from_path(src)

        for i in range(len(images)):
            # Save pages as images in the pdf
            images[i].save('../tmp/images/' + 'img' + str(i) + '.jpg', 'JPEG')

        os.remove(src)

        images = os.listdir("../tmp/images/")
        print(images)
        for img in images:
            print(img)
            csv = convert_img_to_csv(img)
            # TODO send csv
            send_photo_file(os.path.abspath("../tmp/images/" + img), message.from_user.id)
            os.remove(os.path.abspath("../tmp/images/" + img))
            print("end")


bot.infinity_polling()
