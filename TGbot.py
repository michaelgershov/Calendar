import datetime, telebot, re, threading
from telebot import types
import data_calendar

#######################################################################################################################
bot = telebot.TeleBot("6058933003:AAG5Ti0fmydE9xfQYzPYv35pUM4jPOt7LY0")
#######################################################################################################################

#######################################################################################################################
#  СТАРТОВАЯ РАБОТА БОТА (РЕГИСТРАЦИЯ И ВХОД)
#######################################################################################################################
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


def login(message):
    global NICK
    NICK = message.text
    bot.send_message(message.chat.id, "Теперь введите пароль (не менее 8 символов)")
    bot.register_next_step_handler(message, password)


def password(message):
    global USER
    pas = message.text
    pattern1 = re.compile(r"(?=.*[a-z])(?=.*[A-Z])[a-zA-Z\d]{8,}$")
    if pattern1.fullmatch(pas) is not None:
        bot.send_message(message.chat.id, f"Отличный пароль! Ваша учетная запись: ({NICK}, {'*'*len(pas)})")
        keyboard(message)
        USER = [NICK, pas]
    else:
        msg = bot.send_message(message.chat.id, "Пароль не соответствует стандартам. Введите новый")
        bot.register_next_step_handler(msg, password)
#######################################################################################################################


#######################################################################################################################
# ОСНОВНЫЕ КОМАНДЫ (/option, /settings, /help) И КЛАВИАТУРА ОПЦИЙ
#######################################################################################################################
@bot.message_handler(commands=["option"])
def option(message):
    keyboard(message)


@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(message.from_user.id, 'Список всех доступных команд: ')

#функция клавиатуры опций
def keyboard(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("события")
    button2 = types.KeyboardButton("приоритеты")
    button3 = types.KeyboardButton("статистика")
    button4 = types.KeyboardButton("добавить")
    button5 = types.KeyboardButton("окна")
    button6 = types.KeyboardButton("выход")
    markup.add(button1, button2, button3, button4, button5, button6)
    bot.send_message(message.chat.id, "Выберите опцию из меню", reply_markup=markup)
    bot.register_next_step_handler(message, selection)
#######################################################################################################################


#######################################################################################################################
# ОБРАБОТКА ВЫБОРА ОПЦИИ
#######################################################################################################################
#функция обработки выбора опций
def selection(message):
    sel = message.text
    if sel == "добавить":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("дата и время")
        button2 = types.KeyboardButton("дата")
        button3 = types.KeyboardButton("не зависит")
        markup.add(button1, button2, button3)
        bot.send_message(message.chat.id, "Выберите нужный тип события", reply_markup=markup)
        bot.register_next_step_handler(message, type_of_event)
#######################################################################################################################


#######################################################################################################################
# ОБРАБОТКА ВЫБОРА ТИПА СОБЫТИЯ
#######################################################################################################################
#функция выбора типа события
def type_of_event(message):
    sel = message.text
    if sel == "дата и время":
        depending_from_time(message)
    elif sel == "не зависит":
        category_independent(message)
#######################################################################################################################


#######################################################################################################################
# ОБРАБОТКА СОЗДАНИЯ СОБЫТИЯ, ЗАВИСИМОГО ОТ ДАТЫ И ВРЕМЕНИ
#######################################################################################################################
#функция, выводящая календарь для начала события или конца события
def depending_from_time(message):
    if START_TIME is None:
        bot.send_message(message.chat.id, "Выберите день начала события",
                         reply_markup=data_calendar.create_calendar(None, None, 1))
    else:
        bot.send_message(message.chat.id, "Выберите день конца события",
                         reply_markup=data_calendar.create_calendar(None, None, START_DATE))


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    global RET_DATA, FINISH
    RET_DATA = None
    if call is None:
        bot.answer_callback_query(callback_query_id=call.id)
    elif ";" in str(call.data):
        (action, year, month, day) = data_calendar.separate_callback_data(call.data)
        curr = datetime.datetime(int(year), int(month), 1)

        if action == "День":
            RET_DATA = datetime.datetime(int(year), int(month), int(day))
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            if END_TIME is None:
                bot.send_message(call.message.chat.id, f"Вы выбрали дату {RET_DATA.date()}")
                msg = bot.send_message(call.message.chat.id, "Введите нужное время, разделив часы и минуты знаком ':'", reply_markup=None)
                bot.register_next_step_handler(msg, time_selector)
            else:
                FINISH = RET_DATA
                msg = bot.send_message(call.message.chat.id, f"Вы выбрали дату {FINISH.date()}. Введите количество дней в промежутке между повторами", reply_markup=None)
                bot.register_next_step_handler(msg, day_interval)

        elif action == "Пред-месяц":
            pre = curr - datetime.timedelta(days=1)
            if START_TIME is None:
                new_keyboard = data_calendar.create_calendar(int(pre.year), int(pre.month), 1)
            else:
                new_keyboard = data_calendar.create_calendar(int(pre.year), int(pre.month), START_DATE)
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=new_keyboard)
        elif action == "След-месяц":
            ne = curr + datetime.timedelta(days=31)
            if START_TIME is None:
                bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=data_calendar.create_calendar(int(ne.year), int(ne.month),1))
            else:
                bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=data_calendar.create_calendar(int(ne.year), int(ne.month), START_DATE))
        else:
            bot.send_message(call.message.chat.id, "Выберите корректную дату!")

