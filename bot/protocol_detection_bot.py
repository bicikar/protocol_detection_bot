import os
import re

import telebot
import requests
import cv2
from pdf2image import convert_from_path
from aiogram.dispatcher.filters import Text

import keys  # файл с ключами
import working_with_json
from page_recognition.page_rec import page_recognition as page_rec
from page_recognition.page_rec import get_path_to_output as set_path_to_output
from page_recognition.page_rec import pdf_processing as pdf_rec

import google_sheets.google_sheet_api as google_sheet
from pyTelegramBotAPI.telebot import types

URL_TELEGRAM = 'https://api.telegram.org/bot'
URL_GOOGLESHEET = 'https://docs.google.com/spreadsheets/d/'
PATH_TO_TMP = '../tmp'
PATH_TO_IMG = PATH_TO_TMP + '/images/'
PATH_TO_PDF = PATH_TO_TMP + '/pdf/'
PATH_TO_CSV = PATH_TO_TMP + '/csv/'
PATH_TO_OUTPUT = ''
mode = ''
num_of_sheet = 0
bot = telebot.TeleBot(keys.BOT_TOKEN)


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
    if type == "doc":
        with open(file, 'rb') as f:
            bot.send_document(chat_id, f)


def make_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    up_buttons = ["Предоставить свою таблицу", "Сгенерировать таблицу"]
    down_button = "Режим csv"
    keyboard.add(*up_buttons)
    keyboard.add(down_button)
    return keyboard


@bot.message_handler(commands=['start'])
def send_welcome(message):
    working_with_json.create_json()
    keyboard = make_keyboard()
    bot.send_message(message.from_user.id, "Привет!", reply_markup=keyboard)


@bot.message_handler(commands=['link'])
def send_help(message):
    spreadsheet_id = working_with_json.get_spreadsheet_id(message.from_user.id)
    link = 'https://docs.google.com/spreadsheets/d/' + str(spreadsheet_id)
    bot.send_message(message.from_user.id, link)


@bot.message_handler(commands=['keyboard'])
def send_help(message):
    keyboard = make_keyboard()
    bot.send_message(message.from_user.id, "возвращаю клавиатуру", reply_markup=keyboard)


@bot.message_handler(content_types=['text'])
def change_link(message):
    if message.text == "Предоставить свою таблицу":
        del_markup = telebot.types.ReplyKeyboardRemove()
        msg = bot.send_message(message.from_user.id, "Пришлите ссылку на гугл таблицу, в которой разрешено редактирование",
                         reply_markup=del_markup)
        bot.register_next_step_handler(msg, set_spreadsheet_id)
    elif message.text == "Сгенерировать таблицу":
        google_sheet.connect_to_spreadsheet()
        spreadsheet_id = google_sheet.create_new_doc()
        google_sheet.give_everyone_access(role='writer', spreadsheetId=spreadsheet_id)
        working_with_json.set_client(message.from_user.id, spreadsheet_id, 1)
        bot.send_message(message.from_user.id, URL_GOOGLESHEET+spreadsheet_id)
    elif message.text == "Режим csv":
        if working_with_json.is_client_exist(message.from_user.id):
            spreadsheet_id = working_with_json.get_spreadsheet_id(message.from_user.id)
            working_with_json.set_client(message.from_user.id, spreadsheet_id, 0)
        else:
            google_sheet.connect_to_spreadsheet()
            spreadsheet_id = google_sheet.create_new_doc()
            google_sheet.give_everyone_access(role='writer', spreadsheetId=spreadsheet_id)
            working_with_json.set_client(message.from_user.id, spreadsheet_id, 0)


def set_spreadsheet_id(message):
    if re.fullmatch(r"https://docs.google.com/spreadsheets/\S*/edit\S*", message.text):
        spreadsheet_id = message.text[message.text.rfind('/', 0, message.text.rfind('/')) + 1: message.text.rfind('/')]
        working_with_json.set_client(message.from_user.id, spreadsheet_id, 1)
        keyboard = make_keyboard()
        msg = bot.send_message(message.from_user.id, "Данные успешно изменены", reply_markup=keyboard)
    elif message.text == "меню" or message.text == "Меню":
        keyboard = make_keyboard()
        msg = bot.send_message(message.from_user.id, "возвращаю в меню", reply_markup=keyboard)
    else:
        msg = bot.send_message(message.from_user.id, f"Неправильная ссылка, чтобы выйти из режима ввода наберите \"меню\"")
        bot.register_next_step_handler(msg, set_spreadsheet_id)


@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'application/pdf':

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        create_infrastructure()

        create_dir(PATH_TO_PDF + str(message.from_user.id))
        create_dir(PATH_TO_CSV + str(message.from_user.id))
        src = PATH_TO_PDF + str(message.from_user.id) + "/" + message.document.file_name

        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)

        # print(src)
        df = pdf_rec(src)
        list_paths_to_csv = []
        csv_folder = os.listdir(PATH_TO_CSV + str(message.from_user.id))
        for csv in csv_folder:
            list_paths_to_csv.append(PATH_TO_CSV + str(message.from_user.id) + "/" + csv)
        if working_with_json.get_mode(message.from_user.id) == 1:
            spreadsheet_id = working_with_json.get_spreadsheet_id(message.from_user.id)
            google_sheet.connect_to_spreadsheet(spreadsheet_id)
            # print(list_paths_to_csv)
            # print('https://docs.google.com/spreadsheets/d/' + spreadsheet_now)
            google_sheet.assign_pdf_file(list_paths_to_csv, spreadsheet_id=spreadsheet_id)
            bot.send_message(message.from_user.id, "Данные записаны")
        else:
            for csv in list_paths_to_csv:
                send_file(csv, "doc", message.from_user.id)
        for csv in list_paths_to_csv:
            os.remove(csv)
        os.remove(src)


bot.infinity_polling()
