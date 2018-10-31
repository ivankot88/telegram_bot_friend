from telebot import TeleBot
import random
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
from pyowm import OWM
import sqlite3
import time
import datetime
from classes import Users, Events, Reminder, Emoji, Bot_settings

emoji = Emoji()
database = sqlite3.connect("database.db")
cursor = database.cursor()
bot = TeleBot("727398167:AAFa6E7ZjjieCbpqpJhe9CDu_OCazY3vnKs")
telebot = Bot_settings()


def get_user(chosen_member, other_member, is_creator):
    """

    Функция извлекает информацию о пользователе по его id
    и добавляет кнопки для оценки

    """
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='👍', callback_data='rep+_' + str(other_member)))
    keyboard.add(InlineKeyboardButton(text='👎', callback_data='rep-_' + str(other_member)))
    chosen_user = Users.get(Users.id == int(other_member))
    if is_creator == 1:
        text1 = '🔻' + chosen_user.first_name + ' ' + chosen_user.last_name
    else:
        text1 = chosen_user.first_name + ' ' + chosen_user.last_name
    bot.send_message(int(chosen_member), text=text1)
    bot.send_message(int(chosen_member), text="*поставьте оценку*", reply_markup=keyboard)


while True:
    time1 = datetime.datetime.today()
    date = datetime.date.today()
    try:
        reminder = Reminder.select().where((Reminder.time == datetime.time(time1.hour, time1.minute)) &
                                           (Reminder.date == datetime.date(date.year, date.month, date.day)))
        for i in reminder:
            bot.send_message(i.id, text='🗓\nДолжен тебе напомнить:' + '\n' + i.text)
            i.delete_instance()
            i.save()
    except Reminder.DoesNotExist:
        pass
    try:
        user = Users.select().where(
            (Users.weather == 1) & (Users.weather_time == datetime.time(time1.hour, time1.minute)))
        for i in user:
            bot.send_message(i.id, text=telebot.weather_text(i.latitude, i.longitude))
    except Users.DoesNotExist:
        pass
    try:
        event = Events.select().where((Events.time == datetime.time(time1.hour, time1.minute)) & (
                Events.date == datetime.date(date.year, date.month, date.day)) & (Events.status == 0))
        for i in event:     # i - выбранное мероприятие
            cut = i.address.find(",")
            bot.send_message(int(i.creator),
                             text=telebot.weather_text(float(i.address[:cut]), float(i.address[cut + 1:])))
            i.status = -1
            i.save()
            cut = i.address.find(",")
            bot.send_message(int(i.creator),
                             text='✉\nВаше мероприятие "{}" началось! \nКоличество участников: {}'
                                  '\nНе забудьте поставить оценку приглашённым для рейтинга.'.format(i.text,
                                                                                                     str(i.count)))
            for member in list(i.members.split()):
                cut = i.address.find(",")
                bot.send_message(int(member),
                                 text=telebot.weather_text(float(i.address[:cut]), float(i.address[cut + 1:])))
                bot.send_message(int(member),
                                 text='✉\nМероприятие "{}" началось! '
                                      'Не забудьте поставить оценку приглашённым для рейтинга'.format(i.text))
                get_user(member, i.creator, 1)                          # оценка админа
                for other_member in list(i.members.split()):            # оценка других пользователей
                    if other_member != member:
                        get_user(member, other_member, 0)
            for member in list(i.members.split()):
                get_user(i.creator, member, 0)
    except Events.DoesNotExist:
        pass

    try:
        event_to_delete = Events.select().where(Events.status == -1).get()
        event_to_delete.delete_instance()
    except Events.DoesNotExist:
        pass

    time.sleep(60)
