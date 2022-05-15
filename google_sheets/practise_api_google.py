# pip install google-api-python-client oauth2client

from pprint import pprint

#  ending on api
import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

print("hello")

CREDENTIALS_FILE = 'creds.json'
spreadsheet_id = '1fOmbOzRUPOhiY4JqEKGjv_kEDNEDPnNVQVtJA4E1yNI'

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive']
)

print("hello")

httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)

# work with api

'''
# Получение значения
values = service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range='A1:E10',
    majorDimension='COLUMNS'
).execute()

pprint(values)

# Изменение значения
values = service.spreadsheets().values().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={
        "valueInputOption": "USER_ENTERED",
        "data": [
            {"range": "B3:C4",
             "majorDimension": "ROWS",
             "values": [["This is B3", "This is C3"],
                        ["This is B4", "This is C4"]]
             },
            {"range": "D5:E6",
             "majorDimension": "COLUMNS",
             "values": [["This is D5", "This is D6"],
                        ["This is E5", "This is E6"]]
             }
        ]
    }
).execute()

pprint(values)
'''

# Добавление листа
'''
results = service.spreadsheets().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={
        "requests": [{
            "addSheet": {
                "properties": {
                    "title": "Новый листочек",
                    "gridProperties": {
                        "rowCount": 20,
                        "columnCount": 12
                    }
                }
            }
        }
        ]
    }).execute()
'''
'''
# Получаем список листов, их Id и название
spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
sheetList = spreadsheet.get('sheets')
for sheet in sheetList:
    print(sheet['properties']['sheetId'], sheet['properties']['title'])

sheetId = sheetList[0]['properties']['sheetId']
'''
print(ord('Z'))
print(ord('Z') - ord('A'))