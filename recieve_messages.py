from telebot import TeleBot
import random
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
from pyowm import OWM
from subprocess import Popen
import datetime
from classes import Users, Reminder, Events, Words, Emoji
import peewee
from telegramcalendar import create_calendar, number_keyboard
import pprint


Popen("send_messages.py", shell=True)
bot = TeleBot("446864098:AAGMu25VfSzGx-sHRQ-rGjJ81n_8JKQ5AQI")
action = dict()
for i in Users.select():  # инициализация action для всех сохранённых пользователей в DB
    action[i.id] = 'answer'

file = open('event_categories.txt')
lines = file.readlines()
database = peewee.SqliteDatabase("database.db")
current_shown_dates = {}
date = datetime.date(1, 1, 1)
words = Words()
emoji = Emoji()
owm = OWM('ed0a22544e011704dca2f50f3399864f', language="ru")
keyboard = ReplyKeyboardMarkup()


def get_id():
    try:  # пересчёт номеров мероприятий, у каждого мероприятия есть свой id
        id = 0
        for i in Events.select():
            if i.id > id:
                id = i.id
        id += 1
    except:
        id = 0
    return id


def event_invite(msg):
    Event = Events.select().where((Events.creator == msg.chat.id) & (Events.status == 4)).get()
    for i in Users.select():
        if msg.chat.id != i.id and i.fun.find(Event.fun) + 1:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(text='Хочу пойти', callback_data='ev_invite' + str(Event.id)))
            bot.send_message(i.id, text='Новое мероприятие!' + '\n' +
                                        'Время: ' + str(Event.time) + '\n' +
                                        'Дата: ' + str(Event.date) + '\n' + 'Описание:' + Event.text,
                             reply_markup=keyboard)
    Event.status = 0
    Event.save()


def event_create_step1(msg):
    get_calendar(msg)
    bot.send_message(msg.chat.id,
                     text='Ваша категория добавлена, теперь напишите описание вашего данного мероприятия',
                     reply_markup=keyboard)
    Event = Events.create(
        id=get_id(),
        creator=msg.chat.id,
        date=datetime.date(1, 1, 1),
        time=datetime.time(0, 0, 0),
        text='NULL',
        count=-1,
        fun=msg.text,
        address='NULL',
        members='',
        status=1
    )
    Event.save()


def event_create_step2(msg):
    global date, action
    try:
        Event = Events.select().where((Events.count == -1) & (Events.creator == msg.chat.id)).get()
        if Event.status == 1:
            if date == datetime.date(1, 1, 1):
                bot.send_message(msg.chat.id, text='Ты забыл ввести дату!')
                return
            Event.date = date
            Event.text = msg.text
            bot.send_message(msg.chat.id, text='Укажите время мероприятия... в формате HH:MM')
            Event.status = 2
            Event.save()
        elif Event.status == 2:
            Event.time = datetime.time(int(msg.text[0:2]), int(msg.text[3:5]))
            bot.send_message(msg.chat.id, text='Отправьте геолокацию с адресом мероприятия')
            Event.status = 3
            Event.save()
    except:
        bot.send_message(msg.chat.id, text='Проверь правильность ввода данных')


def event_create(msg):
    global action, date, keyboard
    if msg.text + '\n' in lines:
        event_create_step1(msg)
    else:
        event_create_step2(msg)


def event_list(msg):
    global keyboard
    events = Events.select().where((Events.creator == msg.chat.id) & (Events.status == 0))
    if len(events) > 0:
        bot.send_message(msg.chat.id, text='Ваши мероприятия:', reply_markup=keyboard)
    count_admin = 1
    for i in events:
        event_information(msg, i, count_admin, 1)
        count_admin += 1
    count_member = 1
    for i in Events.select():
        if i.members.find(str(msg.chat.id)) != -1:
            if count_member == 1:
                bot.send_message(msg.chat.id, text='Мероприятия, на которые вы идёте:', reply_markup=keyboard
                                 )
            event_information(msg, i, count_member, 0)
            count_member += 1
    if count_admin == 1 and count_member == 1:
        bot.send_message(msg.chat.id, text='У вас нет активных мероприятий', reply_markup=keyboard)


