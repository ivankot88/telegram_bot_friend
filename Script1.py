from telebot import TeleBot
import random
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
from pyowm import OWM
from subprocess import Popen
import datetime
import pprint
from Python_file import Users, Reminder, Events, Words, Emoji
import peewee
from telegramcalendar import create_calendar

"""
возможности:
-привет, пока, как дела
-матные, хорошие слова(репутация)
-поиск друга
-заполнение анкеты
-возможность оставить отзыв
-возможность напоминания
-запрос погоды
-напоминания о погоде каждый день
-база данных
-список увлечений
-база мероприятий, по категориям
"""

Popen("Bot.py", shell=True)
owm = OWM('ed0a22544e011704dca2f50f3399864f', language="ru")
bot = TeleBot("446864098:AAGMu25VfSzGx-sHRQ-rGjJ81n_8JKQ5AQI")

words = Words()
emoji = Emoji()

file = open('Категории мероприятий.txt')
lines5 = file.readlines()
keyboard = ReplyKeyboardRemove()
action = dict()
for i in Users.select():  # инициализация action для всех сохранённых пользователей в DB
    action[i.id] = 'answer'
database = peewee.SqliteDatabase("database.db")
current_shown_dates = {}
date = datetime.date(1, 1, 1)


def event(msg):
    global date
    global action
    global keyboard
    try:  # пересчёт номеров мероприятий, у каждого мероприятия есть свой id
        id = 0
        for i in Events.select():
            if i.id > id:
                id = i.id
        id += 1
    except:
        id = 0
    if action[msg.chat.id] == 'event':
        if msg.text == 'Создать мероприятие':
            keyboard = ReplyKeyboardMarkup()
            for i in lines5:
                keyboard.add(i)
            bot.send_message(msg.chat.id, text='Выберите категорию вашего мероприятия:', reply_markup=keyboard)
            action[msg.chat.id] = 'event_create'
            return
        elif msg.text == 'Посмотреть список моих мероприятий':
            keyboard = ReplyKeyboardRemove()
            count = 1
            for i in Events.select().where(Events.user_id == msg.chat.id):
                text = str(count) + ') ' + i.text + '\n' + 'Дата: ' + str(i.date) + '\n' + 'Время: ' + str(
                    i.time) + '\n'
                bot.send_message(msg.chat.id, text=text, reply_markup=keyboard)
                count += 1
            event = Users.get(Users.id == msg.chat.id)
            event = list(event.events.split())
            if len(event) > 0:
                bot.send_message(msg.chat.id, text='Мероприятия, на которые вы идёте:', reply_markup=keyboard)
            for i in event:
                events = Events.get(Events.text == i)
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton(text='Отменить', callback_data='event_cancel' + events.text))
                text = str(count) + ') ' + events.text + '\n' + 'Дата: ' + str(events.date) + '\n' + 'Время: ' + str(
                    events.time) + '\n'
                bot.send_message(msg.chat.id, text=text, reply_markup=keyboard)
            if count == 1:
                bot.send_message(msg.chat.id, text='У тебя нет мероприятий:(', reply_markup=keyboard)
            action[msg.chat.id] = 'answer'
        elif msg.text == 'Удалить мероприятие':
            keyboard = ReplyKeyboardMarkup()
            try:
                for i in Events.select().where(Events.user_id == msg.chat.id):
                    keyboard.add(i.text)
                bot.send_message(msg.chat.id, text='Выберете мероприятие, которое хотели бы удалить',
                                 reply_markup=keyboard)
                action[msg.chat.id] = 'event_delete'
                return
            except:
                keyboard = ReplyKeyboardRemove()
                bot.send_message(msg.chat.id, text='У тебя нет активных мероприятий', reply_markup=keyboard)
                action[msg.chat.id] = 'answer'
                return
    elif action[msg.chat.id] == 'event_create':
        if msg.text + '\n' in lines5:
            keyboard = ReplyKeyboardRemove()
            get_calendar(msg)
            bot.send_message(msg.chat.id,
                             text='Ваша категория добавлена, теперь напишите время и название мероприятия',
                             reply_markup=keyboard)
            Event = Events.create(
                id=id,
                user_id=msg.chat.id,
                date=datetime.date(1, 1, 1),
                time=datetime.time(0, 0, 0),
                text='NULL',
                count=-1,
                fun=msg.text
            )
            Event.save()
            return
        else:
            try:
                Event = Events.select().where((Events.count == -1)
                                              & (Events.user_id == msg.chat.id)
                                              & (Events.text == 'NULL')).get()
                Event.time = datetime.time(int(msg.text[0:2]), int(msg.text[3:5]))
                Event.date = date
                Event.text = msg.text[6:]  # в будущем нужно исправить этот костыль
                Event.count = 0
                Event.save()
                bot.send_message(msg.chat.id, text="Отлично! Сохранил твоё мероприятие!")
                action[msg.chat.id] = 'answer'
                for i in Users.select():
                    if msg.chat.id != i.id and i.fun.find(Event.fun) + 1:
                        keyboard = InlineKeyboardMarkup()
                        keyboard.add(InlineKeyboardButton(text='Я пойду', callback_data='event_' + str(id - 1)))
                        keyboard.add(InlineKeyboardButton(text='Я не пойду', callback_data='event_not'))
                        bot.send_message(i.id, text='В ближайшее время намечается мероприятие:' + '\n' +
                                                    'Время: ' + str(Event.time) + '\n' +
                                                    'Дата: ' + str(Event.date) + '\n' + Event.text,
                                         reply_markup=keyboard)
                Event.save()
                date = datetime.datetime(1, 1, 1)
            except:
                bot.send_message(msg.chat.id, text='Неправильный ввод данных или не выбрана дата! Повтори попытку')
    elif action[msg.chat.id] == 'event_delete':
        try:
            Event = Events.select().where((Events.text == msg.text) & (Events.user_id == msg.chat.id)).get()
            for i in Users.select():
                if i.events.find(msg.text) and i.id != msg.chat.id:
                    bot.send_message(i.id, text='К сожалению данное мероприятие отменяется:(' + '\n' + msg.text)
                    i.events.replace(msg.text, '')
                    i.save()
            Event.delete_instance()
            Event.save()
            keyboard = ReplyKeyboardRemove()
            bot.send_message(msg.chat.id, text='Удалил твоё мероприятие', reply_markup=keyboard)
            action[msg.chat.id] = 'answer'
        except:
            bot.send_message(msg.chat.id, text='Такого варианта нет(')


