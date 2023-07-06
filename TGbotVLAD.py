import datetime, telebot, re, threading, hashlib
from telebot import types
import data_calendar, calendar_image
import mysqlconnector as db
import multiprocessing

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

multiprocessing.freeze_support()

bot = telebot.TeleBot("6227807125:AAFXklXnWe5UZ4k54Lu_BqcrM1vNMTcph48")
connection = db.create_connection("127.0.0.1", "root", "wkiSyrOIh6)v", "Calendar")


#######################################################################################################################
#  СТАРТОВАЯ РАБОТА БОТА (РЕГИСТРАЦИЯ И ВХОД)
#######################################################################################################################
@bot.message_handler(commands=["start"])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Войти")
    button2 = types.KeyboardButton("Зарегистрироваться")
    markup.add(button1, button2)
    bot.send_message(message.chat.id,
                     "Здравствуйте! Я ваш персональный бот-календарь. Выберите действие для начала работы.",
                     reply_markup=markup)
    bot.register_next_step_handler(message, answering)


def answering(message):
    global LOGIN
    text = message.text
    if text.lower() == "войти":
        bot.send_message(message.chat.id, "Введите имя пользователя (после знака '@').", reply_markup=None)
        bot.register_next_step_handler(message, login)
    elif text.lower() == "зарегистрироваться":
        
        login_user = message.from_user.username
        check_login = f"""
        SELECT 
        EXISTS (SELECT 
        Login FROM users WHERE Login='{login_user}' LIMIT 1)
        """ 
        if db.execute_read_query(connection, check_login)[0][0] == 1:
            LOGIN = login_user
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("Продолжить")
            button2 = types.KeyboardButton("Создать новую учётную запись")
            markup.add(button1, button2)
            bot.send_message(message.chat.id,
                f"Учётная запись для пользователя {LOGIN} уже существует. Желаете продолжить с этой учётной записью или создать новую?", reply_markup=markup)
            bot.register_next_step_handler(message, user_answer)
        else:
            LOGIN = message.from_user.username
            bot.send_message(message.chat.id, "Введите пароль (не менее 8 символов).", reply_markup=None)
            bot.register_next_step_handler(message, password)
    # заглушка для перезагрузки бота
    elif text == "/start" or text == "/back":
        start_message(message)
    elif text == "/help":
        help_bot(message)
    else:
        bot.send_message(message.chat.id, "Проверьте корректность введённой команды или используйте кнопки.")
        bot.register_next_step_handler(message, answering)


def user_answer(message):
    ans = message.text.lower()
    if ans == "продолжить":
        bot.send_message(message.chat.id, "Введите пароль.")
        bot.register_next_step_handler(message, password_check)
    elif ans == "создать новую учётную запись":
        bot.send_message(message.chat.id, "Введите имя пользователя (после знака '@').", reply_markup=None)
        bot.register_next_step_handler(message, create_login)   
    elif ans == "/start" or ans == "/back":
        start_message(message)
    elif ans == "/help":
        help_bot(message)
    else:
        bot.send_message(message.chat.id, "Проверьте корректность введённой команды или используйте кнопки.")
        bot.register_next_step_handler(message, user_answer)

def create_login(message):
    global LOGIN
    LOGIN = message.text.lower()
    check_login = f"""
    SELECT 
    EXISTS (SELECT 
    Login FROM users WHERE Login='{LOGIN}' LIMIT 1)
    """
    if db.execute_read_query(connection, check_login)[0][0] != 1:
        bot.send_message(message.chat.id, "Введите пароль (не менее 8 символов).", reply_markup=None)
        bot.register_next_step_handler(message, password)
    # заглушка для перезагрузки бота
    elif message.text == "/start" or message.text == "/back":
        start_message(message)
    elif message.text == "/help":
        help_bot(message)
    else:
        msg = bot.send_message(message.chat.id, "Пользователь с таким именем уже существует. Попробуйте снова.")
        bot.register_next_step_handler(msg, login)


def login(message):
    global LOGIN
    LOGIN = message.text
    check_login = f"""
    SELECT 
    EXISTS (SELECT 
    Login FROM users WHERE Login='{LOGIN}' LIMIT 1)
    """
    if db.execute_read_query(connection, check_login)[0][0] == 1:
        bot.send_message(message.chat.id, "Введите пароль.")
        bot.register_next_step_handler(message, password_check)
    # заглушка для перезагрузки бота
    elif message.text == "/start" or message.text == "/back":
        start_message(message)
    elif message.text == "/help":
        help_bot(message)
    else:
        msg = bot.send_message(message.chat.id, "Пользователя не существует. Попробуйте снова.")
        bot.register_next_step_handler(msg, login)


def password_check(message):
    pas = message.text
    hash_object = hashlib.sha256(pas.encode())
    hex_dig = hash_object.hexdigest()
    get_pas = f"""
    SELECT 
    Password FROM users WHERE Login='{LOGIN}' LIMIT 1
    """
    if db.execute_read_query(connection, get_pas)[0][0] == hex_dig:
        bot.send_message(message.chat.id, f"Вход выполнен!")
        keyboard(message)
    # заглушка для перезагрузки бота
    elif message.text == "/start" or message.text == "/back":
        start_message(message)
    elif message.text == "/help":
        help_bot(message)
    else:
        msg = bot.send_message(message.chat.id, "Неверный пароль. Попробуйте снова.")
        bot.register_next_step_handler(msg, password_check)


def password(message):
    global LOGIN
    pas = message.text
    pattern1 = re.compile(r"(?=.*[a-z])(?=.*[A-Z])[a-zA-Z\d]{8,}$")
    if pattern1.fullmatch(pas) is not None:
        hash_object = hashlib.sha256(pas.encode())
        hex_dig = hash_object.hexdigest()
        create_user = f"""
        INSERT INTO
          users (login, password)
        VALUES
          ('{LOGIN}', '{hex_dig}')
        """
        db.execute_query(connection, create_user)
        bot.send_message(message.chat.id, f"Отличный пароль!\nУчётная запись для {LOGIN} создана.")
        keyboard(message)
        # заглушка для перезагрузки бота
    elif message.text == "/start" or message.text == "/back":
        start_message(message)
    elif message.text == "/help":
        help_bot(message)
    else:
        msg = bot.send_message(message.chat.id,
                               "Введённый пароль не соответствует стандартам. Введите пароль повторно.")
        bot.register_next_step_handler(msg, password)


#######################################################################################################################


#######################################################################################################################
# ОСНОВНЫЕ КОМАНДЫ (/option, /settings, /help) И КЛАВИАТУРА ОПЦИЙ
#######################################################################################################################
@bot.message_handler(commands=["option"])
def option(message):
    keyboard(message)


@bot.message_handler(commands=["help"])
def help_bot(message):
    bot.send_message(message.from_user.id, 'Список всех доступных команд: ')