def event_information(msg, event, number, is_creator):
    keyboard = InlineKeyboardMarkup()
    text = str(number) + ') ' + event.text + '\n' + 'Дата: ' + str(event.date) + '\n'
    keyboard.add(InlineKeyboardButton(text='Подробнее...', callback_data='info_' + str(event.id)))
    if is_creator:
        keyboard.add(InlineKeyboardButton(text='Удалить', callback_data='del_' + str(event.id)))
    else:
        keyboard.add(InlineKeyboardButton(text='Покинуть', callback_data='leave_' + str(event.id)))
    bot.send_message(msg.chat.id, text=text, reply_markup=keyboard)


def event(msg):
    global date
    global keyboard
    global action
    if action[msg.chat.id] == 'event':
        if msg.text == 'Создать мероприятие':
            keyboard = ReplyKeyboardMarkup()
            for i in lines:
                keyboard.add(i)
            bot.send_message(msg.chat.id, text='Выберите категорию вашего мероприятия:', reply_markup=keyboard)
            keyboard = ReplyKeyboardRemove()
            action[msg.chat.id] = 'event_create'
        elif msg.text == 'Посмотреть список моих мероприятий':
            keyboard = ReplyKeyboardRemove()
            event_list(msg)
            action[msg.chat.id] = 'answer'
    elif action[msg.chat.id] == 'event_create':
        event_create(msg)


def fun_adding(msg):
    keyboard = InlineKeyboardMarkup()
    k = 0
    for i in lines:
        keyboard.add(InlineKeyboardButton(text=i, callback_data='fun_' + str(k)))
        k += 1
    keyboard.add(InlineKeyboardButton(text="Завершить", callback_data='fun_end'))
    bot.send_message(msg.chat.id, text='Добавь развлечения в этот список!', reply_markup=keyboard)
    action[msg.chat.id] = 'fun_add'


def fun_removing(msg):
    keyboard = InlineKeyboardMarkup()
    k = 0
    for i in lines:
        keyboard.add(InlineKeyboardButton(text=i, callback_data='fun_' + str(k)))
        k += 1
    keyboard.add(InlineKeyboardButton(text="Завершить", callback_data='fun_end'))
    bot.send_message(msg.chat.id, text='Удали развлечения из этого списка', reply_markup=keyboard)
    action[msg.chat.id] = 'fun_remove'


def fun(msg):
    global action
    if action[msg.chat.id] == 'fun':
        if msg.text == 'Добавить развлечение':
            fun_adding(msg)
        elif msg.text == 'Удалить развлечение':
            fun_removing(msg)


def review(msg):
    global action
    global keyboard
    if action[msg.chat.id] != "review":
        bot.send_message(msg.chat.id, text="Напиши мне отзыв одним сообщением, я его передам разработчику!",
                         reply_markup=keyboard)
        action[msg.chat.id] = "review"
    else:
        bot.send_message(msg.chat.id, text="Записал твой отзыв, спасибо!", reply_markup=keyboard)
        file4 = open('reviews.txt', "a")
        file4.write(msg.text + '\n')
        file4.close()
        action[msg.chat.id] = 'answer'


def find_friend(msg):
    user = Users.get(Users.id == msg.chat.id)
    hobbies = list(user.hobbies.split())
    bot.send_message(msg.chat.id, text='Выполняю поиск...')
    for i in hobbies:  # список хобби
        for j in Users.select():  # список всех возможных
            hobbies_friend = list(j.hobbies.split())
            if i in hobbies_friend and j.id != user.id:
                bot.send_message(j.id,
                                 text='Я нашёл тебе друга!' + '\n' + 'Его зовут ' + user.first_name + ' ' + user.second_name
                                      + '\n' + 'Его репутация - ' + str(user.reputation)
                                      + '\n' + 'Его телефон ' + user.telephone)
                bot.send_message(msg.chat.id,
                                 text='Я нашёл тебе друга!' + '\n' + 'Его зовут ' + j.first_name + ' ' + j.second_name
                                      + '\n' + 'Его репутация - ' + str(j.reputation)
                                      + '\n' + 'Его телефон ' + j.telephone)
                return
    bot.send_message(msg.chat.id, text='Друг не найден(')


