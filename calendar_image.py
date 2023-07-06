from PIL import Image, ImageDraw, ImageFont
import calendar, datetime, holidays

def get_image_calendar(dates, year, month):

    width, height = 500, 500
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('arial.ttf', size=30)
    dict_for_month = {"January": "Январь", "February": "Февраль", "March": "Март", "April": "Апрель", "May": "Май",
                      "June":
                          "Июнь", "July": "Июль", "August": "Август", "September": "Сентябрь", "October": "Октябрь",
                      "November": "Ноябрь",
                      "December": "Декабрь"}
    title = dict_for_month[calendar.month_name[month]] + ' ' + str(year)
    title_size = draw.textlength(title, font=font)
    draw.text(((width - 100) // 2, 20), title, font=font, fill='black')

    cal = calendar.monthcalendar(year, month)
    now = datetime.datetime.now()

    cell_width = (width - 40) // 7
    cell_height = (height - 100) // len(cal)
    # рисуем дни недели
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    for i, day in enumerate(days):
        day_width, day_height = draw.textlength(day, font=font), 20
        if day == "СБ" or day == "ВС":
            draw.text((20 + i * cell_width + (cell_width - day_width) // 2, 60), day, font=font, fill="red")
        else:
            draw.text((20 + i * cell_width + (cell_width - day_width) // 2, 60), day, font=font, fill="black")

    Belarus_holidays_list = holidays.BY(years=year)
    bel_holidays = [(i.month, i.day) for i in Belarus_holidays_list]
    hol_dict = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: [], 10: [], 11: [], 12: []}
    for i in hol_dict:
        for j in bel_holidays:
            if i == j[0]:
                hol_dict[i].append(j[1])

    for i, row in enumerate(cal):
        for j, day in enumerate(row):
            if day != 0 and day not in dates:
                day_width, day_height = draw.textlength(str(day), font=font), 20
                if now.year == year and now.month == month and day < now.day:
                    draw.text((20 + j * cell_width + (cell_width - day_width) // 2,
                               100 + i * cell_height + (cell_height - day_height) // 2), str(day), font=font,
                              fill="gray")
                elif row[-1] == day or row[-2] == day or day in hol_dict[month]:
                    draw.text((20 + j * cell_width + (cell_width - day_width) // 2,
                               100 + i * cell_height + (cell_height - day_height) // 2), str(day), font=font,
                              fill="red")
                else:
                    draw.text((20 + j * cell_width + (cell_width - day_width) // 2,
                               100 + i * cell_height + (cell_height - day_height) // 2), str(day), font=font,
                              fill="black")
    # сохраняем изображение в файл
    img.save('calendar.png')