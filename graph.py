import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt


def photo(message):
    x = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
    y = [8, 8, 10, 4, 6, 13, 14]
    plt.bar(x, y)
    plt.xlabel('День недели')
    plt.ylabel('Количество поставлненных задач')
    plt.title('12.04.2023-19.04.2023')
    plt.savefig('saved_figure.jpg')
    bot.send_photo(message.chat.id, photo=open('saved_figure.jpg', 'rb'))