START_TIME, END_TIME = None, None
#функция обработки всех возможных вариантов установки времени начала и конца события
def time_selector(message):
    global START_TIME, END_TIME, START_DATE, END_DATE
    if START_TIME is None:
        START_TIME = message.text
        pattern = re.compile(r"^\d{1,2}:\d{2}$")
        if pattern.fullmatch(START_TIME) is not None:
            hours, minutes = map(lambda x: int(x), START_TIME.split(":"))
            if (0 <= hours < 24) and (0 <= minutes < 60):
                if ((datetime.time(hours, minutes) > datetime.datetime.now().time() and RET_DATA.date() == datetime.datetime.now().date()) or RET_DATA.date() > datetime.datetime.now().date()):
                    START_DATE = RET_DATA.replace(hour=hours, minute=minutes)
                    bot.send_message(message.chat.id, f"Вы назначили начало события на {START_DATE}")
                    depending_from_time(message)
                else:
                    bot.send_message(message.chat.id, "Нельзя начать событие в прошлом( Повторите попытку")
                    START_TIME = None
                    bot.register_next_step_handler(message, time_selector)
            else:
                bot.send_message(message.chat.id, "Введите корректное время")
                START_TIME = None
                bot.register_next_step_handler(message, time_selector)
        else:
            bot.send_message(message.chat.id, "Введите указанный формат чч:мм")
            START_TIME = None
            bot.register_next_step_handler(message, time_selector)
    elif END_TIME is None:
        END_TIME = message.text
        pattern2 = re.compile(r"\d+:\d+")
        if pattern2.fullmatch(END_TIME) is not None:
            hours, minutes = map(lambda x: int(x), END_TIME.split(":"))
            END_DATE = RET_DATA
            if (0 <= hours < 24) and (0 <= minutes < 60):
                if (END_DATE > START_DATE) or (END_DATE.date() == START_DATE.date() and datetime.time(hours, minutes) > START_DATE.time()):
                    END_DATE = RET_DATA.replace(hour=hours, minute=minutes)
                    bot.send_message(message.chat.id, f"Вы назначили конец события на {END_DATE}")
                    bot.send_message(message.chat.id, "Введите название события")
                    bot.register_next_step_handler(message, time_save_event)
                else:
                    bot.send_message(message.chat.id, f"Вы не можете назначить конец события раньше начала (начало в {START_DATE.time()}). Выберите время заново")
                    END_TIME = None
                    bot.register_next_step_handler(message, time_selector)
            else:
                bot.send_message(message.chat.id, "Введите корректное время")
                END_TIME = None
                bot.register_next_step_handler(message, time_selector)
        else:
            bot.send_message(message.chat.id, "Введите указанный формат чч:мм")
            END_TIME = None
            bot.register_next_step_handler(message, time_selector)
    else:
        bot.send_message(message.chat.id, "Время для данного события уже зафиксировано")


