from telebot import types
import calendar
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_calendar(year,month):
    markup = types.InlineKeyboardMarkup()
    #First row - Month and Year
    row=[]
    row.append(types.InlineKeyboardButton(calendar.month_name[month]+" "+str(year),callback_data="ignore"))
    markup.row(*row)
    #Second row - Week Days
    week_days=["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]
    row=[]
    for day in week_days:
        row.append(types.InlineKeyboardButton(day,callback_data="ignore"))
    markup.row(*row)

    my_calendar = calendar.monthcalendar(year, month)
    for week in my_calendar:
        row=[]
        for day in week:
            if(day==0):
                row.append(types.InlineKeyboardButton(" ",callback_data="ignore"))
            else:
                row.append(types.InlineKeyboardButton(str(day),callback_data="calendar-day-"+str(day)))
        markup.row(*row)
    #Last row - Buttons
    row=[]
    row.append(types.InlineKeyboardButton("<",callback_data="previous-month"))
    row.append(types.InlineKeyboardButton(" ",callback_data="ignore"))
    row.append(types.InlineKeyboardButton(">",callback_data="next-month"))
    markup.row(*row)
    return markup


def number_keyboard():
    markup = InlineKeyboardMarkup()
    numbers = ["7", "8", "9", "4", "5", "6", "1", "2", "3"]
    row = []
    for number in numbers:
        row.append(InlineKeyboardButton(number, callback_data="number_" + number))
        if len(row) == 3:
            markup.row(*row)
            row = []
    row = []
    row.append(InlineKeyboardButton("<-", callback_data="number_back"))
    row.append(InlineKeyboardButton("0", callback_data="number_0"))
    row.append(InlineKeyboardButton("OK", callback_data="number_done"))
    markup.row(*row)
    return markup