def keyboard(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Мои события")
    button2 = types.KeyboardButton("Редактировать событие")
    button3 = types.KeyboardButton("Статистика")
    button4 = types.KeyboardButton("Добавить событие")
    button5 = types.KeyboardButton("Свободные окна")
    button6 = types.KeyboardButton("Выход")
    markup.add(button1, button2, button3, button4, button5, button6)
    bot.send_message(message.chat.id, "Выберите опцию из меню.", reply_markup=markup)
    bot.register_next_step_handler(message, selection)


#######################################################################################################################


#######################################################################################################################
# ОБРАБОТКА ВЫБОРА ОПЦИИ
#######################################################################################################################
# функция обработки выбора опций
def selection(message):
    global ID_USER
    get_id = f"""
    SELECT 
    id FROM users WHERE Login='{LOGIN}' LIMIT 1
    """
    ID_USER = db.execute_read_query(connection, get_id)[0][0]

    sel = message.text
    if sel.lower() == "мои события":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("На сегодня")
        button2 = types.KeyboardButton("На выбранный день")
        button3 = types.KeyboardButton("Независимые")
        markup.add(button1, button2, button3)
        bot.send_message(message.chat.id, "События какого типа вы желаете увидеть?", reply_markup=markup)
        bot.register_next_step_handler(message, my_events)

    elif sel.lower() == "редактировать событие":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Фиксированное")
        button3 = types.KeyboardButton("Независимое")
        markup.add(button1, button3)
        bot.send_message(message.chat.id, "Выберите нужный тип события", reply_markup=markup)
        bot.register_next_step_handler(message, edit_events)

    elif sel.lower() == "статистика":
        statistics(message)

    elif sel.lower() == "добавить событие":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Дата и время")
        button2 = types.KeyboardButton("Только дата")
        button3 = types.KeyboardButton("Независимое")
        markup.add(button1, button2, button3)
        bot.send_message(message.chat.id,
                         "Выберите нужный тип события. (Ответьте на вопрос: от чего зависит добавляемое Вами событие?)",
                         reply_markup=markup)
        bot.register_next_step_handler(message, type_of_event)

    elif sel.lower() == "свободные окна":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("На день")
        button2 = types.KeyboardButton("На месяц")
        markup.add(button1, button2)
        bot.send_message(message.chat.id, "Выберите интересующий вас отрезок времени.", reply_markup=markup)
        bot.register_next_step_handler(message, free_windows)

    elif sel.lower() == "выход":
        bot.send_message(message.chat.id, f"Вы вышли из учётной записи.")
        start_message(message)

    # заглушка для перезагрузки бота
    elif message.text == "/start":
        start_message(message)
    elif message.text == "/help":
        help_bot(message)
    else:
        msg = bot.send_message(message.chat.id, "Проверьте корректность введённой команды или используйте кнопки.")
        bot.register_next_step_handler(msg, selection)


#######################################################################################################################


#######################################################################################################################
# ОБРАБОТКА ВЫБОРА ТИПА СОБЫТИЯ
#######################################################################################################################

MARK_1, MARK_3 = None, None


# функция выбора типа события
def type_of_event(message):
    global MARK_1, DATE_EVENT, MARK_3
    sel = message.text
    if sel.lower() == "дата и время":
        MARK_1 = None
        MARK_3 = None
        depending_from_time(message)
    elif sel.lower() == "только дата":
        MARK_1 = 1
        DATE_EVENT = None  # хранит дату события, зависимого только от даты
        depending_from_date(message)
    elif sel.lower() == "независимое":
        category_independent(message)
    # заглушка для перезагрузки бота
    elif message.text == "/start":
        start_message(message)
    elif message.text == "/help":
        help_bot(message)
    # для отката на одно действие назад
    elif message.text == "/back":
        keyboard(message)
    else:
        msg = bot.send_message(message.chat.id, "Проверьте корректность введённой команды или используйте кнопки.")
        bot.register_next_step_handler(msg, type_of_event)


#######################################################################################################################


#######################################################################################################################
# ОБРАБОТКА ВЫВОДА СОБЫТИЙ ПОЛЬЗОВАТЕЛЯ
#######################################################################################################################
def req(now, message):
    global ID_USER
    now = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = now.replace(hour=23, minute=59, second=59, microsecond=0)
    get_today_events_1 = f"""
    SELECT DependTime, Event
    FROM plans
    WHERE (idUser={ID_USER})
    AND (DateEvent BETWEEN '{now}' AND '{tomorrow}')
    """
    today_events_1 = db.execute_read_query(connection, get_today_events_1)
    events = {1: "Срочные важные:\n", 2: "Несрочные важные:\n", 3: "Срочные неважные:\n", 4: "Несрочные неважные:\n", 5: "\n"}
    for event in today_events_1:
        if event[0] == "срочное важное":
            events[1] += (event[1] + "\n ")
        elif event[0] == "несрочное важное":
            events[2] += (event[1] + "\n ")
        elif event[0] == "срочное неважное":
            events[3] += (event[1] + "\n ")
        elif event[0] == "несрочное неважное":
            events[4] += (event[1] + "\n ")

    get_today_events_2 = f"""
    SELECT BeginTime, EndTime, Event
    FROM 
        plans
    WHERE 
        (idUser={ID_USER})
    AND 
        ((BeginTime BETWEEN '{now}' AND '{tomorrow}')
    OR
        (EndTime BETWEEN '{now}' AND '{tomorrow}')
    OR
        (BeginTime<'{now}' AND EndTime>'{tomorrow}'))
    """
    today_events_2 = db.execute_read_query(connection, get_today_events_2)
    try:
        today_events_20 = sorted(today_events_2, key=lambda i: i[0])
        for event in today_events_20:
            events[5] += (event[0].strftime('%d.%m %H:%M') + "-" + event[1].strftime('%d.%m %H:%M') + " - " + event[2] + "\n")
    except Exception:
        ...
    n = 0
    for i in range(1,6):
        if events[i] == "Срочные важные:\n" or events[i] == "Несрочные важные:\n" or events[i] == "Срочные неважные:\n" or events[i] == "Несрочные неважные:\n" or events[i] == "\n":
             events[i] = ""
             n += 1
    if n == 5:
        msg = bot.send_message(message.chat.id, "Нет событий на выбранную дату.")
    else:
        msg = bot.send_message(message.chat.id,
            f"Мои события на {now.strftime('%d.%m.%Y')}:\n\n{events[1]}{events[2]}{events[3]}{events[4]}{events[5]}")
    keyboard(msg)

CLICK = None
def my_events(message):
    global MARK_1, DATE_EVENT, RET_DATA, CLICK
    sel = message.text
    if sel.lower() == "на сегодня":
        now = datetime.datetime.now()
        now = now.replace(hour=0, minute=0, second=0, microsecond=0)
        req(now, message)
    elif sel.lower() == "на выбранный день":
        MARK_1 = 2
        DATE_EVENT = None
        depending_from_date(message)           
    elif sel.lower() == "независимые":
        get_indep_events = f"""
        SELECT DependTime, Event
        FROM plans
        WHERE (idUser={ID_USER})
        AND (DateEvent IS NULL)
        AND (BeginTime IS NULL)
        """
        indep_events = db.execute_read_query(connection, get_indep_events)
        events = {1: "Срочные важные:\n", 2: "Несрочные важные:\n", 3: "Срочные неважные:\n", 4: "Несрочные неважные:\n"}
        for event in indep_events:
            if event[0] == "срочное важное":
                events[1] += (event[1] + "\n ")
            elif event[0] == "несрочное важное":
                events[2] += (event[1] + "\n ")
            elif event[0] == "срочное неважное":
                events[3] += (event[1] + "\n ")
            elif event[0] == "несрочное неважное":
                events[4] += (event[1] + "\n ")
        n = 0
        for i in range(1,5):
            if events[i] == "Срочные важные:\n" or events[i] == "Несрочные важные:\n" or events[i] == "Срочные неважные:\n" or events[i] == "Несрочные неважные:\n":
                events[i] = ""
                n += 1
        if n == 4:
            bot.send_message(message.chat.id, "Нет событий.")
        else:
            bot.send_message(message.chat.id,
                f"Мои независимые события:\n\n{events[1]}{events[2]}{events[3]}{events[4]}")
    # заглушка для перезагрузки бота
    elif message.text == "/start":
        start_message(message)
    elif message.text == "/help":
        help_bot(message)
    # для отката на одно действие назад
    elif message.text == "/back":
        keyboard(message)
    else:
        msg = bot.send_message(message.chat.id, "Проверьте корректность введённой команды или используйте кнопки.")
        bot.register_next_step_handler(msg, my_events)

#######################################################################################################################


#######################################################################################################################
# ВЫВОД СТАТИСТИКИ ЗА НЕДЕЛЮ
#######################################################################################################################
def photo(y, monday, now, send_str, message):
    if len(y) != 0:
        x = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][:len(y)]
        plt.bar(x, y)
        plt.xlabel('День недели')
        plt.ylabel('Количество поставленных задач')
        plt.title(f"{monday.strftime('%d.%m.%Y %H:%M')} - {now.strftime('%d.%m.%Y %H:%M')}")
        plt.savefig('saved_figure.jpg')
        bot.send_photo(message.chat.id, photo=open('saved_figure.jpg', 'rb'), caption=send_str)
    else:
        bot.send_message(message.chat.id, send_str)

