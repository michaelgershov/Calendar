import datetime, telebot, re
from telebot import types
import data_calendar


bot = telebot.TeleBot("6227807125:AAFXklXnWe5UZ4k54Lu_BqcrM1vNMTcph48")


@bot.message_handler(commands=["start"])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Войти")
    button2 = types.KeyboardButton("Зарегистрироваться")
    markup.add(button1, button2)
    bot.send_message(message.chat.id, "Здравствуйте. Я ваш персональный бот-календарь. Выберите действие для начала работы", reply_markup=markup)
    bot.register_next_step_handler(message, answering)


def answering(message):
    text = message.text
    if text == "Войти":
        bot.send_message(message.chat.id, "Введите свой ник пользователя", reply_markup=None)
        bot.register_next_step_handler(message, login)
    elif text == "Зарегистрироваться":
        bot.send_message(message.chat.id, "Введите логин")
        bot.register_next_step_handler(message, login)


#@bot.message_handler(commands=["signIn"])
#def signIn_message(message):
#    bot.send_message(message.chat.id, "Введите свой ник пользователя", reply_markup=None)
#    bot.register_next_step_handler(message, login)


#@bot.message_handler(commands=["signUp"])
#def signUp_message(message):
#    bot.send_message(message.chat.id, "Введите логин")
#    bot.register_next_step_handler(message, login)


def login(message):
    global nick
    nick = message.text
    bot.send_message(message.chat.id, "Теперь введите пароль (не менее 8 символов)")
    bot.register_next_step_handler(message, password)


def password(message):
    global user
    pas = message.text
    pattern1 = re.compile(r"(?=.*[a-z])(?=.*[A-Z])[a-zA-Z\d]{8,}$")
    if pattern1.fullmatch(pas) is not None:
        bot.send_message(message.chat.id, f"Отличный пароль! Ваша учетная запись: ({nick}, {'*'*len(pas)})",reply_markup=keyboard(message))
        user = [nick, pas]
    else:
        msg = bot.send_message(message.chat.id, "Пароль не соответствует стандартам. Введите новый")
        bot.register_next_step_handler(msg, password)


@bot.message_handler(commands=["option"])
def option(message):
    bot.register_next_step_handler(message, keyboard)


@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(message.from_user.id, 'Список всех доступных команд: ')


def keyboard(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("/times_events")
    button2 = types.KeyboardButton("/priority")
    button3 = types.KeyboardButton("/statistic")
    button4 = types.KeyboardButton("/add_event")
    button5 = types.KeyboardButton("/free_time")
    button6 = types.KeyboardButton("/exit")
    markup.add(button1, button2, button3, button4, button5, button6)
    bot.send_message(message.chat.id, "Выберите опцию из меню", reply_markup=markup)


@bot.message_handler(commands=["add_event"])
def send_event(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("/dp_from_time")
    button2 = types.KeyboardButton("/dp_from_date")
    button3 = types.KeyboardButton("/dp_from_none")
    markup.add(button1,button2,button3)
    bot.send_message(message.chat.id, "Выберите нужный тип события", reply_markup=markup)


@bot.message_handler(commands=["dp_from_time"])
def set_event(message):

    if start_time is None:
        bot.send_message(message.chat.id, "Выберите день начала события", reply_markup=data_calendar.create_calendar(None,None,1))
    else:
        bot.send_message(message.chat.id, "Выберите день конца события", reply_markup=data_calendar.create_calendar(None,None, start_date))


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    global ret_data
    ret_data = None
    if call == None:
        bot.answer_callback_query(callback_query_id=call.id)
    elif ";" in str(call.data):
        (action, year, month, day) = data_calendar.separate_callback_data(call.data)
        curr = datetime.datetime(int(year), int(month), 1)

        if action == "День":
            ret_data = datetime.datetime(int(year), int(month), int(day))
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.send_message(call.message.chat.id, f"Вы выбрали дату {ret_data.date()}")
            msg = bot.send_message(call.message.chat.id, "Введите нужное время, разделив часы и минуты знаком ':'")
            bot.register_next_step_handler(msg, time_selector)
        elif action == "Пред-месяц":
            pre = curr - datetime.timedelta(days=1)
            if start_time is None:
                new_keyboard = data_calendar.create_calendar(int(pre.year), int(pre.month), 1)
            else:
                new_keyboard = data_calendar.create_calendar(int(pre.year), int(pre.month), start_date)
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=new_keyboard)
        elif action == "След-месяц":
            ne = curr + datetime.timedelta(days=31)
            if start_time is None:
                bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=data_calendar.create_calendar(int(ne.year), int(ne.month),1))
            else:
                bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=data_calendar.create_calendar(int(ne.year), int(ne.month), start_date))
        else:
            bot.send_message(call.message.chat.id, "Что-то не так!")


