import telebot
from telebot import types
from config import BOT_TOKEN, PROVIDER_PAYMENT_TOKEN, ADMIN_ID
import os
from datetime import datetime, timedelta

admin_id_list = ADMIN_ID
bot = telebot.TeleBot(BOT_TOKEN)
temp_admin_adding = ""
FIRST_FILE_ID_OFFSET = int(4)



#region main commands
@bot.message_handler(commands=["start"])
def start_handler(m: types.Message):
    with open('users_chat_id.txt', 'r+') as file:
        if str(m.chat.id) not in file.read():
            file.write(str(m.chat.id) + "\n")
    bot.send_message(m.chat.id, "С помощью данного бота вы можете заказать тематические презентации по математике")
    get_choice(m)

@bot.message_handler(commands=["order"])
def order_handler(m: types.Message):
    order(m)

@bot.message_handler(commands=["help"])
def help(m: types.Message):
    bot.send_message(m.chat.id, "/order - перейти к новому заказу")
#endregion

#region helpers
def gen_purchase_markup() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("Купить"))
    markup.add(types.KeyboardButton("Вернуться к выбору презентаций"))
    markup.add(types.KeyboardButton("Вернуться в начало"))
    return markup

def find_key_by_name(value) -> str:
    with open('config_ready_names.txt', 'r', encoding='utf-8') as file:
        for line in file:
            temp_ready_name_list = line.strip().split("|")
            if temp_ready_name_list[1] == value:
                return temp_ready_name_list[0]
            
def find_name_by_key(key) -> str:
    with open('config_ready_names.txt', 'r', encoding='utf-8') as file:
        for line in file:
            temp_ready_name_list = line.strip().split("|")
            if temp_ready_name_list[0] == key:
                return temp_ready_name_list[1]
            
def read_config(key) -> list[str]:
    with open('config_ready_names.txt', 'r', encoding='utf-8') as file:
        for line in file:
            temp_ready_name_list = line.strip().split("|")
            if temp_ready_name_list[0] == key:
                return temp_ready_name_list
        
def get_last_index() -> int:
    if os.stat('config_ready_names.txt').st_size == 0:
        return 0
    with open('config_ready_names.txt', 'r', encoding='utf-8') as file:
        return int(file.readlines()[-1].split("|")[0])
#endregion

#region admin
@bot.message_handler(commands=["admin"])
def admin(m: types.Message):
    if m.from_user.id in admin_id_list:
        global temp_admin_adding
        temp_admin_adding = ""
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=1)
        markup.add(types.KeyboardButton("Добавить готовую презентацию"), types.KeyboardButton("Удалить презентацию"), types.KeyboardButton("Просмотреть историю заказов"), types.KeyboardButton("Назад"))
        admin_msg = bot.send_message(m.chat.id, "Выберите необходимую команду", reply_markup=markup)
        bot.register_next_step_handler(admin_msg, handle_admin_choice)
    else:
        bot.send_message(m.chat.id, "У вас нет доступа для выполнения данной комманды")

def handle_admin_choice(m: types.Message):
    if m.text == "Добавить готовую презентацию":
        add_presentation(m)
    elif m.text == "Удалить презентацию":
        remove_presentation(m)
    elif m.text == "Просмотреть историю заказов":
        show_history(m)
    elif m.text == "Назад":
        get_choice(m)

def add_presentation(m: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Отмена"))
    new_name_msg = bot.send_message(m.chat.id, "Отправьте *название* презентации, оно будет использовано в кнопках выбора для клиента, названии товара при покупке и в качестве имени отправленного файла:", parse_mode="MarkdownV2", reply_markup=markup)
    bot.register_next_step_handler(new_name_msg, save_new_name)

def save_new_name(m: types.Message):
    if m.text == "Отмена":
        admin(m)
    else:
        global temp_admin_adding
        temp_admin_adding = m.text + "|"
        new_caption_msg = bot.send_message(m.chat.id, "Теперь отправьте *описание* для презентации, оно будет использовано в предпоказе товара, в качестве описания к фотографиям", parse_mode="MarkdownV2")
        bot.register_next_step_handler(new_caption_msg, save_new_caption)

def save_new_caption(m: types.Message):
    if m.text == "Отмена":
        admin(m)
    else:
        global temp_admin_adding
        temp_admin_adding = temp_admin_adding + m.text + "|"
        new_price_msg = bot.send_message(m.chat.id, "Отправьте *цену* презентации в рублях, *одним числом*:", parse_mode="MarkdownV2")
        bot.register_next_step_handler(new_price_msg, save_new_price)

def save_new_price(m: types.Message):
    if m.text == "Отмена":
        admin(m)
    else:
        global temp_admin_adding
        if m.text.isdigit():
            price = int(m.text) * 100 # в копейках для sendInvoice
            temp_admin_adding = temp_admin_adding + str(price) + "|"
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("Завершить загрузку"), types.KeyboardButton("Отмена"))
            new_pics_msg = bot.send_message(m.chat.id, "Отправьте *от 1 до 10* фотографий, которые будут показаны клиенту в предпоказе товара\. Вы можете отправить фотографии как в одном сообщении, так и по отдельности", parse_mode="MarkdownV2", reply_markup=markup)
            bot.register_next_step_handler(new_pics_msg, photo)
        else:
            bot.send_message(m.chat.id, "Введите *число*\!", parse_mode="MarkdownV2")
            bot.register_next_step_handler(m, save_new_price)

