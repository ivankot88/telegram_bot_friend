from telebot import TeleBot
import random
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
from pyowm import OWM
import sqlite3
import time
import datetime
from classes import Users, Events, Reminder, Emoji

emoji = Emoji()
database = sqlite3.connect("database.db")
cursor = database.cursor()
owm = OWM('ed0a22544e011704dca2f50f3399864f', language="ru")
bot = TeleBot("446864098:AAGMu25VfSzGx-sHRQ-rGjJ81n_8JKQ5AQI")


def weather(id, latitude, longitude):
    obs = owm.weather_at_coords(latitude, longitude)
    w = obs.get_weather()
    wind = w.get_wind()
    temp = w.get_temperature(unit='celsius')
    text = 'Сегодня ' + w.get_detailed_status()
    text1 = 'Температура воздуха: ' + str(round(temp['temp'])) + '°C' + '\n'
    text2 = 'Ветер будет достигать ' + str(round(wind['speed'])) + ' м/c' + '\n'
    text = text + ' ' + emoji.weather1(w.get_status()) + '\n' + text1 + text2
    keyboard = ReplyKeyboardRemove()
    bot.send_message(id, text=text, reply_markup=keyboard)
    if w.get_status() == 'Rain' and round(temp['temp']) < 0:
        bot.send_message(id,
                         text="Рекомендую тебе взять зонтик и одеться по теплее" + emoji['зонт'] + emoji['пальто'] +
                              emoji['перчатки'])
    elif w.get_status() == 'Rain':
        bot.send_message(id, text="Рекомендую тебе взять зонтик" + emoji['зонт'])
    elif round(temp['temp']) < 0:
        bot.send_message(id, text="Рекомендую тебе одеться по теплее" + emoji['пальто'] + emoji['перчатки'])
    return


def get_user(member, other_member, is_creator):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='👍', callback_data='rep+_' + str(other_member)))
    keyboard.add(InlineKeyboardButton(text='👎', callback_data='rep-_' + str(other_member)))
    user = Users.get(Users.id == int(other_member))
    if is_creator == 1:
        text1 = '🔻' + user.first_name + ' ' + user.second_name
    else:
        text1 = user.first_name + ' ' + user.second_name
    bot.send_message(int(member), text=text1)
    bot.send_message(int(member), text="*поставьте оценку*", reply_markup=keyboard)


while True:
    time1 = datetime.datetime.today()
    date = datetime.date.today()
    try:
        reminder = Reminder.select().where((Reminder.time == datetime.time(time1.hour, time1.minute)) &
                                           (Reminder.date == datetime.date(date.year, date.month, date.day)))
        for i in reminder:
            bot.send_message(i.id, text='Должен тебе напомнить:' + '\n' + i.text)
            i.delete_instance()
            i.save()
    except:
        pass
    try:
        user = Users.select().where(
            (Users.weather == 1) & (Users.weather_time == datetime.time(time1.hour, time1.minute)))
        for i in user:
            weather(i.id, i.latitude, i.longitude)
    except:
        pass
    try:
        event = Events.select().where((Events.time == datetime.time(time1.hour, time1.minute)) & (
                    Events.date == datetime.date(date.year, date.month, date.day)) & (Events.status == 0))
        for i in event:  # i - выбранное мероприятие
            i.status = -1
            i.save()
            cut = i.address.find(",")
            weather(int(i.creator), float(i.address[:cut]), float(i.address[cut + 1:]))
            bot.send_message(int(i.creator),
                             text='Ваше мероприятие "' + i.text + '" началось! \nКоличество участников: ' + str(i.count) +
                                  '\nНе забудьте поставить оценку приглашённым для рейтинга.')
            for member in list(i.members.split()):

                cut = i.address.find(",")
                weather(int(member), float(i.address[:cut]), float(i.address[cut + 1:]))
                bot.send_message(int(member),
                                 text='Мероприятие "' + i.text + '" началось! Не забудьте поставить оценку приглашённым для рейтинга')
                get_user(member, i.creator, 1)  # оценка админа
                for other_member in list(i.members.split()):  # оценка других пользователей
                    if other_member != member:
                        get_user(member, other_member, 0)
            # bot.send_message(i.creator,text='Ваше мероприятие "' + i.text + '" началось! Не забудьте поставить оценку приглашённым для рейтинга')
            for member in list(i.members.split()):
                get_user(i.creator, member, 0)
    except:
        pass

    try:
        event_to_delete = Events.select().where(Events.status == -1)
        event_to_delete.delete_instance()
    except:
        pass

    # time.sleep(60)
