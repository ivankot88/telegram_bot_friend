import peewee
from pyowm import OWM
import datetime
from telebot.types import ReplyKeyboardMarkup

database = peewee.SqliteDatabase("database.db")

"""

Классы, отвечающие за поля в таблицах

"""


class Users(peewee.Model):
    id = peewee.IntegerField()
    telephone = peewee.CharField()
    hobbies = peewee.CharField()
    first_name = peewee.CharField()
    second_name = peewee.CharField()
    reputation = peewee.IntegerField()
    latitude = peewee.FloatField()
    longitude = peewee.FloatField()
    weather = peewee.IntegerField()
    weather_time = peewee.TimeField()
    fun = peewee.CharField()

    class Meta:
        database = database


class Reminder(peewee.Model):
    id = peewee.IntegerField()
    time = peewee.TimeField()
    text = peewee.CharField()
    date = peewee.DateTimeField()

    class Meta:
        database = database


class Events(peewee.Model):
    id = peewee.IntegerField()
    date = peewee.DateField()
    time = peewee.TimeField()
    text = peewee.CharField()
    count = peewee.IntegerField()
    fun = peewee.CharField()
    creator = peewee.IntegerField()
    members = peewee.CharField()
    status = peewee.IntegerField()
    address = peewee.CharField()

    class Meta:
        database = database


class Emoji:
    """

    Класс Emoji создан для наглядного отображения символов,
    которые меняются взависимости от погодных условий

    """
    def __init__(self):
        self.pictures = {
            'смех': '😂',
            'палец': '👍',
            'солнце': '☀',
            'подмигивание': '😉',
            'туча1': '🌤',
            'туча2': '⛅',
            'туча3': '🌥',
            'дождь1': '🌦',
            'туча5': '☁',
            'дождь2': '🌧',
            'гроза1': '⛈',
            'гроза2': '🌩',
            'снег': '🌨',
            'грусть': '😞',
            'улыбка': '😀',
            'улыбка1': '😊',
            'пальто': '🧥',
            'перчатки': '🧤',
            'зонт': '☂'
        }

    def weather(self, text):
        if text == 'Clouds':
            return '☁'
        elif text == 'Clear':
            return '☀'
        elif text == 'Snow':
            return '🌨'
        elif text == 'Thunderstorm':
            return '⛈'
        elif text == 'Drizzle':
            return '🌨'
        elif text == 'Rain':
            return '🌧'
        else:
            return ''


class Words:
    def __init__(self):
        file = open('welcome_words.txt')
        file1 = open('farewell_words.txt')
        self.welcome = file.readlines()
        self.leave = file1.readlines()


class Bot_settings:
    """

    Класс для хранилища временных данных

    """
    def __init__(self):
        self.action = dict()
        for i in Users.select():                     # инициализация action для всех сохранённых пользователей в DB
            self.action[i.id] = 'answer'
        self.file = open('event_categories.txt')
        self.lines = self.file.readlines()
        self.current_shown_dates = {}
        self.date = datetime.date(1, 1, 1)
        self.words = Words()
        self.emoji = Emoji()
        self.time = ''
        self.owm = OWM('ed0a22544e011704dca2f50f3399864f', language="ru")
        self.keyboard = ReplyKeyboardMarkup()

    def weather_text(self, latitude, longitude):
        """

        Функция получает погоду через API и формирует текст для отправки сообщения

        """
        obs = self.owm.weather_at_coords(latitude, longitude)
        w = obs.get_weather()
        wind = w.get_wind()
        temp = w.get_temperature(unit='celsius')
        text = '☂⛅\nСегодня {} {} \nТемпература воздуха: {}°C\nВетер будет достигать {} м/с\n'.format(
            w.get_detailed_status(),
            self.emoji.weather(
                w.get_status()),
            round(temp['temp']),
            round(wind['speed']))
        if w.get_status() == 'Rain' and round(temp['temp']) < 0:
            text += "Рекомендую тебе взять зонтик и одеться по теплее {}{}{}".format(self.emoji.pictures['зонт'],
                                                                                     self.emoji.pictures['пальто'],
                                                                                     self.emoji.pictures['перчатки'])
        elif w.get_status() == 'Rain':
            text += "Рекомендую тебе взять зонтик {}".format(self.emoji.pictures['зонт'])
        elif round(temp['temp']) < 0:
            text += "Рекомендую тебе одеться по теплее {}{}".format(self.emoji.pictures['пальто'],
                                                                    self.emoji.pictures['перчатки'])
        return text