def memory(msg):
    global action, date
    try:
        time = datetime.time(int(msg.text[0:2]), int(msg.text[3:5]))  # этот костыль тоже нужно исправить
        text = msg.text[6:]
        reminder = Reminder.create(
            id=msg.chat.id,
            text=text,
            date=date,
            time=time
        )
        reminder.save()
        bot.send_message(msg.chat.id, text="Хорошо! Обязательно тебе напомню!")
        action[msg.chat.id] = 'answer'
        date = ''
    except:
        bot.send_message(msg.chat.id, text="Проверь правильность ввода данных! Не забудь указать дату!")
        return


def value_reg(msg):
    user = Users.get(Users.id == msg.chat.id)
    global action
    keyboard = ReplyKeyboardRemove()
    if msg.text == 'Да' or action[msg.chat.id] == 'reg_country' or action[msg.chat.id] == 'reg_hobbies' or action[
        msg.chat.id] == 'reg_end':
        if action[msg.chat.id] == 'reg_telephone':
            keyboard = ReplyKeyboardMarkup()
            bot.send_message(msg.chat.id, text="Отлично! Теперь тебе нужно внести данные, это не займёт много времени!",
                             reply_markup=keyboard)
            keyboard.add(
                KeyboardButton("Отправить номер телефона", request_contact=True)
            )
            bot.send_message(msg.chat.id, text='Отправь мне свой номер телефона', reply_markup=keyboard)
            action[msg.chat.id] = 'reg_country'
            return
        elif action[msg.chat.id] == 'reg_country':
            bot.send_message(msg.chat.id, text="Записал твой номер! Теперь напиши город, в котором ты проживаешь",
                             reply_markup=keyboard)
            user.telephone = msg.contact.phone_number
            user.save()
            action[msg.chat.id] = 'reg_hobbies'
            return
        elif action[msg.chat.id] == 'reg_hobbies':
            bot.send_message(msg.chat.id,
                             text='Записал твой город! Теперь отметь хэштэги по своим интересам, чтобы другим людям '
                                  'было проще найти тебя ')
            user.country = msg.text
            user.save()
            action[msg.chat.id] = 'reg_end'
            return
        elif action[msg.chat.id] == 'reg_end':
            bot.send_message(msg.chat.id, text='Записал твои хобби, спасибо за регистрацию!')
            user.hobbies += msg.text
            user.save()
            action[msg.chat.id] = 'answer'
            return
    elif msg.text == 'Нет, не разрешаю':
        keyboard = ReplyKeyboardRemove()
        bot.send_message(msg.chat.id, text='В таком случае вы не сможете учавствовать в мероприятиях и созздавать их.',
                         reply_markup=keyboard)


def actions(msg):
    global action
    if 'fun' in action[msg.chat.id]:
        fun(msg)
    if 'weather_reg' in action[msg.chat.id]:
        weather_reg(msg)
    elif 'reg' in action[msg.chat.id]:
        value_reg(msg)
    elif action[msg.chat.id] == 'answer':
        bot.send_message(msg.chat.id, text=answer(msg), reply_markup=keyboard)
    elif action[msg.chat.id] == 'review':
        review(msg)
    elif action[msg.chat.id] == 'memory':
        memory(msg)
    elif 'event' in action[msg.chat.id]:
        event(msg)


def weather_reg(msg):
    global action, keyboard
    user = Users.get(Users.id == msg.chat.id)
    if action[msg.chat.id] == 'weather_reg':
        if msg.text == 'Да' or msg.text == 'да':
            user.weather = 1
            user.save()
            bot.send_message(msg.chat.id, text='В какое время ты бы хотел получать уведомления?', reply_markup=keyboard)
            action[msg.chat.id] = 'weather_reg1'
        if msg.text == 'Нет' or msg.text == 'нет':
            user.weather = -1
            user.save()
            keyboard = ReplyKeyboardRemove()
            bot.send_message(msg.chat.id, text="Хорошо, как скажешь)", reply_markup=keyboard)
    else:
        try:
            user.weather_time = datetime.time(int(msg.text[0:2]), int(msg.text[3:5]))
            bot.send_message(msg.chat.id, text='Хорошо, буду тебя предупреждать! Каждый день в ' + msg.text,
                             reply_markup=keyboard)
            action[msg.chat.id] = 'answer'
            user.save()
        except:
            bot.send_message(msg.chat.id, text='Не правильный ввод, повтори ещё раз!', reply_markup=keyboard)