def fun(msg):
    global action
    if action[msg.chat.id] == 'fun':
        if msg.text == 'Добавить развлечение':
            keyboard = InlineKeyboardMarkup()
            k = 0
            for i in lines5:
                keyboard.add(InlineKeyboardButton(text=i, callback_data='fun_' + str(k)))
                k += 1
            keyboard.add(InlineKeyboardButton(text="Завершить", callback_data='fun_end'))
            bot.send_message(msg.chat.id, text='Добавь развлечения в этот список!', reply_markup=keyboard)
            action[msg.chat.id] = 'fun_add'
            return
        elif msg.text == 'Удалить развлечение':
            keyboard = InlineKeyboardMarkup()
            k = 0
            for i in lines5:
                keyboard.add(InlineKeyboardButton(text=i, callback_data='fun_' + str(k)))
                k += 1
            keyboard.add(InlineKeyboardButton(text="Завершить", callback_data='fun_end'))
            bot.send_message(msg.chat.id, text='Удали развлечения из этого списка', reply_markup=keyboard)
            action[msg.chat.id] = 'fun_remove'
            return


def review(msg):
    global action
    if action[msg.chat.id] != "review":
        bot.send_message(msg.chat.id, text="Напиши мне отзыв одним сообщением, я его передам разработчику!",
                         reply_markup=keyboard)
        action[msg.chat.id] = "review"
    else:
        bot.send_message(msg.chat.id, text="Записал твой отзыв, спасибо!", reply_markup=keyboard)
        file4 = open('Отзывы.txt', "a")
        file4.write(msg.text + '\n')
        file4.close()
        action[msg.chat.id] = 'answer'


