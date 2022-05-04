import os
import telebot
from pdf2image import convert_from_path

import keys  # файл с ключами


def create_infrastructure():
    if os.path.exists("../tmp"):
        pass
    else:
        os.mkdir("../tmp")
        os.mkdir("../tmp/pdf")
        os.mkdir("../tmp/images")
        os.mkdir("../tmp/tables")


def send_document(path: str, chat_id: str):
    doc = open(path, 'rb')
    bot.send_document(chat_id, doc)
    bot.send_document(chat_id, "FILEID")


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
        for img in images:
            print(img)
            csv = convert_img_to_csv(img)
            # TODO send csv
            send_document(os.path.abspath("../tmp/images/" + img), message.from_user.id)
            os.remove(os.path.abspath("../tmp/images/" + img))
            print("end")


bot.infinity_polling()