def weather(msg, latitude, longitude):
    obs = owm.weather_at_coords(latitude, longitude)
    w = obs.get_weather()
    wind = w.get_wind()
    temp = w.get_temperature(unit='celsius')
    text = 'Сегодня ' + w.get_detailed_status()
    text1 = 'Температура воздуха: ' + str(round(temp['temp'])) + '°C' + '\n'
    text2 = 'Ветер будет достигать ' + str(round(wind['speed'])) + ' м/c' + '\n'
    text = text + ' ' + emoji.weather1(w.get_status()) + '\n' + text1 + text2
    keyboard = ReplyKeyboardRemove()
    bot.send_message(msg.chat.id, text=text, reply_markup=keyboard)
    if w.get_status() == 'Rain' and round(temp['temp']) < 0:
        bot.send_message(msg.chat.id,
                         text="Рекомендую тебе взять зонтик и одеться по теплее" + emoji.pictures['зонт'] +
                              emoji.pictures['пальто'] +
                              emoji.pictures['перчатки'])
    elif w.get_status() == 'Rain':
        bot.send_message(msg.chat.id, text="Рекомендую тебе взять зонтик" + emoji.pictures['зонт'])
    elif round(temp['temp']) < 0:
        bot.send_message(msg.chat.id,
                         text="Рекомендую тебе одеться по теплее" + emoji.pictures['пальто'] + emoji.pictures[
                             'перчатки'])
    user = Users.get(Users.id == msg.chat.id)
    if user.weather == 0:
        global action
        keyboard = ReplyKeyboardMarkup()
        keyboard.add(
            KeyboardButton('Да'),
            KeyboardButton('Нет'))
        bot.send_message(msg.chat.id, text="Хочешь, чтобы я сообщал тебе погоду каждый день?", reply_markup=keyboard)
        action[msg.chat.id] = 'weather_reg'
        return


def hello(msg):
    global action
    try:
        user = Users.get(Users.id == msg.chat.id)
        bot.send_message(msg.chat.id, text='Приветствую вас, ' + user.first_name +
                                           '! \nЕсли у вас есть какие-то вопросы, используйте команду /help')
    except:
        bot.send_message(msg.chat.id, text="Привет! Я бот Друг! Рад с тобой познакомиться!")
        first_name = msg.from_user.first_name
        last_name = msg.from_user.last_name
        if msg.from_user.first_name == None:
            first_name = 'Unnamed'
        if msg.from_user.last_name == None:
            last_name = ' '
        User = Users.create(id=msg.chat.id,
                            telephone='NULL',
                            country='NULL',
                            hobbies='',
                            first_name=first_name,
                            second_name=last_name,
                            reputation=0,
                            latitude=0.0,
                            longitude=0.0,
                            weather=0,
                            weather_time=datetime.time(0, 0, 0),
                            fun=''
                            )
        User.save()
        keyboard = ReplyKeyboardMarkup()
        keyboard.add(
            KeyboardButton("Да"),
            KeyboardButton("Нет, не разрешаю"))
        bot.send_message(msg.chat.id,
                         text='Для того, чтобы тебе находить друзей, мне надо собирать личную информацию, ты разрешаешь?',
                         reply_markup=keyboard)
        action[msg.chat.id] = 'reg_telephone'


def answer(msg):
    text = msg.text.lower()
    global keyboard, action
    user = Users.get(Users.id == msg.chat.id)
    for i in words.welcome:
        i = i.lower()
        if i.find(text) != -1:
            return words.welcome[random.randint(0, len(words.welcome) - 1)]
    for i in words.leave:
        i = i.lower()
        if i.find(text) != -1:
            return words.leave[random.randint(0, len(words.leave) - 1)]
    if text.find("как") + 1 and text.find("дела") + 1:
        keyboard = ReplyKeyboardMarkup()
        keyboard.add(
            KeyboardButton("Плохо" + emoji.pictures['грусть']),
            KeyboardButton("Хорошо" + emoji.pictures['улыбка']),
            KeyboardButton("Отлично" + emoji.pictures['улыбка1']))
        return "У меня всё хорошо, а у вас?"
    elif text.find("плохо") + 1:
        keyboard = ReplyKeyboardRemove()
        return "Надеюсь, что в скором времени будет хорошо:)" + emoji.pictures['подмигивание']
    elif text.find("хорошо") + 1:
        keyboard = ReplyKeyboardRemove()
        return "Рад за вас!"
    elif text.find("отлично") + 1:
        keyboard = ReplyKeyboardRemove()
        return "Это просто прекрасно!"
    elif text.find("погода") + 1 or text.find("погоду") + 1 or text.find("погоде") + 1 or text.find("погодой") + 1:
        receive_weather(msg)
    elif text.find("отзыв") + 1:
        review(msg)
    elif text.find('репутация') + 1:
        receive_reputation(msg)
    elif text.find('поменя') + 1 and text.find('время') + 1 and text.find('уведомлени') + 1:
        receive_change_weather(msg)
    elif text.find('найди') + 1 and text.find('друга'):
        find_friend(msg)
    elif text.find('напомин') + 1 or text.find('напомни') + 1:
        receive_memory(msg)
    elif text.find('развлечен') + 1:
        receive_fun(msg)
    elif text.find('мероприяти') + 1:
        receive_event(msg)
    else:
        bot.send_message(msg.chat.id, text='Я тебя не понимаю')


