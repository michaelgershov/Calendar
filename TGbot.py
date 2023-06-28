import telebot
from telebot import types

bot = telebot.TeleBot('6058933003:AAG5Ti0fmydE9xfQYzPYv35pUM4jPOt7LY0');

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}! Я бот-календарь!')
    bot.send_message(message.chat.id, r'Для регистрации введите пароль, содержащий не менее 8 символов  и состоящий только из букв и цифр.')

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
    markup.add(button1, button2, button3, button4,button5, button6)
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