def from_two_to_one(event1, event2):
    if event1[0] == event2[0] and event1[1] <= event2[1]:
        return event2
    elif event1[0] == event2[0] and event1[1] > event2[1]:
        return event1
    elif event1[1] < event2[0]:
        return None
    elif event1[0] < event2[0] and event1[1] >= event2[0] and event1[1] < event2[1]:
        return (event1[0],event2[1])
    elif event1[0] < event2[0] and event1[1] >= event2[1]:
        return event1

def modifed_events(events_in: list) -> list:
    events = events_in.copy()
    intermed_list = list()
    answers = list()
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            answer = from_two_to_one(events[i], events[j])
            if answer is None:
                pass
            else:
                if answer not in answers:
                    answers.append(answer)
                if events[i] not in intermed_list:
                    intermed_list.append(events[i])
                if events[j] not in intermed_list:
                    intermed_list.append(events[j])
    for event in intermed_list:
        if event in events:
            events.remove(event)
    for answer in answers:
        events.append(answer)
    events.sort(key=lambda x: x[0])
    return events

def statistics(message):
    global ID_USER
    now = datetime.datetime.now()
    monday = now - datetime.timedelta(days=now.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    y = [0,0,0,0,0,0,0][:now.isoweekday()]
    depend_ints = {"Срочные важные":0, "Несрочные важные":0, "Срочные неважные":0, "Несрочные неважные":0}

    #дата и время
    plans_time = f"""
        SELECT
            BeginTime,EndTime
        FROM
            plans
        WHERE
            (idUser={ID_USER})
        AND
            ((BeginTime BETWEEN '{monday}' AND '{now}')
        OR
            (EndTime BETWEEN '{monday}' AND '{now}')
        OR
            (BeginTime<'{monday}' AND EndTime>'{now}'))
        """
    stat_time = db.execute_read_query(connection, plans_time)
    total = now-now
    for s in stat_time:
        if s[0] >= monday and s[1] <= now:
            for i in range(s[1].toordinal()-s[0].toordinal()+1):
                y[s[0].weekday()+i] += 1
        elif s[0] < monday and s[1] > now:
            for i in range(now.toordinal()-monday.toordinal()+1):
                y[i] += 1
        elif s[0] >= monday:
            for i in range(now.toordinal()-s[0].toordinal()+1):
                y[s[0].weekday()+i] += 1
        elif s[1] <= now:
            for i in range(s[1].toordinal()-monday.toordinal()+1):
                y[i] += 1

    events = sorted(stat_time, key=lambda i: i[0])
    while True:
        mod_events = modifed_events(events)
        if set(map(tuple, mod_events)) == set(map(tuple, events)):
            break
        else:
            events = mod_events

    for s in mod_events:
        if s[0] >= monday and s[1] <= now:
            total += s[1]-s[0]
        elif s[0] < monday and s[1] > now:
            total = now-monday
            break
        elif s[0] >= monday:
            total += now-s[0]
        elif s[1] <= now:
            total += s[1]-monday
    str1 = f"Статистика\n\nЗагруженность недели: {(total/(now-monday)*100).__round__(2)}%"

    #дата
    plans_date = f"""
        SELECT
            DependTime,DateEvent
        FROM
            plans
        WHERE
            (idUser={ID_USER})
        AND
            (DateEvent BETWEEN '{monday}' AND '{now}')
        """
    stat_date = db.execute_read_query(connection, plans_date)
    for s in stat_date:
        if s[0] == "срочное важное":
            depend_ints["Срочные важные"] += 1
        elif s[0] == "несрочное важное":
            depend_ints["Несрочные важные"] += 1
        elif s[0] == "срочное неважное":
            depend_ints["Срочные неважные"] += 1
        elif s[0] == "несрочное неважное":
            depend_ints["Несрочные неважные"] += 1
        y[s[1].weekday()] += 1
    str2 = f"\n\nВсего событий неопределённой длительности за неделю: {len(stat_date)}"
    str22 = ""
    for di in depend_ints.items():
        str22 += f"\n{di[0]}: {di[1]}"
    for k in depend_ints.keys():
        depend_ints[k] = 0

    #ничего
    plans_nth = f"""
    SELECT
        DependTime
    FROM
        plans
    WHERE
        (idUser={ID_USER})
    AND
        (DateEvent IS NULL)
    AND
        (BeginTime IS NULL)
    """
    stat_nth = db.execute_read_query(connection, plans_nth)
    for s in stat_nth:
        if s[0] == "срочное важное":
            depend_ints["Срочные важные"] += 1
        elif s[0] == "несрочное важное":
            depend_ints["Несрочные важные"] += 1
        elif s[0] == "срочное неважное":
            depend_ints["Срочные неважные"] += 1
        elif s[0] == "несрочное неважное":
            depend_ints["Несрочные неважные"] += 1
    str3 = f"\n\nВсего событий без привязки к дате и времени: {len(stat_nth)}"
    str32 = ""
    for di in depend_ints.items():
        str32 += f"\n{di[0]}: {di[1]}"
        
    #график
    photo(y, monday, now, str1+str2+str22+str3+str32, message)
    keyboard(message)
#######################################################################################################################

#######################################################################################################################
# ОБРАБОТКА НАЖАТИЙ INLINE КНОПОК
#######################################################################################################################

MARK_2 = None


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    global RET_DATA, FINISH, MARK_1, DATE_EVENT, CLICK, MARK_2, NEW_DATE
    RET_DATA = None
    if call is None:
        bot.answer_callback_query(callback_query_id=call.id)
    elif ";" in str(call.data):
        (action, year, month, day) = data_calendar.separate_callback_data(call.data)
        curr = datetime.datetime(int(year), int(month), 1)

        if action == "День":
            RET_DATA = datetime.datetime(int(year), int(month), int(day))
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            if MARK_1 is None:
                if END_TIME is None:
                    bot.send_message(call.message.chat.id, f"Вы выбрали дату {RET_DATA.date()}")
                    msg = bot.send_message(call.message.chat.id,
                                           "Введите нужное время, разделив часы и минуты знаком ':'", reply_markup=None)
                    bot.register_next_step_handler(msg, time_selector)
                else:
                    FINISH = RET_DATA
                    msg = bot.send_message(call.message.chat.id,
                                           f"Вы выбрали дату {FINISH.date()}. Введите количество дней в промежутке между повторами",
                                           reply_markup=None)
                    bot.register_next_step_handler(msg, day_interval)
            elif MARK_1 == 1:
                if DATE_EVENT is None:
                    DATE_EVENT = RET_DATA
                    msg = bot.send_message(call.message.chat.id,
                                           f"Вы выбрали дату {DATE_EVENT.date()}. Теперь введите название события",
                                           reply_markup=None)
                    bot.register_next_step_handler(msg, naming)
                else:
                    if MARK_2 is None:
                        FINISH = RET_DATA
                        msg = bot.send_message(call.message.chat.id,
                                               f"Вы выбрали дату {FINISH.date()}. Введите количество дней в промежутке между повторами",
                                               reply_markup=None)
                        bot.register_next_step_handler(msg, day_interval_for_date)
                    elif MARK_2 == 1:
                        NEW_DATE = RET_DATA
                        msg = bot.send_message(call.message.chat.id,
                                               f"Вы выбрали дату {NEW_DATE.date()}.",
                                               reply_markup=None)
                        new_date(msg)

            elif MARK_1 == 2:
                msg = bot.send_message(call.message.chat.id, f"Вы выбрали дату {RET_DATA.date()}")
                req(RET_DATA, msg)
            elif MARK_1 == 3:
                DATE_EVENT = RET_DATA
                msg = bot.send_message(call.message.chat.id, f"Вы выбрали дату {DATE_EVENT.date()}")
                search_free_window(msg)
            elif MARK_1 == 4:
                DATE_EVENT = RET_DATA
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                button1 = types.KeyboardButton("да")
                button2 = types.KeyboardButton("нет")
                markup.add(button1, button2)
                msg = bot.send_message(call.message.chat.id,
                                       f"Вы выбрали дату {DATE_EVENT.date()}. Теперь укажите зависимость от времени (выберите да/нет)",
                                       reply_markup=markup)
                bot.register_next_step_handler(msg, next_step_edit_dp)

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
                    reply_markup=data_calendar.create_calendar(int(ne.year), int(ne.month), 1))
            else:
                bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=data_calendar.create_calendar(int(ne.year), int(ne.month), START_DATE))
        else:
            bot.send_message(call.message.chat.id, "Выберите корректную дату!")


