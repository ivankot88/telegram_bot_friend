from telebot import TeleBot
import random
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
from pyowm import OWM
from Emoji import emoji, emoji_weather
import sqlite3
import time
import datetime
from Python_file import Users, Events, Reminder

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
    text = text + ' ' + emoji_weather(w.get_status()) + '\n' + text1 + text2
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


while True:
    time1 = datetime.datetime.today()
    date = datetime.date.today()
    try:
        reminder = Reminder.select().where((Reminder.time == datetime.time(time1.hour, time1.minute)) &
                                           (Reminder.date == datetime.date(date.year, date.month, date.day,)))
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
    time.sleep(60)

# events (id, time, data, text, fun)
