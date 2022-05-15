from pprint import pprint
import csv
import pandas as pd

import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

cur_spreadsheet_id = '1fOmbOzRUPOhiY4JqEKGjv_kEDNEDPnNVQVtJA4E1yNI'


def connect_to_spreadsheet(spreadsheet_id=cur_spreadsheet_id):
    global cur_spreadsheet_id
    cur_spreadsheet_id = spreadsheet_id

    CREDENTIALS_FILE = 'creds.json'
    cur_spreadsheet_id = spreadsheet_id

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_FILE,
        ['https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive']
    )

    httpAuth = credentials.authorize(httplib2.Http())
    global service
    service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)


def get_all_sheets():
    # Получаем список листов, их Id и название
    global cur_spreadsheet_id, service
    spreadsheet = service.spreadsheets().get(spreadsheetId=cur_spreadsheet_id).execute()
    sheetList = spreadsheet.get('sheets')

    '''
    for sheet in sheetList:
        print(sheet['properties']['sheetId'], sheet['properties']['title'])
    '''

    return sheetList


def get_sheetId(sheet):
    return sheet['properties']['sheetId']


def get_sheetTitle(sheet):
    return sheet['properties']['title']


def get_count_sheets():
    sheetList = get_all_sheets()
    return len(sheetList)


def get_right_age_of_rectangle(left_adge, size_col, size_row):
    if size_col < 0 or size_row < 0:
        print("Смещение от начала прямоугольника должны быть неотрицательные")
        return

    # достали букву
    col_left = left_adge[0]
    if not (ord('A') <= ord(col_left) <= ord('Z')):
        print("Столбцы должны быть заглавными буквами!")
        return
    # вытаскиваем число
    ind_sep = left_adge.find(':', 1)

    if ind_sep == -1:
        print("Нету разделителя :")
        return None
    # print("ind_sep=", ind_sep)

    row_left = left_adge[1:ind_sep]
    # print("row_left = ", row_left)
    row_left = int(row_left)

    # находим правый угол
    if ord(col_left) + size_col - 1 > ord('Z'):
        print("Столбцы должны быть не больше Z")
        return None
    col_right = chr(ord(col_left) + size_col - 1)
    row_right = row_left + size_row - 1

    right_adge = col_right + str(row_right)
    left_adge = col_left + str(row_left)
    return left_adge, right_adge


def check_is_2d_list(list_2d):
    try:
        for col in list_2d:
            for _ in col:
                return True
    except TypeError:
        return False


def get_max_cols_rows_2d_list(list_2d):
    max_col = -1
    try:
        for row in list_2d:
            max_col = max(max_col, len(row))
        return max_col
    except TypeError:
        return -1


def assign_values(values_to_update, title_sheet="Лист1", range_to_update="A1:", majorDimension_to_update="ROWS"):
    global cur_spreadsheet_id, service
    # print('Hello')
    if not range_to_update[1].isdigit():
        print("Дальше буквы Z не работаем! И на втором месте должна стоять цифра!")
        return

    if not check_is_2d_list(values_to_update):
        # print(values_to_update)
        print("Значения должны быть в виде двумерного массива")
        return

    left_adge, right_adge = "", ""
    if majorDimension_to_update == "ROWS":
        size_col = get_max_cols_rows_2d_list(values_to_update)
        size_row = len(values_to_update)
        # print("size_col=", size_col)
        # print("size_row=", size_row)

        left_adge, right_adge = get_right_age_of_rectangle(range_to_update, size_col, size_row)
        # print(left_adge)
        # print(right_adge)
    else:
        pass

    real_range_to_update = left_adge + ":" + right_adge
    # print("real_range_to_update=", real_range_to_update)
    # return

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=cur_spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": title_sheet + "!" + real_range_to_update,
                 "majorDimension": majorDimension_to_update,
                 "values": values_to_update
                 }
            ]
        }
    ).execute()


def assign_csv_file(csv_file, title_sheet="Лист1", range_to_update="A1:"):
    csv_reader = csv.reader(csv_file)
    values_to_update = list(csv_reader)

    assign_values(values_to_update, title_sheet=title_sheet, range_to_update=range_to_update)


def clear_sheet(title_sheet="Лист1", range_to_clear="A1:Z50"):
    global service, spreadsheet_id
    service.spreadsheets().values().clear(
        spreadsheetId=cur_spreadsheet_id,
        range=title_sheet + "!" + range_to_clear,
        body={}
    ).execute()


def create_new_sheet():
    global cur_spreadsheet_id, service
    new_title = "Лист" + str(get_count_sheets() + 1)
    try:
        results = service.spreadsheets().batchUpdate(
            spreadsheetId=cur_spreadsheet_id,
            body={
                "requests": [{
                        "addSheet": {
                            "properties": {
                                "title": new_title,
                            }
                        }
                    }
                ]
            }).execute()
    except TypeError:
        print("Имя занято")


def delete_sheet(sheet_id):
    global service, cur_spreadsheet_id
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=cur_spreadsheet_id,
        body={
            'requests': [
                {
                    "deleteSheet": {
                        "sheetId": sheet_id
                    }
                }
            ]
        }
    ).execute()


if __name__ == '__main__':
    connect_to_spreadsheet()
    sheetList = get_all_sheets()
    '''
    with open('data/2.csv', newline='') as csvfile:
        assign_csv_file(csvfile, range_to_update="B25:")
    '''
    # clear_sheet()
    #create_new_sheet()

    list_val = [[1, 2, 3, 4],
                [5, 6, 7, 8, 9],
                [8, 9],
                [10]]

    assign_values(list_val, "Лист2", range_to_update="B2:")
    clear_sheet("Лист2")
    # assign_values(list_val, range_to_update="K18:")

    #pprint(get_all_sheets())
    #delete_sheet(0)