def get_calendar(msg):
    now = datetime.datetime.now()  # Current date
    chat_id = msg.chat.id
    date = (now.year, now.month)
    current_shown_dates[chat_id] = date  # Saving the current date in a dict
    markup = create_calendar(now.year, now.month)
    bot.send_message(msg.chat.id, "Пожалуйста, выберете дату", reply_markup=markup)


@bot.message_handler(commands=['number'])
def send_keyboard(msg):
    markup = number_keyboard()
    bot.send_message(msg.chat.id, text="Укажите время: ", reply_markup=markup)


@bot.message_handler(commands=['delete'])
def delete(msg):
    User = Users.get(Users.id == msg.chat.id)
    User.delete_instance()
    bot.send_message(msg.chat.id, text='Вы были успешно удалены из базы данных')


@bot.message_handler(content_types='contact')
def phone(msg):
    if action[msg.chat.id] == 'reg_country':
        value_reg(msg)


@bot.message_handler(content_types='location')
def location(msg):
    global action, date
    if action[msg.chat.id] != 'event_create':
        keyboard = ReplyKeyboardRemove()
        user = Users.get(Users.id == msg.chat.id)
        user.latitude = msg.location.latitude
        user.longitude = msg.location.longitude
        user.save()
        bot.send_message(msg.chat.id, text='Записал твою геолокацию, спасибо!', reply_markup=keyboard)
        weather(msg, user.latitude, user.longitude)
    else:
        Event = Events.select().where((Events.count == -1) & (Events.creator == msg.chat.id)).get()
        Event.address = str(msg.location.latitude) + ',' + str(msg.location.longitude)
        Event.status = 4
        Event.count = 0
        Event.save()
        action[msg.chat.id] = 'answer'
        date = datetime.datetime(1, 1, 1)
        bot.send_message(msg.chat.id, text='Мероприетие успешно создано!')
        event_invite(msg)


@bot.callback_query_handler(func=lambda call: call.data[0:13] == 'calendar-day-')
def get_day(call):
    global date
    global action
    global date
    chat_id = call.message.chat.id
    saved_date = current_shown_dates.get(chat_id)
    if (saved_date is not None):
        day = call.data[13:]
        date = datetime.date(int(saved_date[0]), int(saved_date[1]), int(day))
        bot.answer_callback_query(call.id, text="Дата выбрана")
        if action[call.message.chat.id] == 'memory':
            bot.send_message(call.message.chat.id,
                             text='Напиши время и само напоминание')

    else:
        bot.answer_callback_query(call.id, text="Ошибка ввода даты")


@bot.callback_query_handler(func=lambda call: call.data == 'next-month')
def next_month(call):
    chat_id = call.message.chat.id
    saved_date = current_shown_dates.get(chat_id)
    if (saved_date is not None):
        year, month = saved_date
        month += 1
        if month > 12:
            month = 1
            year += 1
        date = (year, month)
        current_shown_dates[chat_id] = date
        markup = create_calendar(year, month)
        bot.edit_message_text("Please, choose a date", call.from_user.id, call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id, text="")
    else:
        pass


@bot.callback_query_handler(func=lambda call: call.data == 'previous-month')
def previous_month(call):
    chat_id = call.message.chat.id
    saved_date = current_shown_dates.get(chat_id)
    if (saved_date is not None):
        year, month = saved_date
        month -= 1
        if month < 1:
            month = 12
            year -= 1
        date = (year, month)
        current_shown_dates[chat_id] = date
        markup = create_calendar(year, month)
        bot.edit_message_text("Please, choose a date", call.from_user.id, call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id, text="")
    else:
        # Do something to inform of the error
        pass