def photo(m: types.Message):
    global temp_admin_adding
    if m.photo is not None:
        if len(temp_admin_adding.strip().split("|")) < 14:
            temp_admin_adding = temp_admin_adding + m.photo[-1].file_id + "|"
            bot.register_next_step_handler(m, photo)
        else:
            bot.send_message(m.chat.id, "Вы пытаетесь загрузить более 10 фотографий")
    elif m.text == "Завершить загрузку":
        if len(temp_admin_adding.split("|")) < 5:
            bot.send_message(m.chat.id, "Вы не прикрепили ни одной фотографии, попробуйте еще раз!")
            bot.register_next_step_handler(m, photo)
        else:
            save_new_presentation(m)
    elif m.text == "Отмена":
        admin(m)


# @bot.message_handler(regexp="Завершить загрузку")
# def upload_done(m: types.Message):
#     global pics_upload
#     if pics_upload:
#         pics_upload = False
#         save_new_presentation(m)

# @bot.message_handler(content_types=['photo'])
# def add_new_pic(m: types.Message):
#     global pics_upload
#     if pics_upload:
#         global temp_admin_adding
#         if len(temp_admin_adding.strip().split("|")) < 14:
#             temp_admin_adding = temp_admin_adding + m.photo[-1].file_id + "|"
#         else:
#             bot.send_message(m.chat.id, "Вы пытаетесь загрузить более 10 фотографий, воспользуйтесь командой /upload_done или начните добавление презентации заново с помощью команды /admin_panel")

def save_new_presentation(m: types.Message):
    global temp_admin_adding
    temp_admin_adding = temp_admin_adding[:-1]
    temp_admin_adding = str(get_last_index() + 1) + "|" + temp_admin_adding + "\n"
    with open('config_ready_names.txt', 'a', encoding='utf-8') as file:
        file.write(temp_admin_adding)
    bot.send_message(m.chat.id, "Презентация успешно добавлена!", reply_markup=types.ReplyKeyboardRemove())
    admin(m)