#######################################################################################################################


#######################################################################################################################
# ОБРАБОТКА СОЗДАНИЯ СОБЫТИЯ, ЗАВИСИМОГО ОТ ДАТЫ И ВРЕМЕНИ
#######################################################################################################################
# функция, выводящая календарь для начала события или конца события
def depending_from_time(message):
    if START_TIME is None:
        bot.send_message(message.chat.id, "Выберите день начала события",
                         reply_markup=data_calendar.create_calendar(None, None, 1))
    else:
        bot.send_message(message.chat.id, "Выберите день конца события",
                         reply_markup=data_calendar.create_calendar(None, None, START_DATE))


START_TIME, END_TIME = None, None


# функция обработки всех возможных вариантов установки времени начала и конца события
def time_selector(message):
    global START_TIME, END_TIME, START_DATE, END_DATE
    if START_TIME is None:
        START_TIME = message.text
        pattern = re.compile(r"^\d{1,2}:\d{2}$")
        if pattern.fullmatch(START_TIME) is not None:
            hours, minutes = map(lambda x: int(x), START_TIME.split(":"))
            if (0 <= hours < 24) and (0 <= minutes < 60):
                if ((datetime.time(hours,
                                   minutes) > datetime.datetime.now().time() and RET_DATA.date() == datetime.datetime.now().date()) or RET_DATA.date() > datetime.datetime.now().date()):
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
                if (END_DATE > START_DATE) or (
                        END_DATE.date() == START_DATE.date() and datetime.time(hours, minutes) > START_DATE.time()):
                    END_DATE = RET_DATA.replace(hour=hours, minute=minutes)
                    if MARK_3 is None:
                        bot.send_message(message.chat.id, f"Вы назначили конец события на {END_DATE}")
                        bot.send_message(message.chat.id, "Введите название события")
                        bot.register_next_step_handler(message, time_save_event)
                    elif MARK_3 == 1:
                        msg = bot.send_message(message.chat.id, f"Вы назначили конец события на {END_DATE}")
                        START_TIME, END_TIME = None, None
                        new_date_and_time(msg)
                else:
                    bot.send_message(message.chat.id,
                                     f"Вы не можете назначить конец события раньше начала (начало в {START_DATE.time()}). Выберите время заново")
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


# функция фиксирования начала, конца события и самого события
def time_save_event(message):
    global TEXT
    TEXT = message.text
    bot.send_message(message.chat.id, f"Событие '{TEXT}' установлено с {START_DATE} по {END_DATE}")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("да")
    button2 = types.KeyboardButton("нет")
    markup.add(button1, button2)
    bot.send_message(message.chat.id, f"Данное событие циклично?", reply_markup=markup)
    bot.register_next_step_handler(message, looping)


# функция обработки введенного промежутка между повторами
def day_interval(message):
    global FINISH, START_TIME, END_TIME
    num = message.text
    delta = FINISH.date() - END_DATE.date()
    origin_delta = END_DATE - START_DATE
    if (num.isdigit() and int(num) > 0 and datetime.timedelta(days=int(num)) <= delta):
        new_start = START_DATE.replace(year=END_DATE.date().year, month=END_DATE.date().month, day=END_DATE.date().day)

        # для добавления в базу первого из повторяющихся события
        create_event = f"""
        INSERT INTO
          plans (idUser, BeginTime, EndTime, Event)
        VALUES
          ('{ID_USER}', '{START_DATE}', '{END_DATE}', '{TEXT}')
        """
        db.execute_query(connection, create_event)

        i = 1
        while new_start < FINISH:
            new_start += datetime.timedelta(days=int(num))
            new_end = new_start + origin_delta
            i += 1

            # для добавления в базу последующих повторяющихся событий
            create_event = f"""
            INSERT INTO
              plans (idUser, BeginTime, EndTime, Event)
            VALUES
              ('{ID_USER}', '{new_start}', '{new_end}', '{TEXT}')
            """
            db.execute_query(connection, create_event)

        bot.send_message(message.chat.id,
                         f"Все повторы данного события и само событие зафиксированы. Всего их получилось {i}")
        START_TIME, END_TIME, FINISH = None, None, None
        bot.send_message(message.chat.id, 'Хотите получить напоминание о данном событии?')
        bot.register_next_step_handler(message, notification)
    else:
        bot.send_message(message.chat.id,
                         "Вы ввели не натуральное число или большее, чем количество дней между концом события и днем последнего повторения. Повторите попытку")
        bot.register_next_step_handler(message, day_interval)


# функция определения цикличности события
def looping(message):
    global START_TIME, END_TIME, FINISH
    answer = message.text.lower()
    if answer == "да":
        dt = END_DATE + datetime.timedelta(days=1)
        bot.send_message(message.chat.id, "До какого дня нужно повторять событие (включительно)?",
                         reply_markup=data_calendar.create_calendar(None, None, dt))
    elif answer == "нет":

        none_value = None
        create_event = f"""
        INSERT INTO
          plans (idUser, BeginTime, EndTime, Event)
        VALUES
          ('{ID_USER}', '{START_DATE}', '{END_DATE}', '{TEXT}')
        """
        db.execute_query(connection, create_event)

        START_TIME, END_TIME, FINISH = None, None, None
        bot.send_message(message.chat.id, "Событие успешно создано")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("да")
        button2 = types.KeyboardButton("нет")
        markup.add(button1, button2)
        bot.send_message(message.chat.id, "Хотите получить напоминание о данном событии?", reply_markup=markup)
        bot.register_next_step_handler(message, notification)
    else:
        bot.send_message(message.chat.id, "Выберите или введите да/нет для продолжения")
        bot.register_next_step_handler(message, looping)


# функция, для установки даты и времени напоминания
def datetime_reminder(message):
    bot.send_message(message.chat.id,
                     "Введите дату и время, когда вы хотите получить напоминание, в формате ГГГГ-ММ-ДД чч:мм.")
    bot.register_next_step_handler(message, get_reminder)


CHANGE_EVENT, DATE_EVENT = None, None


# функция обработки введенного времени для напоминания
def get_reminder(message):
    global CHANGE_EVENT, START_DATE, DATE_EVENT, EVENT_ID, NAME_REM
    try:
        if CHANGE_EVENT is not None:
            reminder_time = datetime.datetime.strptime(message.text, "%Y-%m-%d %H:%M")
            # если дата напоминания позже начала события
            if DATE_EVENT < reminder_time:
                bot.send_message(message.chat.id,
                                 "Дата напоминания установлена позже начала события. Повторите попытку")
                datetime_reminder(message)
            # если дата напоминания раньше сегодняшней
            elif reminder_time < datetime.datetime.now():
                bot.send_message(message.chat.id, "Проверьте правильность ввода!")
                datetime_reminder(message)
            else:
                get_event = f"""
                    SELECT Event
                    FROM plans
                    WHERE id = {EVENT_ID}
                    """
                NAME_REM = db.execute_read_query(connection, get_event)[0][0]
                bot.send_message(message.chat.id,
                                 "Напоминание '{}' установлено на {}.".format(NAME_REM, reminder_time))
                today = datetime.datetime.now()
                date = reminder_time - today
                seconds = date.total_seconds()
                reminder_timer = threading.Timer(seconds, send_reminder, [message.chat.id, NAME_REM])
                reminder_timer.start()
                CHANGE_EVENT = None
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                button1 = types.KeyboardButton("да")
                button2 = types.KeyboardButton("нет")
                markup.add(button1, button2)
                bot.send_message(message.chat.id, "Желаете продолжить редактирование?", reply_markup=markup)
                bot.register_next_step_handler(message, resulting_action)

        else:
            reminder_time = datetime.datetime.strptime(message.text, "%Y-%m-%d %H:%M")
            # если дата напоминания позже начала события
            if START_DATE < reminder_time:
                bot.send_message(message.chat.id,
                                 "Дата напоминания установлена позже начала события. Повторите попытку")
                datetime_reminder(message)
            # если дата напоминания раньше сегодняшней
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


