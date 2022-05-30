import json
import os

PATH_TO_JSON = '../bot/clients.json'
#json = {id: [spreadsheet_id, mode]}


def create_json():
    if os.path.exists(PATH_TO_JSON):
        pass
    else:
        with open(PATH_TO_JSON, 'w+') as file:
            json.dump({}, file)


def is_client_exist(id: int):
    with open(PATH_TO_JSON, "r") as file:
        clients = json.loads(file.read())
    if str(id) in clients.keys():
        return True
    return False


def set_client(id: int, spreadsheet_id: str = None, mode: str = 0):
    with open(PATH_TO_JSON, "r+") as file:
        clients = json.loads(file.read())
    clients[id] = [spreadsheet_id, mode]
    with open(PATH_TO_JSON, "w") as file:
        json.dump(clients, file)


def get_client(id: int) -> [str, str]:
    with open(PATH_TO_JSON, "r") as file:
        clients = json.loads(file.read())
    return clients.get(str(id))


def get_spreadsheet_id(id: int) -> str:
    return get_client(id)[0]


def get_mode(id: int) -> str:
    if not is_client_exist(id):
        return '0'
    return get_client(id)[1]