@bot.callback_query_handler(func=lambda call: call.data == 'ignore')
def ignore(call):
    bot.answer_callback_query(call.id, text="")


@bot.callback_query_handler(func=lambda call: 'fun' in call.data)
def fun_call(call):
    global action
    if call.data == 'fun_end':
        fun_call_end(call)
        return
    fun = lines[int(call.data[4:])]
    user = Users.get(Users.id == call.message.chat.id)
    if action[call.message.chat.id] == 'fun_add':
        fun_call_add(call, fun, user)
    if action[call.message.chat.id] == 'fun_remove':
        fun_call_remove(call, fun, user)


def fun_call_end(call):
    keyboard = ReplyKeyboardRemove()
    bot.send_message(call.message.chat.id, text='Спасибо, Внёс изменения !', reply_markup=keyboard)
    action[call.message.chat.id] = 'answer'


def fun_call_add(call, fun, user):
    if not fun[:len(fun) - 1] in user.fun:
        user.fun += ' ' + fun[:len(fun) - 1]
        user.save()
        bot.answer_callback_query(call.id, text="Развлечение добавлено ")
    else:
        bot.answer_callback_query(call.id, text="Развлечение уже добавлено")


def fun_call_remove(call, fun, user):
    if fun[:len(fun) - 1] in user.fun:
        user.fun = user.fun.replace(fun[:len(fun) - 1], '')
        user.fun = user.fun.replace('  ', ' ')
        user.save()
        bot.answer_callback_query(call.id, text="Развлечение удалено")
    else:
        bot.answer_callback_query(call.id, text="Такого развлечения нет")


@bot.callback_query_handler(func=lambda call: 'ev' in call.data)
def event_call(call):
    if call.data[0:9] == 'ev_invite':
        try:
            User = Users.get(Users.id == call.message.chat.id)
            Event = Events.get(Events.id == int(call.data[9:]))
            if Event.members.find(str(call.message.chat.id)) == -1:
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton(text='Принять', callback_data='ev_accept' + str(Event.id) + ':' + str(
                    call.message.chat.id)))
                keyboard.add(
                    InlineKeyboardButton(text='Отклонить', callback_data='ev_reject' + str(Event.id) + ':' + str(
                        call.message.chat.id)))
                bot.send_message(Event.creator,
                                 text='На ваше мероприятие запиисался человек!' + '\n' + User.first_name + ' ' + User.second_name + '\n' + 'Репутация:' + str(
                                     User.reputation) +
                                      '\n' + 'Телефон: ' + User.telephone, reply_markup=keyboard)
                bot.edit_message_text("Ваша заявка отправлена", call.from_user.id, call.message.message_id)
        except:
            bot.send_message(call.message.chat.id, text="К сожалению, мероприятия больше не существует")
    elif call.data[0:9] == 'ev_accept':
        event_id = int(call.data[9:call.data.find(':')])
        user_id = int(call.data[call.data.find(':') + 1:])
        Event = Events.get(Events.id == event_id)
        if Event.members.find(str(user_id)) == -1:
            keyboard = InlineKeyboardMarkup()
            url = InlineKeyboardButton(text="Адрес", url="https://www.google.ru/maps/place/" + Event.address)
            keyboard.add(url)
            bot.send_message(user_id,
                             text='Ваша заявка одобрена!' + '\n' + 'Время: ' + str(Event.time) + '\n' + 'Дата: ' + str(
                                 Event.date) + '\n' + 'Описание: ' + Event.text + '\n', reply_markup=keyboard)
            Event.count += 1
            Event.members += str(user_id) + ' '
            Event.save()
            bot.send_message(Event.creator, text='Пользователю отправлена полная информация о мероприятии')
        else:
            bot.send_message(Event.creator, text='Этот пользователь уже приглашён на мероприятие')

    elif call.data[0:9] == 'ev_reject':
        event_id = int(call.data[9:call.data.find(':')])
        creator = int(call.data[call.data.find(':') + 1:])
        Event = Events.get(Events.id == event_id)
        bot.send_message(creator, text='Ваша заявка на мероприятие: "' + Event.text + '" отклонена!')