# функция, которая отправляет напоминание пользователю

EVENT_ID = None


def send_reminder(chat_id, reminder_name):
    global EVENT_ID, NAME_REM, TEXT
    if EVENT_ID is not None:
        bot.send_message(chat_id, "Напоминание о событии '{}'!".format(NAME_REM))
    else:
        bot.send_message(chat_id, "Напоминание о событии '{}'!".format(TEXT))


# функция определения потребности напоминания
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
# функция определения категории события
def category_independent(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Срочное важное")
    button2 = types.KeyboardButton("Несрочное важное")
    button3 = types.KeyboardButton("Срочное неважное")
    button4 = types.KeyboardButton("Несрочное неважное")
    markup.add(button1, button2, button3, button4)
    bot.send_message(message.chat.id, "Выберите категорию события", reply_markup=markup)
    bot.register_next_step_handler(message, name_independent)


# функция наименования события
def name_independent(message):
    # прописать варианты всех возможных команд через elif!
    global CATEGORY
    CATEGORY = message.text.lower()
    if CATEGORY == "срочное важное" or CATEGORY == "несрочное важное" or CATEGORY == "срочное неважное" or CATEGORY == "несрочное неважное":
        bot.send_message(message.chat.id, "Введите название события")
        bot.register_next_step_handler(message, exit_independent)
    elif CATEGORY == "/back":
        keyboard(message)
    else:
        bot.send_message(message.chat.id, "Проверьте корректность введённой команды или используйте кнопки.")
        bot.register_next_step_handler(message, name_independent)


# результирующая функция
def exit_independent(message):
    # ЗДЕСЬ И ВО ВСЕХ ТАКИХ ФУНКЦИЯХ НУЖНО ПРОПИСАТЬ ДЕЙСТВИЯ КОМАНД /START, /HELP И ДРУГИХ!
    global ID_USER, CATEGORY
    text = message.text
    get_events = f"""
        SELECT Event
        FROM plans
        WHERE (idUser = {ID_USER})
        AND (DateEvent IS NULL)
        AND (BeginTime IS NULL)
        """
    check_list = db.execute_read_query(connection, get_events)
    check = True

    for i in check_list:
        if i[0].lower() == text.lower():
            check = False
    if check:
        create_event = f"""
        INSERT INTO
          plans (idUser, DependTime, Event)
        VALUES
          ('{ID_USER}', '{CATEGORY}', '{text}')
        """
        db.execute_query(connection, create_event)

        bot.send_message(message.chat.id, "Событие '{}' успешно добавлено в категорию '{}'!".format(text, CATEGORY))
        keyboard(message)
    else:
        bot.send_message(message.chat.id, "Событие с данным названием и данной степенью важности уже существуют")


#######################################################################################################################


#######################################################################################################################
# ОБРАБОТКА СОБЫТИЯ, ЗАВИСИМОГО ТОЛЬКО ОТ ДАТЫ
#######################################################################################################################
def depending_from_date(message):
    bot.send_message(message.chat.id, "Выберите дату события",
                     reply_markup=data_calendar.create_calendar(None, None, 1))


# функция определения названия события
def naming(message):
    global NAME, DATE_EVENT
    NAME = message.text
    get_check = f"""
        SELECT DateEvent, Event
        FROM plans
        WHERE (idUser = {ID_USER})
        AND (DateEvent = '{DATE_EVENT}')
        AND (DependTime IS NOT NULL)
        """
    check_list = db.execute_read_query(connection, get_check)
    new_check_list = [(i, j.lower()) for i, j in check_list]
    check = True
    event = (DATE_EVENT.date(), NAME.lower())
    for i in new_check_list:
        if event == i:
            check = False
    if check:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Срочное важное")
        button2 = types.KeyboardButton("Несрочное важное")
        button3 = types.KeyboardButton("Срочное неважное")
        button4 = types.KeyboardButton("Несрочное неважное")
        markup.add(button1, button2, button3, button4)
        bot.send_message(message.chat.id, "Выберите категорию события", reply_markup=markup)
        bot.register_next_step_handler(message, loop_define)
    else:
        bot.send_message(message.chat.id, "Данное событие уже есть в планах на указанный день. Повторите попытку")
        bot.register_next_step_handler(message, naming)


def loop_define(message):
    global TYPE
    TYPE = message.text.lower()
    if TYPE == "срочное важное" or TYPE == "несрочное важное" or TYPE == "срочное неважное" or TYPE == "несрочное неважное":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("да")
        button2 = types.KeyboardButton("нет")
        markup.add(button1, button2)
        bot.send_message(message.chat.id, "Последнее, данное событие является цикличным?", reply_markup=markup)
        bot.register_next_step_handler(message, looping_date)
    elif TYPE == "/back":
        keyboard(message)
    else:
        bot.send_message(message.chat.id, "Проверьте корректность введённой команды или используйте кнопки.")
        bot.register_next_step_handler(message, loop_define)


# функция определения цикличности
def looping_date(message):
    global DATE_EVENT
    answer = message.text.lower()
    if answer == "да":
        dt = DATE_EVENT + datetime.timedelta(days=1)
        bot.send_message(message.chat.id, "До какого дня нужно повторять событие (включительно)?",
                         reply_markup=data_calendar.create_calendar(None, None, dt))
    elif answer == "нет":

        create_event = f"""
        INSERT INTO
          plans (idUser, DependTime, DateEvent, Event)
        VALUES
          ('{ID_USER}', '{TYPE}', '{DATE_EVENT}', '{NAME}')
        """
        db.execute_query(connection, create_event)

        bot.send_message(message.chat.id, f"Событие {NAME} записано на {DATE_EVENT.date()}")
        keyboard(message)
    else:
        bot.send_message(message.chat.id, "Выберите или введите да/нет для продолжения")
        bot.register_next_step_handler(message, looping_date)


# функция добавления всех повторов
def day_interval_for_date(message):
    num = message.text
    delta = FINISH - DATE_EVENT
    if (num.isdigit() and int(num) > 0 and datetime.timedelta(days=int(num)) <= delta):
        new_date = DATE_EVENT

        create_event = f"""
        INSERT INTO
          plans (idUser, DependTime, DateEvent, Event)
        VALUES
          ('{ID_USER}', '{TYPE}', '{DATE_EVENT}', '{NAME}')
        """
        db.execute_query(connection, create_event)

        i = 1
        while new_date < FINISH:
            new_date += datetime.timedelta(days=int(num))
            i += 1

            create_event = f"""
            INSERT INTO
              plans (idUser, DependTime, DateEvent, Event)
            VALUES
              ('{ID_USER}', '{TYPE}', '{new_date}', '{NAME}')
            """
            db.execute_query(connection, create_event)

        bot.send_message(message.chat.id,
                         f"Все повторы данного события, а также и само событие зафиксированы. Всего их получилось {i}")
        keyboard(message)
    else:
        bot.send_message(message.chat.id, "Ошибка. Введите корректное натуральное число")
        bot.register_next_step_handler(message, day_interval_for_date)


#######################################################################################################################


#######################################################################################################################
# ПРОСМОТР СВОБОДНЫХ ОКОН
#######################################################################################################################
#функция выбора типа окна
def free_windows(message):
    global MARK_1, DATE_EVENT
    answer = message.text.lower()
    if answer == "на день":
        MARK_1 = 3
        DATE_EVENT = None
        depending_from_date(message)
    elif answer == "на месяц":
        bot.send_message(message.chat.id, "Введите интересующий вас год", reply_markup=None)
        bot.register_next_step_handler(message, year_for_window)
    else:
        bot.send_message(message.chat.id, "Ошибка. Повторите ввод/выбор")
        bot.register_next_step_handler(message, free_windows)


#функция поиска окон в указанный день
def search_free_window(message):
    global DATE_EVENT, ID_USER   # DATE_EVENT выполняет ту же функцию, что и ранее

    get_today_events = f"""
    SELECT BeginTime, EndTime
    FROM plans
    WHERE idUser={ID_USER}
    AND (EndTime > '{DATE_EVENT}' AND BeginTime < '{DATE_EVENT.replace(hour=23, minute=59, second=59, microsecond=0)}')
    """
    today_events = db.execute_read_query(connection, get_today_events)
    
    events = list()
    d = int(DATE_EVENT.strftime('%d'))  # выбранный день
    i = j = 0
    for event in today_events:
        begin = [int(event[0].strftime('%d')), event[0].time()]
        end = [int(event[-1].strftime('%d')), event[-1].time()]
        if begin[0] < d and end[0] > d:
            bot.send_message(message.chat.id, "У вас отсутствуют свободные окна на выбранный день.")
            DATE_EVENT = None
            keyboard(message)
            return None
        elif begin[0] < d:
            events.append([datetime.time(0, 0), end[-1]])
            i = 1
        elif begin[0] == d and end[0] == d:
            events.append([begin[-1], end[-1]])
        else:
            events.append([begin[-1], datetime.time(23, 59)])
            j = 1

    if i != 1:
        events.append([datetime.time(0, 0)])
    if j != 1:
        events.append([datetime.time(23, 59)])
    events.sort(key=lambda x: x[0])
    
    while True:
        mod_events = modifed_events(events)
        if set(map(tuple, mod_events)) == set(map(tuple, events)):
            break
        else:
            events = mod_events

    windows = list()
    for i in range(len(events) - 1):
        windows.append([events[i][-1], events[i + 1][0]])
    res = str()
    for window in windows:
        res += "С " + window[0].strftime("%H:%M") + " до " + window[1].strftime("%H:%M") + "\n"

    bot.send_message(message.chat.id, f"Ваши свободные окна на выбранный день:\n{res}")
    DATE_EVENT = None
    keyboard(message)


#функция проверки введенного года
def year_for_window(message):
    global YEAR
    year = message.text
    if year.isdigit() and (datetime.datetime.now().year <= int(year) < 2100):
        YEAR = int(year)
        bot.send_message(message.chat.id, "Отлично, теперь введите номер интересующего Вас месяца")
        bot.register_next_step_handler(message, month_for_window)
    else:
        bot.send_message(message.chat.id, "Введите корректный год")
        bot.register_next_step_handler(message, year_for_window)


#функция проверки введенного месяца
def month_for_window(message):
    global MONTH, YEAR
    month = message.text
    now = datetime.datetime.now()
    if month.isdigit() and (now.month == int(month)) and YEAR == now.year:
        MONTH = int(month)
        DAY = now.day
        month_date_window = f"""
        SELECT DateEvent
        FROM plans
        WHERE idUser={ID_USER}
        AND DateEvent>='{YEAR}-{MONTH}-{DAY}'
        AND DateEvent<='{YEAR}-{MONTH}-{data_calendar.calendar.monthrange(YEAR, MONTH)[-1]}'
        """
        month_date_events = db.execute_read_query(connection, month_date_window)
        events = set()
        for event in month_date_events:
            events.add(int(event[0].strftime("%d")))

        days = data_calendar.calendar.monthrange(YEAR, MONTH)[-1]
        month_datetime_window = f"""
        SELECT BeginTime, EndTime
        FROM plans
        WHERE idUser={ID_USER}
        AND BeginTime>='{YEAR}-{MONTH}-{DAY} 00:00:00'
        AND EndTime<='{YEAR}-{MONTH}-{days} 23:59:59'
        """
        month_datetime_events = db.execute_read_query(connection, month_datetime_window)
        for event in month_datetime_events:
            events.add(int(event[0].strftime("%d")))

        calendar_image.get_image_calendar(tuple(events), YEAR, MONTH)
        img = open("calendar.png", "rb")
        bot.send_photo(message.chat.id, photo=img, caption="Ваши свободные окна на указанный месяц")
        keyboard(message)
    elif month.isdigit() and (0 < int(month) < 13):
        MONTH = int(month)
        month_date_window = f"""
        SELECT DateEvent
        FROM plans
        WHERE idUser={ID_USER}
        AND DateEvent>='{YEAR}-{MONTH}-01'
        AND DateEvent<='{YEAR}-{MONTH}-{data_calendar.calendar.monthrange(YEAR, MONTH)[-1]}'
        """
        month_date_events = db.execute_read_query(connection, month_date_window)
        events = set()
        for event in month_date_events:
            events.add(int(event[0].strftime("%d")))

        days = data_calendar.calendar.monthrange(YEAR, MONTH)[-1]
        month_datetime_window = f"""
        SELECT BeginTime, EndTime
        FROM plans
        WHERE idUser={ID_USER}
        AND BeginTime>='{YEAR}-{MONTH}-01 00:00:00'
        AND EndTime<='{YEAR}-{MONTH}-{days} 23:59:59'
        """
        month_datetime_events = db.execute_read_query(connection, month_datetime_window)
        for event in month_datetime_events:
            events.add(int(event[0].strftime("%d")))

        # month_days = set(range(1, days + 1))
        # windows = tuple(month_days^events)

        calendar_image.get_image_calendar(tuple(events), YEAR, MONTH)
        img = open("calendar.png", "rb")
        bot.send_photo(message.chat.id, photo=img, caption="Ваши свободные окна на указанный месяц")
        keyboard(message)
    else:
        bot.send_message(message.chat.id, "Введите корректный месяц")
        bot.register_next_step_handler(message, month_for_window)

#######################################################################################################################
# ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ОКОН
#######################################################################################################################
# Жесть функция
def from_two_to_one(event1, event2) -> list:
    if event1[0] == event2[0] and event1[-1] <= event2[-1]:
        return event2
    elif event1[0] == event2[0] and event1[-1] > event2[-1]:
        return event1
    elif event1[-1] < event2[0]:  # случай нулевого пересечения  
        return None
    elif event1[0] < event2[0] and event1[1] >= event2[0] and event1[-1] < event2[-1]:
        return (event1[0],event2[-1])
    elif event1[0] < event2[0] and event1[-1] >= event2[-1]:
        return event1

def modifed_events(events_in: list) -> list:
    events = events_in.copy()
    
    intermed_list = list()
    answers = list()
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            answer = from_two_to_one(events[i], events[j])
            if answer is None:
                pass
            else:
                if answer not in answers:
                    answers.append(answer)
                if events[i] not in intermed_list:
                    intermed_list.append(events[i])
                if events[j] not in intermed_list:
                    intermed_list.append(events[j])            
    
    for event in intermed_list:
        if event in events:
            events.remove(event)
    for answer in answers:
        events.append(answer)

    events.sort(key=lambda x: x[0])

    return events
######################################################################################################################


#######################################################################################################################
# РЕДАКТИРОВАНИЕ И УДАЛЕНИЕ СОБЫТИЙ
#######################################################################################################################
# функция определения типа события (1 этап)
START_EDIT = None


def edit_events(message):
    global MARK_1, DATE_EVENT
    sel = message.text
    if sel.lower() == "фиксированное":
        MARK_1 = 4
        DATE_EVENT = None
        depending_from_date(message)
    elif sel.lower() == "независимое":
        list_edit_ind(message)
    # заглушка для перезагрузки бота
    elif message.text == "/start":
        start_message(message)
    elif message.text == "/help":
        help_bot(message)
    # для отката на одно действие назад
    elif message.text == "/back":
        keyboard(message)
    else:
        msg = bot.send_message(message.chat.id, "Проверьте корректность введённой команды или используйте кнопки.")
        bot.register_next_step_handler(msg, edit_events)


def list_edit_ind(message):
    global START_EDIT, NEW_LIST, ID_USER
    get_indep_events = f"""
                    SELECT DependTime, Event
                    FROM plans
                    WHERE (idUser={ID_USER})
                    AND (DateEvent IS NULL)
                    AND (BeginTime IS NULL)
                    """
    indep_events = db.execute_read_query(connection, get_indep_events)
    print(indep_events)
    result = ""
    START_EDIT = None
    if indep_events == []:
        bot.send_message(message.chat.id, "У вас нет событий данного типа", reply_markup=None)
        keyboard(message)
    else:
        NEW_LIST = list()
        for i, tup in enumerate(indep_events, 1):
            result += f"{i}. " + " ".join(str(x) for x in tup) + "\n"
            NEW_LIST.append((i, tup))
        bot.send_message(message.chat.id, "Вот ваши планы: \n" + result)
        bot.send_message(message.chat.id, "Выберите интересующее Вас событие (введите его порядковый номер)",
                         reply_markup=None)
        bot.register_next_step_handler(message, take_num)


# функция определения зависимости (время/дата)
def next_step_edit_dp(message):
    global DATE_EVENT, START_EDIT, END_EDIT
    answer = message.text.lower()
    if answer == "да":  # зависит от даты и времени
        if DATE_EVENT.date() == datetime.datetime.now().date():  # сегодня
            START_EDIT = datetime.datetime.now()
            END_EDIT = DATE_EVENT.replace(hour=23, minute=59, second=59, microsecond=0)
        else:  # любой другой день
            START_EDIT = DATE_EVENT
            END_EDIT = DATE_EVENT.replace(hour=23, minute=59, second=59, microsecond=0)
        msg = bot.send_message(message.chat.id, "Понял", reply_markup=None)
        list_edit(msg)
    elif answer == "нет":  # зависит только от даты
        START_EDIT = 1
        msg = bot.send_message(message.chat.id, "Понял", reply_markup=None)
        list_edit(msg)
    # заглушка для перезагрузки бота
    elif message.text == "/start":
        start_message(message)
    elif message.text == "/help":
        help_bot(message)
    # для отката на одно действие назад
    elif message.text == "/back":
        keyboard(message)
    else:
        bot.send_message(message.chat.id, "Проверьте корректность введённой команды или используйте кнопки.")
        bot.register_next_step_handler(message, next_step_edit_dp)


# функция получения списка событий на день
def list_edit(message):
    global DATE_EVENT, ID_USER, START_EDIT, END_EDIT, NEW_LIST
    if START_EDIT == 1:  # зависит только от даты
        get_today_events = f"""
            SELECT
                DependTime, DateEvent,Event
            FROM
                plans
            WHERE
                (idUser={ID_USER})
            AND
                (DateEvent = '{DATE_EVENT.date()}')
            """

    #################### name END_EDIT is not defined, если переходить к повторному редактированию ###################################

    else:  # зависит только от даты и времени
        get_today_events = f"""
            SELECT BeginTime,EndTime,Event
            FROM plans
            WHERE (idUser={ID_USER})
            AND (
            (BeginTime BETWEEN '{START_EDIT}' AND '{END_EDIT}')
            OR
            (BeginTime<'{START_EDIT}' AND EndTime>'{END_EDIT}'))
            """
    today_events = db.execute_read_query(connection, get_today_events)
    if today_events == []:
        bot.send_message(message.chat.id, "У вас нет событий данного типа на выбранную дату", reply_markup=None)
        keyboard(message)
    else:
        result = ""
        NEW_LIST = []
        for i, tup in enumerate(today_events, 1):
            result += f"{i}. " + " ".join(str(x) for x in tup) + "\n"
            NEW_LIST.append((i, tup))
        bot.send_message(message.chat.id, f"Ваши события на {DATE_EVENT.date()}: \n" + result)
        bot.send_message(message.chat.id, "Введите номер интересующего Вас события")
        bot.register_next_step_handler(message, take_num)


# функция выбора события из списка
def take_num(message):
    global NEW_LIST, CHANGE_EVENT, EVENT_ID
    answer = message.text
    if answer.isdigit() and int(answer) > 0 and int(answer) <= len(NEW_LIST):
        num = int(answer)
        CHANGE_EVENT = NEW_LIST[num - 1][1]
        if START_EDIT == 1:
            get_id_event = f"""
                SELECT id
                FROM plans
                WHERE (idUser = {ID_USER})
                AND (DependTime = '{CHANGE_EVENT[0]}')
                AND (DateEvent = '{CHANGE_EVENT[1]}')
                AND (Event = '{CHANGE_EVENT[2]}')
                """
        elif START_EDIT is None:
            get_id_event = f"""
                SELECT id
                FROM plans
                WHERE (idUser = {ID_USER})
                AND (DateEvent IS NULL)
                AND (BeginTime IS NULL)
                AND (DependTime = '{CHANGE_EVENT[0]}')
                AND (Event = '{CHANGE_EVENT[1]}')
                """
        else:
            get_id_event = f"""
                SELECT id
                FROM plans
                WHERE (idUser = {ID_USER})
                AND (BeginTime = '{CHANGE_EVENT[0]}')
                AND (EndTime = '{CHANGE_EVENT[1]}')
                AND (Event = '{CHANGE_EVENT[2]}')
                """
        EVENT_ID = db.execute_read_query(connection, get_id_event)[0][0]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if (START_EDIT is not None) and (START_EDIT != 1):
            button1 = types.KeyboardButton("редактировать")
            button2 = types.KeyboardButton("установить напоминание")
            button3 = types.KeyboardButton("удалить")
            markup.add(button1, button2, button3)
        else:
            button1 = types.KeyboardButton("редактировать")
            button2 = types.KeyboardButton("удалить")
            markup.add(button1, button2)
        bot.send_message(message.chat.id, "Что Вы хотите сделать с событием?", reply_markup=markup)
        bot.register_next_step_handler(message, action)
    # заглушка для перезагрузки бота
    elif message.text == "/start":
        start_message(message)
    elif message.text == "/help":
        help_bot(message)
    # для отката на одно действие назад
    elif message.text == "/back":
        if (START_EDIT is not None) and (START_EDIT != 1):
            list_edit(message)
        else:
            list_edit_ind(message)
    else:
        bot.send_message(message.chat.id, "Проверьте корректность введённого номера и повторите попытку.")
        bot.register_next_step_handler(message, take_num)


# функция выбора действия над событием
def action(message):
    global CHANGE_EVENT, ID_USER, START_EDIT, DATE_EVENT, TEXT, EVENT_ID
    answer = message.text.lower()
    if answer == "редактировать":
        if START_EDIT == 1:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("важность")
            button2 = types.KeyboardButton("дата")
            button3 = types.KeyboardButton("название")
            markup.add(button1, button2, button3)
            bot.send_message(message.chat.id, "Выберите параметр для изменения", reply_markup=markup)
            bot.register_next_step_handler(message, param_for_change)
        elif START_EDIT is None:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("важность")
            button2 = types.KeyboardButton("название")
            markup.add(button1, button2)
            bot.send_message(message.chat.id, "Выберите параметр для изменения", reply_markup=markup)
            bot.register_next_step_handler(message, param_for_change)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("название")
            button2 = types.KeyboardButton("дата и время")
            markup.add(button2, button1)
            bot.send_message(message.chat.id, "Выберите параметр для изменения", reply_markup=markup)
            bot.register_next_step_handler(message, param_for_change)
    elif answer == "удалить":
        bot.send_message(message.chat.id, "Ваше событие успешно удалено")

        del_event = f"""
        DELETE FROM plans
        WHERE id={EVENT_ID}
        """
        db.execute_query(connection, del_event)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("да")
        button2 = types.KeyboardButton("нет")
        markup.add(button1, button2)
        bot.send_message(message.chat.id, "Желаете продолжить редактирование?", reply_markup=markup)
        bot.register_next_step_handler(message, resulting_action)
    elif (answer == "установить напоминание" and START_EDIT is not None) or (
            answer == "установить напоминание" and START_EDIT != 1):
        TEXT = None
        datetime_reminder(message)
    # заглушка для перезагрузки бота
    elif message.text == "/start":
        start_message(message)
    elif message.text == "/help":
        help_bot(message)
    # для отката на одно действие назад
    elif message.text == "/back":
        keyboard(message)
    else:
        bot.send_message(message.chat.id, "Проверьте корректность ввода и повторите попытку.")
        bot.register_next_step_handler(message, action)


# функция выбора параметра для события, зависимого только от дня
def param_for_change(message):
    global START_EDIT, MARK_1, MARK_2, MARK_3
    answer = message.text.lower()
    if (answer == "важность" and START_EDIT == 1) or (answer == "важность" and START_EDIT is None):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Срочное важное")
        button2 = types.KeyboardButton("Несрочное важное")
        button3 = types.KeyboardButton("Срочное неважное")
        button4 = types.KeyboardButton("Несрочное неважное")
        markup.add(button1, button2, button3, button4)
        bot.send_message(message.chat.id, "Введите новую степень важности", reply_markup=markup)
        bot.register_next_step_handler(message, new_priority)
    elif answer == "название":
        bot.send_message(message.chat.id, "Введите новое название событие")
        bot.register_next_step_handler(message, new_name)
    elif answer == "дата" and START_EDIT == 1:
        MARK_1 = 1
        MARK_2 = 1
        depending_from_date(message)
    elif (answer == "дата и время" and START_EDIT is not None) or (answer == "дата и время" and START_EDIT != 1):
        MARK_1 = None
        MARK_3 = 1
        depending_from_time(message)
    # заглушка для перезагрузки бота
    elif message.text == "/start":
        start_message(message)
    elif message.text == "/help":
        help_bot(message)
    # для отката на одно действие назад
    elif message.text == "/back":
        keyboard(message)
    else:
        bot.send_message(message.chat.id, "Проверьте корректность ввода и повторите попытку.")
        bot.register_next_step_handler(message, action)


# функция изменения важности события
def new_priority(message):
    global EVENT_ID
    new_category = message.text.lower()
    if new_category in ("срочное важное", "несрочное важное", "срочное неважное", "несрочное неважное"):

        update_category = f"""
        UPDATE plans
        SET DependTime = '{new_category}'
        WHERE id = {EVENT_ID}
        """
        db.execute_query(connection, update_category)

        bot.send_message(message.chat.id, "Изменение важности события успешно завершено")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("да")
        button2 = types.KeyboardButton("нет")
        markup.add(button1, button2)
        bot.send_message(message.chat.id, "Желаете продолжить редактирование?", reply_markup=markup)
        bot.register_next_step_handler(message, resulting_action)
    # заглушка для перезагрузки бота
    elif message.text == "/start":
        start_message(message)
    elif message.text == "/help":
        help_bot(message)
    # для отката на одно действие назад
    elif message.text == "/back":
        keyboard(message)
    else:
        bot.send_message(message.chat.id, "Проверьте корректность введенного параметра важности и повторите попытку.")
        bot.register_next_step_handler(message, new_priority)


# функция изменения названия события
def new_name(message):
    global ID_USER, START_EDIT
    name = message.text
    if START_EDIT is None:
        get_name = f"""
        SELECT Event
        FROM plans
        WHERE idUser={ID_USER}
        AND DependTime IS NOT NULL
        AND DateEvent IS NULL
        """
        name_list = db.execute_read_query(connection, get_name)
        check = True
        for i in name_list:
            if name == i[0]:
                check = False
                break
        if check:
            update_name = f"""
                    UPDATE plans
                    SET Event = '{name}'
                    WHERE id = {EVENT_ID}
                    """
            db.execute_query(connection, update_name)
            bot.send_message(message.chat.id, "Изменение названия события успешно завершено")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("да")
            button2 = types.KeyboardButton("нет")
            markup.add(button1, button2)
            bot.send_message(message.chat.id, "Желаете продолжить редактирование?", reply_markup=markup)
            bot.register_next_step_handler(message, resulting_action)
        else:
            bot.send_message(message.chat.id, "Событие с таким названием уже существует. Повторите попытку")
            bot.register_next_step_handler(message, new_name)
    elif START_EDIT is not None:
        if START_EDIT == 1:
            
            update_name = f"""
                        UPDATE plans
                        SET Event = '{name}'
                        WHERE id = {EVENT_ID}
                        """
            db.execute_query(connection, update_name)
            
        else:
            update_name = f"""
                                        UPDATE plans
                                        SET Event = '{name}'
                                        WHERE id = {EVENT_ID}
                                        """
            db.execute_query(connection, update_name)
        bot.send_message(message.chat.id, "Изменение названия события успешно завершено")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("да")
        button2 = types.KeyboardButton("нет")
        markup.add(button1, button2)
        bot.send_message(message.chat.id, "Желаете продолжить редактирование?", reply_markup=markup)
        bot.register_next_step_handler(message, resulting_action)
    elif message.text == "/start":
        start_message(message)
    elif message.text == "/help":
        help_bot(message)
        # для отката на одно действие назад
    elif message.text == "/back":
        keyboard(message)
    else:
        bot.send_message(message.chat.id, "Событие такого типа с данным названием уже существует. Повторите попытку.")
        bot.register_next_step_handler(message, new_name)


# функция изменения даты события, зависящего только от неё самой
def new_date(message):
    global NEW_DATE, ID_USER, EVENT_ID, MARK_2, MARK_1
    update_date = f"""
                    UPDATE plans
                    SET DateEvent = '{NEW_DATE}'
                    WHERE id = {EVENT_ID}
                    """
    db.execute_query(connection, update_date)
    MARK_1, MARK_2 = None, None
    bot.send_message(message.chat.id, "Изменение даты события успешно завершено")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("да")
    button2 = types.KeyboardButton("нет")
    markup.add(button1, button2)
    bot.send_message(message.chat.id, "Желаете продолжить редактирование?", reply_markup=markup)
    bot.register_next_step_handler(message, resulting_action)


def new_date_and_time(message):
    global START_DATE, END_DATE, ID_USER, EVENT_ID, MARK_3, MARK_1
    update_date_and_time = f"""
                UPDATE plans
                SET BeginTime = '{START_DATE}', EndTime = '{END_DATE}'
                WHERE id = {EVENT_ID}
                """
    db.execute_query(connection, update_date_and_time)
    MARK_3, START_DATE, MARK_1, END_DATE = None, None, None, None
    bot.send_message(message.chat.id, "Изменение даты и времени события успешно завершено")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("да")
    button2 = types.KeyboardButton("нет")
    markup.add(button1, button2)
    bot.send_message(message.chat.id, "Желаете продолжить редактирование?", reply_markup=markup)
    bot.register_next_step_handler(message, resulting_action)


# функция-конец)
def resulting_action(message):
    global START_EDIT
    answer = message.text.lower()
    if answer == "да":
        if START_EDIT == 1 or START_EDIT is not None:
            list_edit(message)
        else:
            list_edit_ind(message)
    elif answer == "нет":
        keyboard(message)
    # заглушка для перезагрузки бота
    elif message.text == "/start":
        start_message(message)
    elif message.text == "/help":
        help_bot(message)
    # для отката на одно действие назад
    elif message.text == "/back":
        keyboard(message)
    else:
        bot.send_message(message.chat.id, "Проверьте корректность введённого номера и повторите попытку.")
        bot.register_next_step_handler(message, action)


#######################################################################################################################


#######################################################################################################################
# ОБРАБОТКА ТЕКСТОВЫХ НЕВЕРНЫХ СООБЩЕНИЙ
#######################################################################################################################
@bot.message_handler(content_types=["text"])
def send_message(message):
    bot.send_message(message.chat.id, "Соблюдайте, пожалуйста, формат сообщений")


#######################################################################################################################


#######################################################################################################################
# МЕНЮ
#######################################################################################################################
bot.set_my_commands([
    telebot.types.BotCommand("/start", "Перезапуск бота"),
    telebot.types.BotCommand("/back", "Назад"),
    telebot.types.BotCommand("/help", "Помощь"),
    telebot.types.BotCommand("/option", 'Доступные опции'),
    telebot.types.BotCommand("/settings", "Изменить логин или пароль")
])
#######################################################################################################################

bot.infinity_polling()