start_time = None
end_time = None
def time_selector(message):
    global start_time, end_time, start_date, end_date
    if start_time == None:
        start_time = message.text
        pattern2 = re.compile(r"\d+:\d+")
        if pattern2.fullmatch(start_time) is not None:
            hours, minutes = map(lambda x: int(x), start_time.split(":"))
            if (0 <= hours < 24) and (0 <= minutes < 60):
                start_date = ret_data.replace(hour=hours, minute=minutes)
                bot.send_message(message.chat.id, f"Вы назначили начало события на {start_date}")
                bot.send_message(message.chat.id, "Нажмите /dp_from_time или введите данную команду для продолжения")
            else:
                bot.send_message(message.chat.id, "Введите корректное время")
                start_time = None
                bot.register_next_step_handler(message, time_selector)
        else:
            bot.send_message(message.chat.id, "Введите указанный формат чч:мм")
            start_time = None
            bot.register_next_step_handler(message, time_selector)
    elif end_time == None:
        end_time = message.text
        pattern2 = re.compile(r"\d+:\d+")
        if pattern2.fullmatch(end_time) is not None:
            hours, minutes = map(lambda x: int(x), end_time.split(":"))
            end_date = ret_data
            if (0 <= hours < 24) and (0 <= minutes < 60):
                if (end_date > start_date) or (end_date.date() == start_date.date() and datetime.time(hours, minutes) > start_date.time()):
                    end_date = ret_data.replace(hour=hours, minute=minutes)
                    bot.send_message(message.chat.id, f"Вы назначили конец события на {end_date}")
                    bot.send_message(message.chat.id, "Введите название события")
                    bot.register_next_step_handler(message, save_event)
                else:
                    bot.send_message(message.chat.id, f"Вы не можете назначить конец события раньше начала (начало в {start_date.time()}). Выберите время заново")
                    end_time = None
                    bot.register_next_step_handler(message, time_selector)
            else:
                bot.send_message(message.chat.id, "Введите корректное время")
                end_time = None
                bot.register_next_step_handler(message, time_selector)
        else:
            bot.send_message(message.chat.id, "Введите указанный формат чч:мм")
            end_time = None
            bot.register_next_step_handler(message, time_selector)
    else:
        bot.send_message(message.chat.id, "Время для данного события уже зафиксировано")


events = []
def save_event(message):
    global text, event, start_time, end_time, events
    text = message.text
    event = [start_date, end_date, text]
    events.append(event)
    bot.send_message(message.chat.id, f"Событие '{event[-1]}' установлено с {event[0]} по {event[1]}")
    start_time, end_time = None, None
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("да")
    button2 = types.KeyboardButton("нет")
    markup.add(button1,button2)
    bot.send_message(message.chat.id, f"Данное событие циклично?", reply_markup=markup)
    bot.register_next_step_handler(message, looping)


def looping(message):
    answer = message.text
    if answer == "да":
        bot.send_message(message.chat.id, "ok")
    elif answer == "нет":
        bot.send_message(message.chat.id, "Данное событие допускает вложенность?")
        bot.register_next_step_handler(message, embedding)



def embedding(message):
    bot.send_message(message.chat.id, "ok")


bot.set_my_commands([
    telebot.types.BotCommand("/start", "Перезапуск бота"),
    telebot.types.BotCommand("/help", "Помощь"),
    telebot.types.BotCommand("/option", 'Доступные опции'),
    telebot.types.BotCommand("/settings", "Изменить логин или пароль")
])


bot.infinity_polling()