def remove_presentation(m: types.Message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    with open('config_ready_names.txt', 'r', encoding='utf-8') as file:
        for line in file:
            temp_ready_name_list = line.strip().split("|")
            markup.add(types.KeyboardButton(temp_ready_name_list[1]))
    markup.add(types.KeyboardButton("Назад"))
    remove_choice_msg = bot.send_message(m.chat.id, "Выберите презентацию для удаления:", reply_markup=markup)
    bot.register_next_step_handler(remove_choice_msg, handle_remove_choice)

def handle_remove_choice(m: types.Message):
    if m.text == "Назад":
        admin(m)
    else:
        with open('config_ready_names.txt', 'r', encoding='utf-8') as reader:
            with open('temp.txt', 'w', encoding='utf-8') as writer:
                for line in reader:
                    temp_ready_name_list = line.strip().split("|")
                    if temp_ready_name_list[1] != m.text:
                        writer.write(line)
        os.replace('temp.txt', 'config_ready_names.txt')
        bot.send_message(m.chat.id, f"Презентация \"{m.text}\" успешно удалена!")
        admin(m)

def show_history(m: types.Message):
    message = ""
    with open('orders.txt', 'r', encoding='utf-8') as file:
        for line in file:
            line_split = line.strip().split("|")
            if line_split:
                message = message + datetime.strftime((datetime.strptime(line_split[0], "%Y-%d-%m %H:%M:%S.%f") + timedelta(hours=5)), "%d.%m.%Y %H:%M:%S") + f", {line_split[2]} ({line_split[1]}). Комментарий: {line_split[3]}\n\n"
    if message:
        bot.send_message(m.chat.id, message.strip())
    else:
        bot.send_message(m.chat.id, "Заказов пока что нет")
        
#endregion

def get_choice(m: types.Message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("Выбрать из готовых"), types.KeyboardButton("Сделать заказ"))
    choice = bot.send_message(m.chat.id, "Вы можете выбрать презентацию из имеющихся либо оформить индивидуальный заказ", reply_markup=markup)
    bot.register_next_step_handler(choice, handle_choice)

def handle_choice(m: types.Message):
    if m.text == "Выбрать из готовых":
        build_ready_choices(m)
    elif m.text == "Сделать заказ":
        order(m)
    elif m.text == "/admin":
        admin(m)
    elif m.text == "/start":
        start_handler(m)

def build_ready_choices(m: types.Message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    with open('config_ready_names.txt', 'r', encoding='utf-8') as file:
        for line in file:
            temp_ready_name_list = line.strip().split("|")
            markup.add(types.KeyboardButton(temp_ready_name_list[1]))
    markup.add(types.KeyboardButton("Назад"))
    ready_choice = bot.send_message(m.chat.id, "Выберите тематику презентации для предварительного просмотра:", reply_markup=markup)
    bot.register_next_step_handler(ready_choice, show_ready_presentation)
    
    '''
    how to find out file_id:
    test = bot.send_media_group(m.chat.id, media=[types.InputMediaPhoto(open(image, 'rb'), caption="Презентация \"Тачки\""), types.InputMediaPhoto(open(image, 'rb'))])
    print(list(i.file_id for i in test[0].photo))
    '''

def order(m: types.Message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("Назад"))
    order_msg = bot.send_message(m.chat.id, "Вы можете запросить личную консультацию для создания презентации лично для вас, для начала отправьте нам краткую информацию о заказе", reply_markup=markup)
    bot.register_next_step_handler(order_msg, handle_order)

def handle_order(m: types.Message):
    if m.text == "Назад":
        get_choice(m)
    else:
        for admin_id in admin_id_list:
            bot.send_message(admin_id, f"Получен новый заказ от {m.from_user.first_name}, @{m.from_user.username}: {m.text}")
        with open('orders.txt', 'a', encoding='utf-8') as file:
            file.write(f"{datetime.utcnow()}|@{m.from_user.username}|{m.from_user.first_name}|{m.text}\n")
        bot.send_message(m.chat.id, "Заказ успешно оформлен, мы скоро свяжемся с вами для обсуждения деталей!", reply_markup=types.ReplyKeyboardRemove())
        redirect(m)

def redirect(m: types.Message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("Перейти к выбору"))
    redirect_msg = bot.send_message(m.chat.id, "Желаете приобрести следующую(?) презентацию?", reply_markup=markup)
    bot.register_next_step_handler(redirect_msg, handle_redirect)

def handle_redirect(m: types.Message):
    if m.text == "Перейти к выбору":
        get_choice(m)

def show_ready_presentation(m: types.Message):
    if m.text == "Назад":
        get_choice(m)
        return
    key = find_key_by_name(m.text)
    presentation_preview_images = []
    temp_list = read_config(key)
    for i in range(FIRST_FILE_ID_OFFSET, len(temp_list)):
        presentation_preview_images.append(types.InputMediaPhoto(temp_list[i], caption=temp_list[2] if i == FIRST_FILE_ID_OFFSET else None))
    bot.send_media_group(m.chat.id, media=presentation_preview_images)
    price = int(int(temp_list[3]) / 100) # в копейках
    formatted_currency = str("ь") if price % 10 == 1 else str("я") if price % 10 >= 2 and price % 10 <= 4 else str("ей")
    purchase_choice = bot.send_message(m.chat.id, f"Стоимость данной презентации {price} рубл{formatted_currency}", reply_markup=gen_purchase_markup())
    bot.register_next_step_handler(purchase_choice, purchase_callback, key)

#region payments
def purchase_callback(m, key):
    if m.text == "Купить":
        temp_list = read_config(key)
        bot.send_invoice(
            m.chat.id,
            title=temp_list[1],
            description=temp_list[1],
            invoice_payload=f'{key}_{m.chat.id}',
            provider_token=PROVIDER_PAYMENT_TOKEN,
            currency="rub",
            prices=[types.LabeledPrice(label=temp_list[1], amount=int(temp_list[3]))],
            is_flexible=False
        )
    elif m.text == "Вернуться к выбору презентаций":
        build_ready_choices(m)
    elif m.text == "Вернуться в начало":
        get_choice(m)

@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_payment(m: types.Message):
    key = m.successful_payment.invoice_payload[0]
    title = f'{find_name_by_key(key)}.pptx'
    bot.send_message(m.chat.id, "Оплата прошла успешно, спасибо за покупку!")
    bot.send_document(m.chat.id, document=open(f"presentations\\{key}.pptx", 'rb'), visible_file_name=title)
    redirect(m)
#endregion

if __name__ == '__main__':
    bot.infinity_polling()