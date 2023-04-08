import telebot
from telebot import types
from config import BOT_TOKEN, PROVIDER_PAYMENT_TOKEN, ADMIN_ID
import os
from datetime import datetime

admin_id_list = ADMIN_ID
bot = telebot.TeleBot(BOT_TOKEN)
temp_admin_adding = ""
FIRST_FILE_ID_OFFSET = int(4)
pics_upload = bool(False)

#region helpers
def gen_purchase_markup() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("Купить"))
    markup.add(types.KeyboardButton("Вернуться к выбору презентаций"))
    markup.add(types.KeyboardButton("Вернуться в начало(?)"))
    return markup

def find_key_by_name(value) -> str:
    with open('config_ready_names.txt', 'r', encoding='utf-8') as file:
        for line in file:
            temp_ready_name_list = line.strip().split("|")
            if temp_ready_name_list[1] == value:
                return temp_ready_name_list[0]
            
def read_config(key) -> list[str]:
    with open('config_ready_names.txt', 'r', encoding='utf-8') as file:
        for line in file:
            temp_ready_name_list = line.strip().split("|")
            if temp_ready_name_list[0] == key:
                return temp_ready_name_list
        
def get_last_index() -> int:
    with open('config_ready_names.txt', 'r', encoding='utf-8') as file:
        return int(file.readlines()[-1].split("|")[0])
#endregion

#region admin
@bot.message_handler(commands=["admin_panel"])
def admin(m):
    if m.from_user.id in admin_id_list:
        global temp_admin_adding
        temp_admin_adding = ""
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=1)
        markup.add(types.KeyboardButton("Добавить готовую презентацию"), types.KeyboardButton("Удалить презентацию"), types.KeyboardButton("Просмотреть историю заказов"))
        admin_msg = bot.send_message(m.chat.id, "Выберите необходимую команду", reply_markup=markup)
        bot.register_next_step_handler(admin_msg, handle_admin_choice)
    else:
        bot.send_message(m.chat.id, "У вас нет доступа для выполнения данной комманды")

@bot.message_handler(commands=["admin_exit"])
def admin_exit(m):
    pass

def handle_admin_choice(m):
    if m.text == "Добавить готовую презентацию":
        add_presentation(m)
    elif m.text == "Удалить презентацию":
        remove_presentation(m)
    else:
        pass

def add_presentation(m):
    new_name_msg = bot.send_message(m.chat.id, "Отправьте название презентации, оно будет использовано в кнопках выбора для клиента, названии товара при покупке и в качестве имени отправленного файла:")
    bot.register_next_step_handler(new_name_msg, save_new_name)

def save_new_name(m):
    global temp_admin_adding
    temp_admin_adding = m.text + "|"
    new_caption_msg = bot.send_message(m.chat.id, "Теперь отправьте описание для презентации, оно будет использовано в предпоказе товара, в качестве описания к фотографиям")
    bot.register_next_step_handler(new_caption_msg, save_new_caption)

def save_new_caption(m):
    global temp_admin_adding
    temp_admin_adding = temp_admin_adding + m.text + "|"
    new_price_msg = bot.send_message(m.chat.id, "Отправьте цену презентации в рублях, одним числом:")
    bot.register_next_step_handler(new_price_msg, save_new_price)

def save_new_price(m):
    global temp_admin_adding, pics_upload
    price = int(m.text) * 100 # в копейках для sendInvoice
    temp_admin_adding = temp_admin_adding + str(price) + "|"
    new_pics_msg = bot.send_message(m.chat.id, "Отправьте от 1 до 10 фотографий, которые будут показаны клиенту в предпоказе товара. Вы можете отправить фотографии как в одном сообщении, так и по отдельности, по завершению загрузки кликните на команду /upload_done")
    pics_upload = True

@bot.message_handler(commands=['upload_done'])
def upload_done(m):
    global pics_upload
    if pics_upload:
        pics_upload = False
        save_new_presentation(m)

@bot.message_handler(content_types=['photo'])
def add_new_pic(m):
    global pics_upload
    if pics_upload:
        global temp_admin_adding
        if len(temp_admin_adding.strip().split("|")) < 13:
            temp_admin_adding = temp_admin_adding + m.photo[-1].file_id + "|"
        else:
            bot.send_message(m.chat.id, "Вы пытаетесь загрузить более 10 фотографий, воспользуйтесь командой /upload_done или начните добавление презентации заново с помощью команды /admin_panel")

def save_new_presentation(m):
    global temp_admin_adding
    temp_admin_adding = temp_admin_adding[:-1]
    temp_admin_adding = "\n" + str(get_last_index() + 1) + "|" + temp_admin_adding
    with open('config_ready_names.txt', 'a', encoding='utf-8') as file:
        file.write(temp_admin_adding)
    bot.send_message(m.chat.id, "Презентация успешно добавлена!")
    admin(m)

