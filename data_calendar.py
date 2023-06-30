from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import datetime
import calendar


def create_callback_data(action, year, month, day):
    return ";".join([action, str(year), str(month), str(day)])


def separate_callback_data(data):
    return data.split(";")


def create_calendar(year=None, month=None, time=1):
    if time == 1:
        now = datetime.datetime.now()
    else:
        now = time
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    data_ignore = create_callback_data("Ничего", year, month, 0)
    keyboard = []
    row = []
    row.append(InlineKeyboardButton(calendar.month_name[month]+" "+str(year), callback_data=data_ignore))
    keyboard.append(row)
    row=[]
    for day in ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]:
        row.append(InlineKeyboardButton(day, callback_data=data_ignore))
    keyboard.append(row)
    my_calendar = calendar.monthcalendar(year, month)
    for week in my_calendar:
        row=[]
        for day in week:
            if ((day == 0) or ((day > 0 and day < now.day) and (month == now.month) and (year == now.year))):
                row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
            else:
                row.append(InlineKeyboardButton(str(day), callback_data=create_callback_data("День", year, month, day)))
        keyboard.append(row)
    row=[]
    if month == now.month:
        row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
        row.append(InlineKeyboardButton(">", callback_data=create_callback_data("След-месяц", year, month, day)))
        keyboard.append(row)
    else:
        row.append(InlineKeyboardButton("<", callback_data=create_callback_data("Пред-месяц", year, month, day)))
        row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
        row.append(InlineKeyboardButton(">", callback_data=create_callback_data("След-месяц", year, month, day)))
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)