EVENTS = []
#функция фиксирования начала, конца события и самого события
def time_save_event(message):
    global TEXT, EVENT, START_TIME, END_TIME, EVENTS
    TEXT = message.text
    EVENT = [START_DATE, END_DATE, TEXT]
    bot.send_message(message.chat.id, f"Событие '{EVENT[-1]}' установлено с {EVENT[0]} по {EVENT[1]}")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("да")
    button2 = types.KeyboardButton("нет")
    markup.add(button1,button2)
    bot.send_message(message.chat.id, f"Данное событие циклично?", reply_markup=markup)
    bot.register_next_step_handler(message, looping)


#функция обработки введенного промежутка между повторами
def day_interval(message):
    num = message.text
    delta = FINISH - END_DATE
    origin_delta = END_DATE - START_DATE
    if (num.isdigit() and datetime.timedelta(days=int(num)) < origin_delta):
        bot.send_message(message.chat.id, "Ошибка. Длительность события больше промежутка между повторениями. Повторите попытку")
        bot.register_next_step_handler(message, day_interval)
    elif (num.isdigit() and int(num) > 0 and datetime.timedelta(days=int(num)) < delta):
        new_start, new_end = START_DATE, END_DATE
        while new_start < FINISH:
            new_start += datetime.timedelta(days=int(num))
            new_end += datetime.timedelta(days=int(num))
            event = [new_start, new_end, TEXT, True]
            EVENTS.append(event)
        bot.send_message(message.chat.id, f"Все повторы данного события зафиксированы. Всего их получилось {len(EVENTS)-1}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("да")
        button2 = types.KeyboardButton("нет")
        markup.add(button1, button2)
        bot.send_message(message.chat.id, "Осталось немного). Данное событие допускает вложенность?",reply_markup=markup)
        bot.register_next_step_handler(message, embedding)
    else:
        bot.send_message(message.chat.id, "Вы ввели не натуральное число или большее, чем количество дней между концом события и днем последнего повторения. Повторите попытку")
        bot.register_next_step_handler(message, day_interval)


#функция определения цикличности события
def looping(message):
    answer = message.text
    if answer == "да":
        dt = END_DATE + datetime.timedelta(days=1)
        bot.send_message(message.chat.id, "До какого дня нужно повторять событие (включительно)?", reply_markup=data_calendar.create_calendar(None, None, dt))
    elif answer == "нет":
        EVENT.append(None)
        EVENTS.append(EVENT)
        bot.send_message(message.chat.id, "Данное событие допускает вложенность?")
        bot.register_next_step_handler(message, embedding)
    else:
        bot.send_message(message.chat.id, "Выберите или введите да/нет для продолжения")
        bot.register_next_step_handler(message, looping)


#функция определения вложенности события
def embedding(message):
    global START_TIME, END_TIME
    START_TIME, END_TIME = None, None
    answer = message.text
    if answer == "да":
        bot.send_message(message.chat.id, "Принял, тогда введите число уровней вложенности", reply_markup=None)
        bot.register_next_step_handler(message, levels_of_embedding)
    elif answer == "нет":
        if None in EVENT:
            EVENT.append(None)
            EVENTS.append(EVENT)
            bot.send_message(message.chat.id, f"Тогда всё) Событие '{EVENT[2]}' с {EVENT[0]} по {EVENT[1]} успешно создано. (не является циклическим и не имеет вложенности)")
        else:
            EVENT.append(None)
            EVENTS.append(EVENT)
            bot.send_message(message.chat.id,
                             f"Тогда всё) Событие '{EVENT[2]}' с {EVENT[0]} по {EVENT[1]} успешно создано. (является циклическим и не имеет вложенности)")
        bot.send_message(message.chat.id, 'Хотите получить напоминание о данном событии?')
        bot.register_next_step_handler(message, notification)
    else:
        bot.send_message(message.chat.id, "Выберите или введите да/нет для продолжения")
        bot.register_next_step_handler(message, embedding)


#функция, фиксирующая количество уровней вложенности события и собирающая полную инфу про событие
def levels_of_embedding(message):
    num = message.text
    if (num.isdigit() and int(num) > 0):
        bot.send_message(message.chat.id, "Хорошо")
        for i in range(len(EVENTS)):
            if EVENT[2] == EVENTS[i][2]:
                EVENTS[i].append(int(num))
                EVENTS[i] = tuple(EVENTS[i])
            else:
                pass
        if None in EVENTS[0]:
            bot.send_message(message.chat.id,
                             f"Тогда всё) Событие '{EVENT[2]}' с {EVENT[0]} по {EVENT[1]} успешно создано. (не является циклическим и имеет вложенность)")
        else:
            bot.send_message(message.chat.id,
                             f"Тогда всё) Событие '{EVENT[2]}' с {EVENT[0]} по {EVENT[1]} успешно создано. (является циклическим и имеет вложенность)")
        bot.send_message(message.chat.id, 'Хотите получить напоминание о данном событии?')
        bot.register_next_step_handler(message, notification)
    else:
        bot.send_message(message.chat.id, "Вы ввели некорректное значение. Повторите попытку")
        bot.register_next_step_handler(message, levels_of_embedding)


#функция, для установки даты и времени напоминания
def datetime_reminder(message):
    bot.send_message(message.chat.id, "Введите дату и время, когда вы хотите получить напоминание, в формате ГГГГ-ММ-ДД чч:мм.")
    bot.register_next_step_handler(message, get_reminder)


#функция обработки введенного времени для напоминания
def get_reminder(message):
    try:
        reminder_time = datetime.datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        #если дата напоминания позже начала события
        if START_DATE < reminder_time:
            bot.send_message(message.chat.id, "Дата напоминания установлена позже начала события. Повторите попытку")
            datetime_reminder(message)
        #если дата напоминания раньше сегодняшней
        elif reminder_time < datetime.datetime.now():
            bot.send_message(message.chat.id, "Проверьте правильность ввода!")
            datetime_reminder(message)
        else:
            bot.send_message(message.chat.id, "Напоминание '{}' установлено на {}.".format(TEXT, reminder_time))
            today = datetime.datetime.now()
            date = reminder_time - today
            seconds = date.total_seconds()
            reminder_timer = threading.Timer(seconds, send_reminder, [message.chat.id, TEXT])
            reminder_timer.start()
            keyboard(message)
    except:
        bot.send_message(message.chat.id, "Вы ввели неверный формат даты и времени, попробуйте еще раз.")
        datetime_reminder(message)


#функция, которая отправляет напоминание пользователю
def send_reminder(chat_id, reminder_name):
    bot.send_message(chat_id, "Напоминание о событии '{}'!".format(TEXT))


#функция определения потребности напоминания
def notification(message):
    if message.text.lower() == "нет":
        bot.send_message(message.chat.id, "Напоминание не будет установлено")
        keyboard(message)
    elif message.text.lower() == "да":
        datetime_reminder(message)
    else:
        bot.send_message(message.chat.id, "Напишите ответ в виде 'Да' или 'Нет'!")
        bot.register_next_step_handler(message, notification)
#######################################################################################################################


#######################################################################################################################
# ОБРАБОТКА СОЗДАНИЯ СОБЫТИЯ, НЕЗАВИСИМОГО ОТ ВРЕМЕНИ
#######################################################################################################################
#функция определения категории события
def category_independent(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Срочные важные")
    button2 = types.KeyboardButton("Несрочные важные")
    button3 = types.KeyboardButton("Срочные неважные")
    button4 = types.KeyboardButton("Несрочные неважные")
    markup.add(button1, button2, button3, button4)
    bot.send_message(message.chat.id, "Выберите категорию события", reply_markup=markup)
    bot.register_next_step_handler(message, name_independent)


#функция наименования события
def name_independent(message):
    global CATEGORY
    CATEGORY = message.text
    bot.send_message(message.chat.id, "Введите название события")
    bot.register_next_step_handler(message, exit_independent)


#результирующая функция
def exit_independent(message):
    name = message.text
    event = (name, CATEGORY)
    EVENTS.append(event)
    bot.send_message(message.chat.id, "Событие '{}' успешно добавлено в категорию '{}'!".format(name, CATEGORY))
    keyboard(message)
#######################################################################################################################


#######################################################################################################################
# МЕНЮ
#######################################################################################################################
bot.set_my_commands([
    telebot.types.BotCommand("/start", "Перезапуск бота"),
    telebot.types.BotCommand("/help", "Помощь"),
    telebot.types.BotCommand("/option", 'Доступные опции'),
    telebot.types.BotCommand("/settings", "Изменить логин или пароль")
])
#######################################################################################################################


bot.infinity_polling()
