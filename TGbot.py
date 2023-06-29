import telebot
from telebot import types

bot = telebot.TeleBot('6058933003:AAG5Ti0fmydE9xfQYzPYv35pUM4jPOt7LY0');


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}! Я бот-календарь!')
    bot.send_message(message.chat.id,
                     r'Для регистрации введите пароль, содержащий не менее 8 символов  и состоящий только из букв и цифр.')


@bot.message_handler(commands=["creevent"])
def send_calendar(message):
    bot.send_message(message.chat.id, "Выберите день", reply_markup=data_calendar.create_calendar())


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    global ret_data
    ret_data = None
    (action, year, month, day) = data_calendar.separate_callback_data(call.data)
    curr = datetime.datetime(int(year), int(month), 1)
    if action == "Ничего":
        bot.answer_callback_query(callback_query_id= call.id)
    elif action == "День":
        ret_data = datetime.datetime(int(year), int(month), int(day))
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(call.message.chat.id, f"Вы выбрали {ret_data}")
        bot.send_message(call.message.chat.id, "Введите нужное время, разделив часы и минуты знаком ':'")
    elif action == "Пред-месяц":
        pre = curr - datetime.timedelta(days=1)
        new_keyboard = data_calendar.create_calendar(int(pre.year), int(pre.month))
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=new_keyboard)
    elif action == "След-месяц":
        ne = curr + datetime.timedelta(days=31)
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=data_calendar.create_calendar(int(ne.year), int(ne.month)))
    else:
        bot.send_message(call.message.chat.id, "Что-то не так!")


@bot.message_handler(content_types=["text"])
def password(message):
    password = message.text
    if len(password) < 8:
        bot.send_message(message.chat.id, 'Ваш пароль содержит менее 8 символов! Пожалуйста, повторите попытку')
    elif password.isalnum() == False:
        bot.send_message(message.chat.id, 'Некорректный пароль! Пожалуйста, повторите попытку!')
    else:
        bot.send_message(message.chat.id, 'Отлично! Ваш пароль сохранен! Теперь Вам доступны все опции!')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Календарь на месяц")
        button2 = types.KeyboardButton('Дела на сегодня')
        button3 = types.KeyboardButton("Статистика за неделю")
        button4 = types.KeyboardButton("Добавить событие")
        button5 = types.KeyboardButton("Найти свободное окно")
        button6 = types.KeyboardButton("Задачи с приоритетом")
        markup.add(button1, button2, button3, button4, button5, button6)
        bot.send_message(message.from_user.id, "Выберите нужную опцию", reply_markup=markup)


@bot.message_handler(commands=['option'])
def option(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Календарь на месяц")
    button2 = types.KeyboardButton('Дела на сегодня')
    button3 = types.KeyboardButton("Статистика")
    button4 = types.KeyboardButton("Добавить событие")
    button5 = types.KeyboardButton("Найти свободное окно")
    button6 = types.KeyboardButton("Задачи с приоритетом")
    markup.add(button1, button2, button3, button4, button5, button6)
    bot.send_message(message.from_user.id, "Выберите нужную опцию", reply_markup=markup)


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.from_user.id, 'Список всех доступных команд: ')


bot.set_my_commands([
    telebot.types.BotCommand("/start", "Перезапуск бота"),
    telebot.types.BotCommand("/help", "Помощь"),
    telebot.types.BotCommand("/option", 'Доступные опции'),
    telebot.types.BotCommand("/settings", "Изменить логин или пароль")
])

bot.infinity_polling()