def find_friend(msg):
    user = Users.get(Users.id == msg.chat.id)
    hobbies = list(user.hobbies.split())
    flag = True
    bot.send_message(msg.chat.id, text='Выполняю поиск...')
    for i in hobbies:  # список хобби
        for j in Users.select():  # список всех возможных
            hobbies_friend = list(j.hobbies.split())
            if i in hobbies_friend and j.id != user.id:
                flag = False
                bot.send_message(j.id,
                                 text='Я нашёл тебе друга!' + '\n' + 'Его зовут ' + user.first_name + ' ' + user.second_name
                                      + '\n' + 'Его репутация - ' + str(user.reputation)
                                      + '\n' + 'Его телефон ' + user.telephone)
                bot.send_message(msg.chat.id,
                                 text='Я нашёл тебе друга!' + '\n' + 'Его зовут ' + j.first_name + ' ' + j.second_name
                                      + '\n' + 'Его репутация - ' + str(j.reputation)
                                      + '\n' + 'Его телефон ' + j.telephone)
                return
    if flag:
        bot.send_message(msg.chat.id, text='Друг не найден(')


def memory(msg):
    global action
    global date
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
                             text='Записал твой город! Теперь расскажи о своих хобби, напиши их через пробел в И.п.')
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
    else:
        bot.send_message(msg.chat.id, text='Хорошо, как хочешь)')


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
    global action
    global keyboard
    user = Users.get(Users.id == msg.chat.id)
    if action[msg.chat.id] == 'weather_reg':
        if msg.text == 'Да' or msg.text == 'да':
            user.weather = 1
            user.save()
            bot.send_message(msg.chat.id, text='В какое время ты бы хотел получать уведомления?', reply_markup=keyboard)
            action[msg.chat.id] = 'weather_reg1'
            return
        if msg.text == 'Нет' or msg.text == 'нет':
            user.weather = -1
            user.save()
            keyboard = ReplyKeyboardRemove()
            bot.send_message(msg.chat.id, text="Хорошо, как скажешь)", reply_markup=keyboard)
            return
    else:
        try:
            user.weather_time = datetime.time(int(msg.text[0:2]), int(msg.text[3:5]))
            bot.send_message(msg.chat.id, text='Хорошо, буду тебя предупреждать! Каждый день в ' + msg.text,
                             reply_markup=keyboard)
            action[msg.chat.id] = 'answer'
            user.save()
            return
        except:
            bot.send_message(msg.chat.id, text='Не правильный ввод, повтори ещё раз!', reply_markup=keyboard)
            return


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
                         text="Рекомендую тебе взять зонтик и одеться по теплее" + emoji.pictures['зонт'] + emoji.pictures['пальто'] +
                              emoji.pictures['перчатки'])
    elif w.get_status() == 'Rain':
        bot.send_message(msg.chat.id, text="Рекомендую тебе взять зонтик" + emoji.pictures['зонт'])
    elif round(temp['temp']) < 0:
        bot.send_message(msg.chat.id, text="Рекомендую тебе одеться по теплее" + emoji.pictures['пальто'] + emoji.pictures['перчатки'])
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
    bot.send_message(msg.chat.id, text="Привет! Я бот Друг! Рад с тобой познакомиться!")
    User = Users.create(id=msg.chat.id,
                        telephone='NULL',
                        country='NULL',
                        hobbies='',
                        first_name=msg.from_user.first_name,
                        second_name=msg.from_user.last_name,
                        reputation=0,
                        latitude=0.0,
                        longitude=0.0,
                        weather=0,
                        weather_time=datetime.time(0, 0, 0),
                        fun='',
                        events=''
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
    return


def answer(msg):
    text = msg.text.lower()
    global keyboard, action
    user = Users.get(Users.id == msg.chat.id)
    for j in words.polite_words:  # вежливые слова
        j = j.lower()
        if text.find(j[0:len(j) - 1]) != -1 and len(text) > 3:
            user.reputation += 1
            user.save()
    for j in words.curse_words:
        j = j.lower()  # матные слова
        if text.find(j[0:len(j) - 1]) + 1 and len(text) >= 3:
            user.reputation -= 1
            user.save()
            return "Не ругайся, пожалуйста, за матные слова будет снижена твоя репутация!"
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
        recieve_weather(msg)
    elif text.find("отзыв") + 1:
        review(msg)
    elif text.find('репутация') + 1:
        recieve_reputation(msg)
    elif text.find('поменя') + 1 and text.find('время') + 1 and text.find('уведомлени') + 1:
        recieve_change_weather(msg)
    elif text.find('найди') + 1 and text.find('друга'):
        find_friend(msg)
    elif text.find('напомин') + 1 or text.find('напомни') + 1:
        recieve_memory(msg)
    elif text.find('развлечен') + 1:
        recieve_fun(msg)
    elif text.find('мероприяти') + 1:
        recieve_event(msg)
    else:
        bot.send_message(msg.chat.id, text='Я тебя не понимаю')


def get_calendar(msg):
    now = datetime.datetime.now()  # Current date
    chat_id = msg.chat.id
    date = (now.year, now.month)
    current_shown_dates[chat_id] = date  # Saving the current date in a dict
    markup = create_calendar(now.year, now.month)
    bot.send_message(msg.chat.id, "Пожалуйста, выберете дату", reply_markup=markup)


@bot.message_handler(content_types='contact')
def phone(msg):
    if action[msg.chat.id] == 'reg_country':
        value_reg(msg)


@bot.message_handler(content_types='location')
def location(msg):
    keyboard = ReplyKeyboardRemove()
    user = Users.get(Users.id == msg.chat.id)
    user.latitude = msg.location.latitude
    user.longitude = msg.location.longitude
    user.save()
    bot.send_message(msg.chat.id, text='Записал твою геолокацию, спасибо!', reply_markup=keyboard)
    weather(msg, user.latitude, user.longitude)


@bot.callback_query_handler(func=lambda call: call.data[0:13] == 'calendar-day-')
def get_day(call):
    global date
    global action
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
        # Do something to inform of the error
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
        keyboard = ReplyKeyboardRemove()
        bot.send_message(call.message.chat.id, text='Спасибо, Внёс изменения !', reply_markup=keyboard)
        action[call.message.chat.id] = 'answer'
        return
    #############################################
    fun = lines5[int(call.data[4:])]
    user = Users.get(Users.id == call.message.chat.id)
    #############################################
    if action[call.message.chat.id] == 'fun_add':
        if not fun[:len(fun) - 1] in user.fun:
            user.fun += ' ' + fun[:len(fun) - 1]
            user.save()
            bot.answer_callback_query(call.id, text="Развлечение добавлено ")
        else:
            bot.answer_callback_query(call.id, text="Развлечение уже добавлено")
    elif action[call.message.chat.id] == 'fun_remove':
        if fun[:len(fun) - 1] in user.fun:
            user.fun = user.fun.replace(fun[:len(fun) - 1], '')
            user.fun = user.fun.replace('  ', ' ')
            user.save()
            bot.answer_callback_query(call.id, text="Развлечение удалено")
        else:
            bot.answer_callback_query(call.id, text="Такого развлечения нет")


@bot.callback_query_handler(func=lambda call: 'event' in call.data)
def event_call(call):
    if call.data == 'event_not':
        bot.send_message(call.message.chat.id, text='Очень жаль:(')
    elif call.data[0:12] == 'event_cancel':
        User = Users.get(Users.id == call.message.chat.id)
        User.events = User.events.replace(call.data[12:], '')
        User.save()
        bot.answer_callback_query(call.id, text="Мероприятие удалено")
        Event = Events.get(Events.text == call.data[12:])
        Event.count -= 1
        bot.send_message(Event.user_id,
                         text='К сожалению человек не сможет прийти на ваше мероприятие:' + '\n' + Event.text + '\n' +
                              'Количество идущих на данный момент: ' + Event.count)
        Event.save()
    elif int(call.data[6:]) >= 0:
        Event = Events.get(Events.id == int(call.data[6:]))
        Event.count += 1
        bot.send_message(Event.user_id,
                         text='На ваше мероприятие записался человек! ' + 'Количество: ' + str(Event.count))
        bot.send_message(call.message.chat.id, text='Отлично! Хорошо провести вам время!')
        User = Users.get(Users.id == call.message.chat.id)
        User.events += ' ' + Event.text
        Event.save()
        User.save()


@bot.message_handler(commands=['weather'])
def recieve_weather(msg):
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
def recieve_event(msg):
    keyboard = ReplyKeyboardMarkup()
    keyboard.add(
        KeyboardButton('Создать мероприятие'),
        KeyboardButton('Посмотреть список моих мероприятий'),
        KeyboardButton('Удалить мероприятие')
    )
    bot.send_message(msg.chat.id, text='Что вы хотите сделать?', reply_markup=keyboard)
    action[msg.chat.id] = 'event'


@bot.message_handler(commands=['find_friend'])
def recieve_friend(msg):
    find_friend(msg)


@bot.message_handler(commands=['fun'])
def recieve_fun(msg):
    keyboard = ReplyKeyboardMarkup()
    keyboard.add(
        KeyboardButton('Добавить развлечение'),
        KeyboardButton('Удалить развлечение')
    )
    bot.send_message(msg.chat.id, text='Что вы хотите сделать?', reply_markup=keyboard)
    action[msg.chat.id] = 'fun'
    actions(msg)


@bot.message_handler(commands=['change_weather'])
def recieve_change_weather(msg):
    keyboard = ReplyKeyboardMarkup()
    keyboard.add(
        KeyboardButton('Да'),
        KeyboardButton('Нет'))
    bot.send_message(msg.chat.id, text="Хочешь, чтобы я сообщел тебе погоду каждый день?", reply_markup=keyboard)
    action[msg.chat.id] = 'weather_reg'


@bot.message_handler(commands=['memory'])
def recieve_memory(msg):
    get_calendar(msg)

    action[msg.chat.id] = 'memory'


@bot.message_handler(commands=['review'])
def recieve_review(msg):
    review(msg)


@bot.message_handler(commands=['reputation'])
def recieve_reputation(msg):
    user = Users.get(Users.id == msg.chat.id)
    if user.reputation < 2 and user.reputation > -2:
        bot.send_message(msg.chat.id, text='Твоя репутация: ' + str(user.reputation) + ' - нейтральная')
    elif int(user.reputation) > 2:
        bot.send_message(msg.chat.id, text='Твоя репутация: ' + str(
            user.reputation) + ' - положительная(ты вежливый пользователь)')
    else:
        bot.send_message(msg.chat.id, text='Твоя репутация: ' + str(
            user.reputation) + ' - отрицательная (ты часто ругаетешься и грубишь)')


@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id, text="привет, у меня есть такие комманды...")
    help(msg)


@bot.message_handler(commands=['help'])
def help(msg):
    bot.send_message(msg.chat.id, text='/weather - Узнать погоду по вашему местоположению' + '\n' +
                                       '/events - Назначить/Удалить/Узнать ваши мероприятия' + '\n' +
                                       '/find_friend - Найти друга со схожими интересами' + '\n' +
                                       '/fun - Редактировать свои развлечения' + '\n' +
                                       '/change_weather - изменить время отправки погоды' + '\n' +
                                       '/reputation - посмотреть свою репутацию' + '\n' +
                                       '/help - посмотреть список комманд' + '\n' +
                                       '/start - начать работу' + '\n' +
                                       '/cancel - отменить действие')


@bot.message_handler(commands=['cancel'])
def cancel(msg):
    keyboard = ReplyKeyboardRemove()
    bot.send_message(msg.chat.id, text='Действие отменено', reply_markup=keyboard)
    action[msg.chat.id] = 'answer'
    Event = Events.select().where((Events.count == -1)
                                  & (Events.user_id == msg.chat.id)
                                  & (Events.text == 'NULL')).get()
    Event.delete_instance()
    Event.save()


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