@bot.callback_query_handler(func=lambda call: 'info_' in call.data)
def event_info(call):
    try:
        event_id = call.data[5:]
        event = Events.get(Events.id == event_id)
        admin = Users.get(Users.id == event.creator)
        keyboard = InlineKeyboardMarkup()
        url = InlineKeyboardButton(text="Адрес", url="https://www.google.ru/maps/place/" + event.address)
        keyboard.add(url)
        text = 'Описание: ' + event.text + '\n' + 'Время: ' + str(event.time) + '\n' + 'Дата: ' + str(event.date) + '\n'
        text1 = 'Создатель: ' + '\n' + admin.first_name + ' ' + admin.second_name + '\n' + 'Телефон: ' + admin.telephone + '\n' + 'Репутация: ' + str(
            admin.reputation)
        bot.send_message(call.message.chat.id, text=text, reply_markup=keyboard)
        bot.send_message(call.message.chat.id, text=text1)
        text2 = 'Участники:' + '\n'
        for members in event.members.split():
            User = Users.get(Users.id == int(members))
            text2 += User.first_name + ' ' + User.second_name + '\n' + 'Телефон: ' + User.telephone
        if len(text2) > 11:
            bot.send_message(call.message.chat.id, text=text2)
    except:
        pass


@bot.callback_query_handler(func=lambda call: 'del_' in call.data)
def event_delete(call):
    try:
        event_id = call.data[4:]
        event = Events.get(Events.id == event_id)
        for i in list(event.members.split()):
            bot.send_message(int(i), text='К сожалению создатель удалил мероприятие "' + event.text + '"')
        bot.send_message(event.creator, text='Мероприятие успешно удалено')
        event.delete_instance()
        event.save()
    except:
        pass


@bot.callback_query_handler(func=lambda call: 'leave_' in call.data)
def event_delete(call):
    keyboard = InlineKeyboardMarkup()
    event_id = call.data[6:]
    user_id = str(call.message.chat.id)
    try:
        event = Events.get(Events.id == event_id)
        if event.members.find(str(user_id)) != -1:
            event.members = event.members.replace(str(user_id), ' ')
            event.members = event.members.replace('  ', ' ')
            event.count -= 1
            keyboard.add(InlineKeyboardButton(text='Подробнее...', callback_data='info_' + str(event.id)))
            bot.send_message(int(event.creator), text='К сожалению, ваше мероприятие покинул человек!',
                             reply_markup=keyboard)
            event.save()
        else:
            bot.answer_callback_query(call.id, text='Вы уже покинули это мероприятие')
    except:
        bot.send_message(call.message.chat.id, text='Мероприятия не существует')


@bot.callback_query_handler(func=lambda call: 'rep+' in call.data)
def rep_positive(call):
    user = Users.get(Users.id == int(call.data[5:]))
    user.reputation += 1
    bot.edit_message_text("*пользователь оценён*", call.from_user.id, call.message.message_id)
    user.save()


@bot.callback_query_handler(func=lambda call: 'rep-' in call.data)
def rep_positive(call):
    user = Users.get(Users.id == int(call.data[5:]))
    user.reputation -= 1
    bot.edit_message_text("*пользователь оценён*", call.from_user.id, call.message.message_id)
    user.save()


@bot.callback_query_handler(func=lambda call: 'number_' in call.data)
def send_keyboard(call):
    global time
    markup = number_keyboard()
    if len(call.data) == 8:
        if len(time) == 2:
            time += ':' + call.data[7:]
        else:
            time += call.data[7:]
        bot.edit_message_text("Укажите время: " + time, call.from_user.id, call.message.message_id, reply_markup=markup)
    elif call.data == "number_back":
        if len(time) == 4:
            time = time[:3]
        else:
            time = time[:len(time) - 1]
        bot.edit_message_text("Укажите время: " + time, call.from_user.id, call.message.message_id, reply_markup=markup)
    elif call.data == "number_done":
        bot.edit_message_text("Вы выбрали время: " + time, call.from_user.id, call.message.message_id,
                              reply_markup=markup)
    elif call.data == "number_clear":
        time = ''
        bot.edit_message_text("Укажите время: " + time, call.from_user.id, call.message.message_id, reply_markup=markup)