def remove_presentation(m):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    with open('config_ready_names.txt', 'r', encoding='utf-8') as file:
        for line in file:
            temp_ready_name_list = line.strip().split("|")
            markup.add(types.KeyboardButton(temp_ready_name_list[1]))
    markup.add(types.KeyboardButton("Назад"))
    remove_choice_msg = bot.send_message(m.chat.id, "Выберите презентацию для удаления:", reply_markup=markup)
    bot.register_next_step_handler(remove_choice_msg, handle_remove_choice)

def handle_remove_choice(m):
    if m.text == "Назад":
        admin(m)
    else:
        with open('config_ready_names.txt', 'r', encoding='utf-8') as input:
            with open('temp.txt', 'w', encoding='utf-8') as output:
                for line in input:
                    temp_ready_name_list = line.strip().split("|")
                    if temp_ready_name_list[1] != m.text:
                        output.write(line)
        os.replace('temp.txt', 'config_ready_names.txt')
        bot.send_message(m.chat.id, f"Презентация \"{m.text}\" успешно удалена!")
        admin(m)
        
#endregion

@bot.message_handler(commands=["start", "order"])
def start(m):
    bot.send_message(m.chat.id, "С помощью данного бота вы можете заказать тематические презентации по математике")
    get_choice(m)

@bot.message_handler(commands=["help"])
def help(m):
    bot.send_message(m.chat.id, "/order - перейти к новому заказу")

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
    with open('config_ready_names.txt', 'r', encoding='utf-8') as file:
        for line in file:
            temp_ready_name_list = line.strip().split("|")
            markup.add(types.KeyboardButton(temp_ready_name_list[1]))
    ready_choice = bot.send_message(m.chat.id, "Выберите тематику презентации для предварительного просмотра:", reply_markup=markup)
    bot.register_next_step_handler(ready_choice, show_ready_presentation)
    
    '''
    how to find out file_id:
    test = bot.send_media_group(m.chat.id, media=[types.InputMediaPhoto(open(image, 'rb'), caption="Презентация \"Тачки\""), types.InputMediaPhoto(open(image, 'rb'))])
    print(list(i.file_id for i in test[0].photo))
    '''

def order(m):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("Назад"))
    order_msg = bot.send_message(m.chat.id, "Вы можете запросить личную консультацию для создания презентации лично для вас, для начала отправьте нам краткую информацию о заказе", reply_markup=markup)
    bot.register_next_step_handler(order_msg, handle_order)

def handle_order(m):
    if m.text == "Назад":
        get_choice(m)
    else:
        for admin_id in admin_id_list:
            bot.send_message(admin_id, f"Получен новый заказ от {m.from_user.first_name}, @{m.from_user.username}: {m.text}")
        with open('orders.txt', 'a', encoding='utf-8') as file:
            file.write(f"\n{datetime.utcnow()}|@{{m.from_user.username}}|{m.from_user.first_name}|{m.text}")
        bot.send_message(m.chat.id, "Заказ успешно оформлен, мы скоро свяжемся с вами для обсуждения деталей!", reply_markup=types.ReplyKeyboardRemove())
        redirect(m)

def redirect(m):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("Перейти к выбору"))
    redirect_msg = bot.send_message(m.chat.id, "Желаете приобрести следующую(?) презентацию?", reply_markup=markup)
    bot.register_next_step_handler(redirect_msg, handle_redirect)

def handle_redirect(m):
    if m.text == "Перейти к выбору":
        get_choice(m)

def show_ready_presentation(m):
    key = find_key_by_name(m.text)
    presentation_preview_images = []
    temp_list = read_config(key)
    for i in range(FIRST_FILE_ID_OFFSET, len(temp_list)):
        presentation_preview_images.append(types.InputMediaPhoto(temp_list[i], caption=temp_list[2] if i == FIRST_FILE_ID_OFFSET else None))
    bot.send_media_group(m.chat.id, media=presentation_preview_images)
    purchase_choice = bot.send_message(m.chat.id, "Стоимость данной презентации 100 рублев", reply_markup=gen_purchase_markup())
    bot.register_next_step_handler(purchase_choice, purchase_callback, key)

#region payments
def purchase_callback(m, key):
    if m.text == "Купить":
        temp_list = read_config(key)
        bot.send_invoice(
            m.chat.id,
            title=temp_list[1],
            description=temp_list[1],
            invoice_payload=key,
            provider_token=PROVIDER_PAYMENT_TOKEN,
            currency="rub",
            prices=[types.LabeledPrice(label=temp_list[1], amount=int(temp_list[3]))],
            is_flexible=False
        )
    elif m.text == "Вернуться к выбору презентаций":
        build_ready_choices(m)
    elif m.text == "Вернуться в начало(?)":
        get_choice(m)

@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_payment(m):
    key = m.successful_payment.invoice_payload
    bot.send_message(m.chat.id, "Оплата прошла успешно, спасибо за покупку!")
    bot.send_document(m.chat.id, document=open(f"presentations\\{key}.pptx", 'rb'))
    redirect(m)
#endregion

if __name__ == '__main__':
    bot.infinity_polling()