# главный файл бота

import datetime, telebot, re, threading
from telebot import types
import data_calendar
import mysqlconnector as db
from multiprocessing import freeze_support

freeze_support()


bot = telebot.TeleBot("6058933003:AAG5Ti0fmydE9xfQYzPYv35pUM4jPOt7LY0")
connection = db.create_connection("127.0.0.1", "root", "1234", "Calendar")

#######################################################################################################################
#  СТАРТОВАЯ РАБОТА БОТА (РЕГИСТРАЦИЯ И ВХОД)
#######################################################################################################################
@bot.message_handler(commands=["start"])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Войти")
    button2 = types.KeyboardButton("Зарегистрироваться")
    markup.add(button1, button2)
    bot.send_message(message.chat.id, "Здравствуйте! Я ваш персональный бот-календарь. Выберите действие для начала работы.", reply_markup=markup)
    bot.register_next_step_handler(message, answering)


def answering(message):
    text = message.text
    if text.lower() == "войти":
        bot.send_message(message.chat.id, "Введите имя пользователя (после знака '@').", reply_markup=None)
        bot.register_next_step_handler(message, login)
    elif text.lower() == "зарегистрироваться":
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
    get_pas = f"""
    SELECT 
    Password FROM users WHERE Login='{LOGIN}' LIMIT 1
    """
    if db.execute_read_query(connection, get_pas)[0][0] == hash(pas):
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
    LOGIN = message.from_user.username
    pas = message.text
    pattern1 = re.compile(r"(?=.*[a-z])(?=.*[A-Z])[a-zA-Z\d]{8,}$")
    if pattern1.fullmatch(pas) is not None:
        create_user = f"""
        INSERT INTO
          users (login, password)
        VALUES
          ('{LOGIN}', '{hash(f"{pas}")}')
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
        msg = bot.send_message(message.chat.id, "Введённый пароль не соответствует стандартам. Введите пароль повторно.")
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
#функция обработки выбора опций
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
        ...

    elif sel.lower() == "статистика":
        bot.register_next_step_handler(message, statistics)

    elif sel.lower() == "добавить событие":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Дата и время")
        button2 = types.KeyboardButton("Только дата")
        button3 = types.KeyboardButton("Независимое")
        markup.add(button1, button2, button3)
        bot.send_message(message.chat.id, "Выберите нужный тип события. (Ответьте на вопрос: от чего зависит добавляемое Вами событие?)", reply_markup=markup)
        bot.register_next_step_handler(message, type_of_event)

    elif sel.lower() == "свободные окна":
        ...

    elif sel.lower() == "выход":
        ...

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
MARK_1 = None
#функция выбора типа события
def type_of_event(message):
    global MARK_1, DATE_EVENT
    sel = message.text
    if sel.lower() == "дата и время":
        MARK_1 = None
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
def my_events(message):
    sel = message.text
    if sel.lower() == "На сегодня":
        pass
    elif sel.lower() == "На выбранный день":
        ...
    elif sel.lower() == "Независимые":
        
        get_indep_events = f"""
        SELECT DependTime, Event
        FROM plans
        WHERE DateEvent IS NULL
        """
        indep_events = db.execute_read_query(connection, get_indep_events)
        
        events = {1: "Срочные и важные: ", 2: "Несрочные и важные: ", 3: "Срочные неважные: ", 4: "Несрочные неважные: "}
        for event in indep_events:
            if event[0] == "срочное важное":
                events[1] += (event[1] + ", ")
            elif event[0] == "несрочное важное":
                events[2] += (event[1] + ", ")
            elif event[0] == "срочное неважное":
                events[3] += (event[1] + ", ")
            elif event[0] == "несрочное неважное":
                events[4] += (event[1] + ", ")
        
        bot.send_message(message.chat.id,
            f"Мои независимые события.\n{events[1]}.\n{events[2]}.\n{events[3]}.\n{events[4]}.")
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
def statistics(message):
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    yesterday = yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
    sunday = now - datetime.timedelta(days=now.isoweekday())
    sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=0)
    now = now.replace(hour=0, minute=0, second=0, microsecond=0)
    depend_ints = {"Срочные важные":0, "Несрочные важные":0, "Срочные неважные":0, "Несрочные неважные":0}
    get_id = f"""
        SELECT 
            id
        FROM
            users
        WHERE
            Login='{LOGIN}' LIMIT 1
        """
    id_user = int(db.execute_read_query(connection, get_id)[0][0])

    #дата и время
    plans_time = f"""
        SELECT
            BeginTime,EndTime
        FROM
            plans
        WHERE
            (idUser={id_user})
        AND
            (BeginTime BETWEEN '{sunday}' AND '{yesterday}')
        AND
            (EndTime BETWEEN '{sunday}' AND '{now}')
        """
    stat_time = db.execute_read_query(connection, plans_time)
    total = now-now
    for s in stat_time:
        total += s[1]-s[0]
        # print(s, '\n')
    str1 = f"Загруженность недели: {(total/(now-sunday)*100).__round__(2)}%"

    #дата
    plans_date = f"""
        SELECT
            DependTime,DateEvent
        FROM
            plans
        WHERE
            (idUser={id_user})
        AND
            (DateEvent BETWEEN '{sunday}' AND '{yesterday}')
        """
    stat_date = db.execute_read_query(connection, plans_date)
    for s in stat_date:
        if s[0] == "срочные важные":
            depend_ints["Срочные важные"] += 1
        if s[0] == "несрочные важные":
            depend_ints["Несрочные важные"] += 1
        if s[0] == "срочные неважные":
            depend_ints["Срочные неважные"] += 1
        if s[0] == "несрочные неважные":
            depend_ints["Несрочные неважные"] += 1
        # print(s, '\n')
    str2 = f"\n\nВсего событий неопределённой длительности за неделю: {len(stat_date)}"
    str22 = ""
    for di in depend_ints.items():
        str22 += f"\n{di[0]}: {di[1]}"
    for k in depend_ints.keys():
        depend_ints[k] = 0
    print("\n")

    #ничего
    plans_nth = f"""
    SELECT
        DependTime
    FROM
        plans
    WHERE
        (idUser={id_user})
    AND
        (DateEvent IS NULL)
    AND
        (BeginTime IS NULL)
    """
    stat_nth = db.execute_read_query(connection, plans_nth)
    for s in stat_nth:
        if s[0] == "срочные важные":
            depend_ints["Срочные важные"] += 1
        if s[0] == "несрочные важные":
            depend_ints["Несрочные важные"] += 1
        if s[0] == "срочные неважные":
            depend_ints["Срочные неважные"] += 1
        if s[0] == "несрочные неважные":
            depend_ints["Несрочные неважные"] += 1
        # print(s, '\n')
    str3 = f"\n\nВсего событий без привязки к дате и времени: {len(stat_nth)}"
    str32 = ""
    for di in depend_ints.items():
        str32 += f"\n{di[0]}: {di[1]}"
    bot.send_message(message.chat.id, str1+str2+str22+str3+str32)
    keyboard(message)
#######################################################################################################################


#######################################################################################################################
# ОБРАБОТКА НАЖАТИЙ INLINE КНОПОК
#######################################################################################################################
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    global RET_DATA, FINISH, MARK_1, DATE_EVENT
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
            else:
                if DATE_EVENT is None:
                    DATE_EVENT = RET_DATA
                    msg = bot.send_message(call.message.chat.id, f"Вы выбрали дату {DATE_EVENT.date()}. Теперь введите название события", reply_markup=None)
                    bot.register_next_step_handler(msg, naming)
                else:
                    FINISH = RET_DATA
                    msg = bot.send_message(call.message.chat.id,
                                           f"Вы выбрали дату {FINISH.date()}. Введите количество дней в промежутке между повторами",
                                           reply_markup=None)
                    bot.register_next_step_handler(msg, day_interval_for_date)

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
#функция, выводящая календарь для начала события или конца события
def depending_from_time(message):
    if START_TIME is None:
        bot.send_message(message.chat.id, "Выберите день начала события",
                         reply_markup=data_calendar.create_calendar(None, None, 1))
    else:
        bot.send_message(message.chat.id, "Выберите день конца события",
                         reply_markup=data_calendar.create_calendar(None, None, START_DATE))


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


#функция фиксирования начала, конца события и самого события
def time_save_event(message):
    global TEXT
    TEXT = message.text
    bot.send_message(message.chat.id, f"Событие '{TEXT}' установлено с {START_DATE} по {END_DATE}")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("да")
    button2 = types.KeyboardButton("нет")
    markup.add(button1,button2)
    bot.send_message(message.chat.id, f"Данное событие циклично?", reply_markup=markup)
    bot.register_next_step_handler(message, looping)


#функция обработки введенного промежутка между повторами
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

        bot.send_message(message.chat.id, f"Все повторы данного события и само событие зафиксированы. Всего их получилось {i}")
        START_TIME, END_TIME, FINISH = None, None, None
        bot.send_message(message.chat.id, 'Хотите получить напоминание о данном событии?')
        bot.register_next_step_handler(message, notification)
    else:
        bot.send_message(message.chat.id, "Вы ввели не натуральное число или большее, чем количество дней между концом события и днем последнего повторения. Повторите попытку")
        bot.register_next_step_handler(message, day_interval)


#функция определения цикличности события
def looping(message):
    global START_TIME, END_TIME, FINISH
    answer = message.text.lower()
    if answer == "да":
        dt = END_DATE + datetime.timedelta(days=1)
        bot.send_message(message.chat.id, "До какого дня нужно повторять событие (включительно)?", reply_markup=data_calendar.create_calendar(None, None, dt))
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
        bot.send_message(message.chat.id, 'Хотите получить напоминание о данном событии?')
        bot.register_next_step_handler(message, notification)
    else:
        bot.send_message(message.chat.id, "Выберите или введите да/нет для продолжения")
        bot.register_next_step_handler(message, looping)


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
    button1 = types.KeyboardButton("Срочное важное")
    button2 = types.KeyboardButton("Несрочное важное")
    button3 = types.KeyboardButton("Срочное неважное")
    button4 = types.KeyboardButton("Несрочное неважное")
    markup.add(button1, button2, button3, button4)
    bot.send_message(message.chat.id, "Выберите категорию события", reply_markup=markup)
    bot.register_next_step_handler(message, name_independent)


#функция наименования события
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


#результирующая функция
def exit_independent(message):
    # ЗДЕСЬ И ВО ВСЕХ ТАКИХ ФУНКЦИЯХ НУЖНО ПРОПИСАТЬ ДЕЙСТВИЯ КОМАНД /START, /HELP И ДРУГИХ!
    text = message.text

    create_event = f"""
    INSERT INTO
      plans (idUser, DependTime, Event)
    VALUES
      ('{ID_USER}', '{CATEGORY}', '{text}')
    """
    db.execute_query(connection, create_event)

    bot.send_message(message.chat.id, "Событие '{}' успешно добавлено в категорию '{}'!".format(text, CATEGORY))
    keyboard(message)
#######################################################################################################################


#######################################################################################################################
# ОБРАБОТКА СОБЫТИЯ, ЗАВИСИМОГО ТОЛЬКО ОТ ДАТЫ
#######################################################################################################################
def depending_from_date(message):
    bot.send_message(message.chat.id, "Выберите дату события", reply_markup=data_calendar.create_calendar(None, None, 1))


#функция определения названия события
def naming(message):
    global NAME
    NAME = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Срочное важное")
    button2 = types.KeyboardButton("Несрочное важное")
    button3 = types.KeyboardButton("Срочное неважное")
    button4 = types.KeyboardButton("Несрочное неважное")
    markup.add(button1, button2, button3, button4)
    bot.send_message(message.chat.id, "Выберите категорию события", reply_markup=markup)
    bot.register_next_step_handler(message, loop_define)


def loop_define(message):
    global TYPE
    TYPE = message.text.lower()
    if TYPE == ("срочное важное" or "несрочное важное" or "срочное неважное" or "несрочное неважное"):
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



#функция определения цикличности
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


#функция добавления всех повторов
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