@bot.message_handler(commands=['weather'])
def receive_weather(msg):
    user = Users.get(Users.id == msg.chat.id)
    if user.latitude == 0 or user.longitude == 0:
        keyboard = ReplyKeyboardMarkup()
        keyboard.add(
            KeyboardButton("Отправить геолокацию", request_location=True)
        )
        bot.send_message(msg.chat.id, text='Прости, но я не знаю твоей геолокации:(', reply_markup=keyboard)
        return
    else:
        weather(msg, user.latitude, user.longitude)


@bot.message_handler(commands=['events'])
def receive_event(msg):
    global keyboard, action, date
    keyboard = ReplyKeyboardMarkup()
    keyboard.add(
        KeyboardButton('Создать мероприятие'),
        KeyboardButton('Посмотреть список моих мероприятий')
    )
    bot.send_message(msg.chat.id, text='Что вы хотите сделать?', reply_markup=keyboard)
    action[msg.chat.id] = 'event'
    keyboard = ReplyKeyboardRemove()


@bot.message_handler(commands=['find_friend'])
def receive_friend(msg):
    find_friend(msg)


@bot.message_handler(commands=['fun'])
def receive_fun(msg):
    keyboard = ReplyKeyboardMarkup()
    keyboard.add(
        KeyboardButton('Добавить развлечение'),
        KeyboardButton('Удалить развлечение')
    )
    bot.send_message(msg.chat.id, text='Что вы хотите сделать?', reply_markup=keyboard)
    action[msg.chat.id] = 'fun'
    actions(msg)


@bot.message_handler(commands=['change_weather'])
def receive_change_weather(msg):
    keyboard = ReplyKeyboardMarkup()
    keyboard.add(
        KeyboardButton('Да'),
        KeyboardButton('Нет'))
    bot.send_message(msg.chat.id, text="Хочешь, чтобы я сообщел тебе погоду каждый день?", reply_markup=keyboard)
    action[msg.chat.id] = 'weather_reg'


@bot.message_handler(commands=['memory'])
def receive_memory(msg):
    get_calendar(msg)
    action[msg.chat.id] = 'memory'


@bot.message_handler(commands=['review'])
def receive_review(msg):
    review(msg)


@bot.message_handler(commands=['reputation'])
def receive_reputation(msg):
    user = Users.get(Users.id == msg.chat.id)
    if user.reputation < 2 and user.reputation > -2:
        bot.send_message(msg.chat.id, text='Твоя репутация: ' + str(user.reputation) + ' (нейтральная)')
    elif int(user.reputation) > 2:
        bot.send_message(msg.chat.id, text='Твоя репутация: ' + str(
            user.reputation) + ' (к тебе хорошо относятся твои друзья)')
    else:
        bot.send_message(msg.chat.id, text='Твоя репутация: ' + str(
            user.reputation) + ' (к тебе плохо относятся твоя друзья)')


@bot.message_handler(commands=['start'])
def start(msg):
    hello(msg)


@bot.message_handler(commands=['help'])
def help(msg):
    bot.send_message(msg.chat.id, text='/weather - Узнать погоду по вашему местоположению\n' +
                                       '/events - Создать/Удалить/Узнать ваши мероприятия\n' +
                                       '/find_friend - Найти друга со схожими интересами\n' +
                                       '/fun - Редактировать свои развлечения\n' +
                                       '/change_weather - изменить время отправки погоды\n' +
                                       '/reputation - посмотреть свою репутацию\n' +
                                       '/help - посмотреть список комманд\n' +
                                       '/start - начать работу\n' +
                                       '/cancel - отменить последнее действие\n' +
                                       '/review - тех.поддержка\n' +
                                       '/memory - добавить напоминание\n')


@bot.message_handler(commands=['cancel'])
def cancel(msg):
    keyboard = ReplyKeyboardRemove()
    bot.send_message(msg.chat.id, text='Действие отменено', reply_markup=keyboard)
    action[msg.chat.id] = 'answer'
    try:
        Event = Events.select().where(Events.count == -1).get()
        Event.delete_instance()
        Event.save()
    except:
        pass


@bot.message_handler(content_types=["text"])
def receive_message(msg):
    global action
    if not msg.chat.id in action.keys():
        action[msg.chat.id] = 'answer'
    try:
        user = Users.get(Users.id == msg.chat.id)
    except:
        hello(msg)
    actions(msg)


bot.polling(none_stop=True)
