import asyncio
import re
import telethon
import telebot
import urllib
import time
import openpyxl
import json


with open("config.json", "r") as file:
    data = json.load(file)

myBot = telebot.TeleBot(token=data["for_program"]["bot_token"], threaded=False)
client = telethon.TelegramClient('session_test', data["for_program"]["api_id"], data["for_program"]["api_hash"])
#client.start()

adminPhone = ""
adminPassword = 0
phoneNumbers = []
usersID = []
channel_id = data["for_program"]["channel_id"]


checkFileProcessing = False
checkInputPhone = False
checkInputPassword = False


def getPhoneNumbersFromExcel(fileName):
    numbers = []
    index = 1
    wb = openpyxl.reader.excel.load_workbook(filename=fileName)
    wb.active = 0
    sheet = wb.active
    while sheet[f'A{index}'].value != None:
        numbers.append(str(sheet[f'A{index}'].value))
        index += 1
    wb.close()
    return numbers


def saveNumAndUserIDinExcel(fileName, numUsers, IDUsers):
    idIndex = 0
    wb = openpyxl.Workbook()
    sheet = wb.active
    print(numUsers, IDUsers)
    print(len(numUsers), len(IDUsers))
    for num in numUsers:
        sheet[f'A{data["for_excel"]["user_index"]}'] = str(num)
        sheet[f'B{data["for_excel"]["user_index"]}'] = str(IDUsers[idIndex])
        idIndex += 1
        data["for_excel"]["user_index"] += 1
    with open("config.json", "w") as file:
        json.dump(data, file, indent=3)
    wb.save(fileName)
    wb.close()


async def getUserIDAndInviteToChannel(numPhone):
    count = 0
    userID = []
    for num in numPhone:
        contact = telethon.types.InputPhoneContact(client_id=0, phone=num, first_name=str(data["for_user"]["first_name"]), last_name="")
        a = await client(telethon.functions.contacts.ImportContactsRequest([contact]))
        count += 1
        data["for_user"]["first_name"] += 1
        if count % 50 == 0:
            time.sleep(300)
        if len(a.users) != 0:
            if data["for_user"]["first_name"] <= 201:
                print(a.users[0])
                result = await client(telethon.functions.channels.InviteToChannelRequest(
                    channel=channel_id,
                    users=[a.users[0]]
                ))
                print(result)
            userID.append(a.users[0].id)
        else:
            userID.append("Пользователь не найден")
    with open("config.json", "w") as file:
        json.dump(data, file, indent=3)
    return userID


async def get_auth():
    return await client.is_user_authorized()

loop = asyncio.get_event_loop()
loop.run_until_complete(client.connect())


print(myBot.get_me())


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@myBot.message_handler(commands=['start'])
def start(message):
    myBot.send_message(message.chat.id, "Введите /help для помощи")
    a = loop.run_until_complete(get_auth())
    if not a:
        msg = myBot.send_message(message.chat.id, "введите номер телефона аккаунта администратора канала (пример +79141234567)")
        print(msg)
            # myBot.register_next_step_handler(msg, get_admin_phone)


def get_admin_phone(message):
    global adminPhone
    adminPhone = message.text
    if re.match("\+7", adminPhone) and len(adminPhone) == 12:
        loop.run_until_complete(client.send_code_request(adminPhone))
        print(adminPhone, type(adminPhone), len(adminPhone))
        msg1 = myBot.send_message(message.chat.id, "Введите код, который прислал telegram")

        # myBot.register_next_step_handler(msg1, get_admin_password)
    else:
        myBot.send_message(message.chat.id,"Номер введен не корректно")
        # msg1 = myBot.send_message(message.chat.id,
        #                          "введите номер телефона аккаунта администратора канала (пример +79141234567)")
        # myBot.register_next_step_handler(msg1, get_admin_phone)
    print("test")


def get_admin_password(message):
    global adminPhone, adminPassword
    adminPassword = message.text
    print(adminPassword)
    loop.run_until_complete(client.sign_in(adminPhone, adminPassword))


@myBot.message_handler(commands=['help'])
def start(message):
    myBot.send_message(message.chat.id,
                       "/getinfo - получить информацию о состоянии\n/getbd - получить сформированный файл с номирами телефонов\nДля начала работы отправте файл excel с номирами телефонов")


@myBot.message_handler(content_types=["document"])
def getExcel(doc):
    global checkFileProcessing
    fileID = doc.document.file_id
    fileInfo = myBot.get_file(fileID)
    urllib.request.urlretrieve(f'http://api.telegram.org/file/bot{data["for_program"]["bot_token"]}/{fileInfo.file_path}', 'new1.xlsx')
    myBot.send_message(doc.chat.id, "файл получен,\nобработка файла началась\nпо факту завершения бутет сообщение")
    checkFileProcessing = True
    if checkFileProcessing:
        phoneNumbers = getPhoneNumbersFromExcel('new1.xlsx')
        usersID = client.loop.run_until_complete(getUserIDAndInviteToChannel(phoneNumbers))
        client.loop.close()
        saveNumAndUserIDinExcel('DataBase.xlsx', phoneNumbers, usersID)
        myBot.send_message(doc.chat.id, "Работа с файлами завершена")
        checkFileProcessing = False


@myBot.message_handler(commands=['getinfo'])
def getinfo(message):
    if checkFileProcessing:
        myBot.send_message(message.chat.id, "Я работаю с файлом")
    else:
        myBot.send_message(message.chat.id, "Я ничего не делаю")


@myBot.message_handler(commands=['getbd'])
def getbd(message):
    myBot.send_document(message.chat.id, open("DataBase.xlsx", "rb"))
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


myBot.polling(none_stop=True)


# id - 1190636846
# channel id - -1001613425971

