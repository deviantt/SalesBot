import telebot
from telebot import types
from config import BOT_TOKEN, PROVIDER_PAYMENT_TOKEN, ADMIN_ID


admin_id = ADMIN_ID
bot = telebot.TeleBot(BOT_TOKEN)
ready_names = {
    "shrek": "Презентация \"Шрек\" на тему лыжа диода",
    "cars": "Презентация \"Тачки\" на тему быстрое преобразование Фурье"
}
ready_captions = {
    "shrek": "Презентация \"Шрек\" на тему лыжа диода",
    "cars" : "Презентация \"Тачки\" на тему быстрое преобразование Фурье"
}
ready_pics_id = {
    "shrek": ["AgACAgIAAxkDAAObZCmo1RzegKHfmSSLQjeICQKU23YAAuTOMRtr41BJ2j9Plgw_i1wBAAMCAAN5AAMvBA", "AgACAgIAAxkDAAObZCmo1RzegKHfmSSLQjeICQKU23YAAuTOMRtr41BJ2j9Plgw_i1wBAAMCAAN5AAMvBA", "AgACAgIAAxkDAAObZCmo1RzegKHfmSSLQjeICQKU23YAAuTOMRtr41BJ2j9Plgw_i1wBAAMCAAN5AAMvBA"],
    "cars": ["AgACAgIAAxkDAAOpZCmp6EBejp_-SbaMaTrg96SWPwYAAsvOMRtr41BJHwmmzcMi-pQBAAMCAAN4AAMvBA", "AgACAgIAAxkDAAOpZCmp6EBejp_-SbaMaTrg96SWPwYAAsvOMRtr41BJHwmmzcMi-pQBAAMCAAN4AAMvBA", "AgACAgIAAxkDAAOpZCmp6EBejp_-SbaMaTrg96SWPwYAAsvOMRtr41BJHwmmzcMi-pQBAAMCAAN4AAMvBA"]
}
ready_prices = {
    "shrek": types.LabeledPrice(label="Презентация \"Шрек\"", amount=8160),
    "cars": types.LabeledPrice(label="Презентация \"Тачки\"", amount=8160)
}


def gen_purchase_markup() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("Купить"))
    markup.add(types.KeyboardButton("Вернуться к выбору презентаций"))
    markup.add(types.KeyboardButton("Вернуться в начало(?)"))
    return markup

def find_key_by_value(value):
    for k, v in ready_names.items():
        if v == value:
            return k

@bot.message_handler(commands=["start", "order"])
def start(m):
    bot.send_message(m.chat.id, "С помощью данного бота вы можете заказать тематические презентации по математике")
    get_choice(m)

@bot.message_handler(commands=["help"])
def help(m):
    bot.send_message(m.chat.id, "/order - перейти к новому заказу")

@bot.message_handler(commands=["admin_panel"])
def admin(m):
    if m.from_user.id in admin_id:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton("Добавить презентацию"), types.KeyboardButton("Удалить презентацию"), types.KeyboardButton("Просмотреть историю заказов"))
        admin_msg = bot.send_message(m.chat.id, "Выберите необходимую команду", reply_markup=markup)
        bot.register_next_step_handler(admin_msg, handle_admin_choice)
    else:
        bot.send_message(m.chat.id, "У вас нет доступа для выполнения данной комманды")

def handle_admin_choice(m):
    pass

def get_choice(m):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("Выбрать из готовых"), types.KeyboardButton("Сделать заказ"))
    choice = bot.send_message(m.chat.id, "Вы можете выбрать презентацию из имеющихся либо оформить индивидуальный заказ", reply_markup=markup)
    bot.register_next_step_handler(choice, handle_choice)

def handle_choice(m):
    if m.text == "Выбрать из готовых":
        build_ready_choices(m)
    elif m.text == "Сделать заказ":
        order(m)

def build_ready_choices(m):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for ready_presentation in ready_names.values():
        markup.add(types.KeyboardButton(ready_presentation))
    ready_choice = bot.send_message(m.chat.id, "Выберите тематику презентации для предварительного просмотра:", reply_markup=markup)
    bot.register_next_step_handler(ready_choice, show_ready_presentation)
    
    '''
    How to find out file_id:
    test = bot.send_media_group(m.chat.id, media=[types.InputMediaPhoto(open(image, 'rb'), caption="Презентация \"Тачки\""), types.InputMediaPhoto(open(image, 'rb'))])
    print(list(i.file_id for i in test[0].photo))
    '''

def order(m):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("Заказать!"))
    order_msg = bot.send_message(m.chat.id, "Вы можете запросить личную консультацию для создания презентации лично для вас", reply_markup=markup)
    bot.register_next_step_handler(order_msg, process_order)

def process_order(m):
    bot.send_message(admin_id[0], f"Получен новый заказ от {m.from_user.first_name}, @{m.from_user.username}")
    bot.send_message(m.chat.id, "Заказ успешно оформлен, в течение дня свяжемся с вами для обкашливания вопросов", reply_markup=types.ReplyKeyboardRemove())
    redirect(m)

def redirect(m):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("Перейти к выбору"))
    redirect_msg = bot.send_message(m.chat.id, "Желаете приобрести следующую(?) презентацию?", reply_markup=markup)
    bot.register_next_step_handler(redirect_msg, process_redirect)

def process_redirect(m):
    if m.text == "Перейти к выбору":
        get_choice(m)

def show_ready_presentation(m):
    if m.text in ready_names.values():
        key = find_key_by_value(m.text)
        presentation_preview_images = []
        for i in range(len(ready_pics_id[key])):
            presentation_preview_images.append(types.InputMediaPhoto(ready_pics_id[key][i], caption=ready_captions[key] if i == 0 else None))
        bot.send_media_group(m.chat.id, media=presentation_preview_images)
        purchase_choice = bot.send_message(m.chat.id, "Стоимость данной презентации 100 рублев", reply_markup=gen_purchase_markup())
        bot.register_next_step_handler(purchase_choice, purchase_callback, key)

def purchase_callback(m, key):
    if m.text == "Купить":
        bot.send_invoice(
            m.chat.id,
            title=ready_names[key],
            description=ready_captions[key],
            invoice_payload=key,
            provider_token=PROVIDER_PAYMENT_TOKEN,
            currency="rub",
            prices=[ready_prices[key]],
            is_flexible=False
        )
    elif m.text == "Вернуться к выбору презентаций":
        build_ready_choices(m)
    elif m.text == "Вернуться в начало(?)":
        get_choice(m)

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def process_payment(m):
    key = m.successful_payment.invoice_payload
    bot.send_message(m.chat.id, "Оплата прошла успешно, спасибо за покупку!")
    bot.send_document(m.chat.id, document=open(f"presentations\\{key}.pptx", 'rb'))
    redirect(m)


if __name__ == '__main__':
    bot.infinity_polling()