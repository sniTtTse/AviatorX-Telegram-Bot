import random
import threading
import time
import json
import telebot
from telebot import types

# Ініціалізація бота
API_TOKEN = '7521035909:AAG6m07C1qV1lTtsV6_iy0jFu6tSWdONTf8'
bot = telebot.TeleBot(API_TOKEN)

# Ініціація другого бота
OTHER_BOT_TOKEN = '7777584488:AAFRnBk5j46DZVo6TJz2kBL_9XiU19Nfh2M'
other_bot = telebot.TeleBot(OTHER_BOT_TOKEN)

# Зняття вебхука для обох ботів
bot.remove_webhook()
other_bot.remove_webhook()

# Файл для збереження даних користувачів
DATA_FILE = 'user_data.json'

# Дані користувачів
users = {}

# Початкові налаштування гри
initial_bets = [10, 20, 50, 100, 200, 500]
initial_balance = 0  # Початковий баланс 0 грн
game_running = False
coefficient = 1.00

def load_user_data():
    global users
    try:
        with open(DATA_FILE, 'r') as file:
            users = json.load(file)
    except FileNotFoundError:
        users = {}

def save_user_data():
    with open(DATA_FILE, 'w') as file:
        json.dump(users, file)

# Генерація унікального коментаря
def generate_unique_comment():
    return ''.join(random.choices('0123456789', k=10))

# Функція для скидання змінних гри
def reset_game():
    global game_running, coefficient
    game_running = False
    coefficient = 1.00

# Функція для симуляції польоту літака
def start_game(user_id):
    global game_running, coefficient
    game_running = True
    coefficient = 1.00
    start_time = time.time()

    # Генеруємо випадковий коефіцієнт залежно від шансів
    random_value = random.random()
    if random_value <= 0.10:
        max_coefficient = random.uniform(10.00, 100.00)  # 10% шанс на коефіцієнт більше 10х
    elif random_value <= 0.30:
        max_coefficient = random.uniform(5.00, 10.00)  # 20% шанс на коефіцієнт більше 5х
    elif random_value <= 0.70:
        max_coefficient = random.uniform(2.00, 5.00)  # 40% шанс на коефіцієнт більше 2х
    else:
        max_coefficient = random.uniform(1.00, 2.00)  # 30% шанс на коефіцієнт до 2х

    # Надсилання початкового повідомлення з коефіцієнтом
    message = bot.send_message(user_id, f'✈️ Поточний коефіцієнт: {coefficient:.2f}x')

    while game_running:
        time.sleep(0.5)  # Сповільнити зміну коефіцієнту
        elapsed_time = time.time() - start_time
        coefficient = 1.00 + (elapsed_time / 4) + random.random() / 10  # Збільшення коефіцієнта з часом

        if coefficient >= max_coefficient:
            game_running = False

        # Редагування повідомлення з коефіцієнтом
        bot.edit_message_text(chat_id=user_id, message_id=message.message_id, text=f'✈️ Поточний коефіцієнт: {coefficient:.2f}x')

        # Перевірка на автоматичне зняття
        for bet_index, bet_data in enumerate(users[user_id]['bets']):
            if bet_data['auto_cashout'] and coefficient >= bet_data['auto_cashout']:
                winnings = bet_data['bet'] * coefficient
                users[user_id]['balance'] += winnings
                bot.send_message(user_id, f'Автоматичне зняття для ставки {bet_index + 1} при {coefficient:.2f}x. Ви виграли {winnings:.2f} грн. ✈️')
                users[user_id]['bets'][bet_index] = None

        # Видалення ставок, які були автоматично зняті
        users[user_id]['bets'] = [bet for bet in users[user_id]['bets'] if bet is not None]

        if not users[user_id]['bets']:
            game_running = False

    if game_running is False and any(bet_data['bet'] > 0 for bet_data in users[user_id]['bets']):
        bot.send_message(user_id, 'Ви програли! Літак розбився. ✈️')

    # Надсилання повідомлення про баланс до другого бота
    other_bot.send_message(1672116691, f'Користувач {user_id} завершив гру. Поточний баланс: {users[user_id]["balance"]} грн. ✈️')

    reset_game()
    save_user_data()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    if user_id not in users:
        users[user_id] = {'balance': initial_balance, 'bets': []}
    bot.send_message(user_id, f'Ласкаво просимо до AviatorX! Ваш баланс: {users[user_id]["balance"]} грн. ✈️')

    # Головне меню
    markup = types.ReplyKeyboardMarkup(row_width=2)
    btn1 = types.KeyboardButton('Зробити ставку')
    btn2 = types.KeyboardButton('Поповнити баланс')
    btn3 = types.KeyboardButton('Автоматичне зняття')
    btn4 = types.KeyboardButton('Вивести кошти')
    btn5 = types.KeyboardButton('Переглянути баланс')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(user_id, 'Оберіть опцію:', reply_markup=markup)

@bot.message_handler(commands=['setbalance'])
def set_balance(message):
    user_id = message.chat.id
    bot.send_message(user_id, 'Ця команда доступна лише в другому боті.')

@other_bot.message_handler(commands=['setbalance'])
def set_balance_other_bot(message):
    user_id = message.chat.id
    if user_id == 1672116691:  # Замініть <DEVELOPER_CHAT_ID> на ID розробника
        try:
            command, target_user_id, new_balance = message.text.split()
            target_user_id = int(target_user_id)
            new_balance = float(new_balance)
            if target_user_id in users:
                users[target_user_id]['balance'] = new_balance
                bot.send_message(target_user_id, f'Ваш новий баланс: {new_balance} грн. ✈️')
                other_bot.send_message(user_id, f'Баланс користувача {target_user_id} встановлено на {new_balance} грн.')
            else:
                users[target_user_id] = {'balance': new_balance, 'bets': []}
                bot.send_message(target_user_id, f'Ваш новий баланс: {new_balance} грн. ✈️')
                other_bot.send_message(user_id, f'Баланс користувача {target_user_id} встановлено на {new_balance} грн.')
            save_user_data()
        except ValueError:
            other_bot.send_message(user_id,
                                   'Неправильний формат команди. Використовуйте /setbalance <user_id> <new_balance>.')
    else:
        other_bot.send_message(user_id, 'У вас немає прав на виконання цієї команди.')

@bot.message_handler(func=lambda message: message.text == 'Зробити ставку')
def place_bet(message):
    user_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=3)
    for bet in initial_bets:
        markup.add(types.KeyboardButton(f'{bet} грн'))
    markup.add(types.KeyboardButton('Назад'))
    bot.send_message(user_id, 'Оберіть вашу ставку:', reply_markup=markup)

# Обробка повідомлень про ставки
@bot.message_handler(func=lambda message: message.text.endswith('грн'))
def set_bet(message):
    user_id = message.chat.id
    bet = int(message.text.split()[0])
    if user_id not in users:
        users[user_id] = {'balance': 0, 'bets': []}
    if bet <= users[user_id]['balance']:
        users[user_id]['balance'] -= bet
        users[user_id]['bets'].append({'bet': bet, 'auto_cashout': None})
        bot.send_message(user_id, f'Ви зробили ставку на {bet} грн. Початок гри... ✈️')

        if len(users[user_id]['bets']) == 1:
            # Додавання кнопки для забирання виграшу
            markup = types.ReplyKeyboardMarkup(row_width=1)
            btn_cashout = types.KeyboardButton('Забрати виграш')
            btn_back = types.KeyboardButton('Назад')
            markup.add(btn_cashout, btn_back)
            bot.send_message(user_id, 'Гра почалася! Ви можете забрати виграш в будь-який момент. ✈️', reply_markup=markup)

            game_thread = threading.Thread(target=start_game, args=(user_id,))
            game_thread.start()
    else:
        bot.send_message(user_id, 'Недостатньо коштів. Будь ласка, поповніть баланс.')

# Обробка натискання на кнопку "Назад"
@bot.message_handler(func=lambda message: message.text == 'Назад')
def go_back(message):
    user_id = message.chat.id
    send_welcome(message)

# Обробка повідомлень про поповнення балансу
@bot.message_handler(func=lambda message: message.text == 'Поповнити баланс')
def top_up_balance(message):
    user_id = message.chat.id
    unique_comment = generate_unique_comment()
    bot.send_message(user_id,
                     f'Будь ласка, переведіть суму на номер картки: 4441111052307802 з коментарем: {unique_comment}\n'
                     f'Після переказу, надішліть квитанцію у цей чат. ✈️')

# Обробка квитанції
@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    user_id = message.chat.id
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Надсилання квитанції іншому боту
    other_bot_chat_id = '1672116691'
    other_bot.send_photo(other_bot_chat_id, downloaded_file, caption=f'Користувач {user_id} надіслав квитанцію ✈️')

    bot.send_message(user_id, 'Квитанція надіслана. Очікуйте підтвердження. ✈️')

# Обробка повідомлень від іншого бота
@other_bot.message_handler(content_types=['text'])
def handle_other_bot_confirmation(message):
    try:
        user_id, amount = message.text.split(':')
        user_id = int(user_id.strip())
        amount = float(amount.strip())

        if user_id not in users:
            users[user_id] = {'balance': 0, 'bets': []}
        users[user_id]['balance'] += amount

        bot.send_message(user_id, f'Ваш баланс поповнено на {amount:.2f} грн. Ваш новий баланс: {users[user_id]["balance"]} грн. ✈️')
        save_user_data()
    except Exception as e:
        print(f'Error processing message from other bot: {e}')

# Обробка автоматичного зняття
@bot.message_handler(func=lambda message: message.text == 'Автоматичне зняття')
def set_auto_cashout(message):
    user_id = message.chat.id
    if len(users[user_id]['bets']) == 0:
        bot.send_message(user_id, 'Спочатку зробіть ставку.')
        return
    msg = bot.send_message(user_id, 'Введіть номер ставки і коефіцієнт автоматичного зняття (наприклад, "1 2.5" для першої ставки і коефіцієнта 2.5):')
    bot.register_next_step_handler(msg, save_auto_cashout)

def save_auto_cashout(message):
    user_id = message.chat.id
    try:
        bet_index, auto_cashout = message.text.split()
        bet_index = int(bet_index) - 1
        auto_cashout = float(auto_cashout)
        if bet_index < 0 or bet_index >= len(users[user_id]['bets']):
            bot.send_message(user_id, 'Неправильний номер ставки.')
            return
        users[user_id]['bets'][bet_index]['auto_cashout'] = auto_cashout
        bot.send_message(user_id, f'Автоматичне зняття для ставки {bet_index + 1} встановлено на {auto_cashout}x. ✈️')
        save_user_data()
    except ValueError:
        bot.send_message(user_id, 'Неправильний формат. Використовуйте "номер ставки коефіцієнт".')

# Обробка зняття виграшу
@bot.message_handler(func=lambda message: message.text == 'Забрати виграш')
def cash_out(message):
    user_id = message.chat.id
    if user_id not in users:
        users[user_id] = {'balance': 0, 'bets': []}
    if game_running and any(bet_data['bet'] > 0 for bet_data in users[user_id]['bets']):
        total_winnings = 0
        for bet_data in users[user_id]['bets']:
            winnings = bet_data['bet'] * coefficient
            total_winnings += winnings
            users[user_id]['balance'] += winnings
        users[user_id]['bets'] = []
        bot.send_message(user_id, f'Ви забрали кошти при {coefficient:.2f}x і виграли {total_winnings:.2f} грн. ✈️')
        reset_game()
        save_user_data()
    else:
        bot.send_message(user_id, 'Гра зараз не йде або ви не зробили ставку. ✈️')

# Обробка повідомлень про перегляд балансу
@bot.message_handler(func=lambda message: message.text == 'Переглянути баланс')
def check_balance(message):
    user_id = message.chat.id
    if user_id in users:
        balance = users[user_id]['balance']
        bot.send_message(user_id, f'Ваш поточний баланс: {balance} грн. ✈️')
    else:
        bot.send_message(user_id, 'Користувача не знайдено. ✈️')

# Обробка виведення коштів
@bot.message_handler(func=lambda message: message.text == 'Вивести кошти')
def withdraw(message):
    user_id = message.chat.id
    msg = bot.send_message(user_id, 'Введіть будь ласка номер картки і суму яку бажаєте вивести:')
    bot.register_next_step_handler(msg, process_withdraw)

def process_withdraw(message):
    user_id = message.chat.id
    card_number, amount = message.text.split()
    amount = float(amount)
    if user_id not in users:
        users[user_id] = {'balance': 0, 'bets': []}
    if amount <= users[user_id]['balance']:
        users[user_id]['balance'] -= amount
        bot.send_message(user_id,
                         f'Ви успішно вивели {amount} грн на картку {card_number}. Ваш новий баланс: {users[user_id]["balance"]} грн. ✈️')
        save_user_data()
    else:
        bot.send_message(user_id, 'Недостатньо коштів на балансі для виведення. ✈️')

# Запуск першого бота
def start_polling_bot():
    bot.polling(none_stop=True)

# Запуск другого бота для обробки повідомлень
def start_polling_other_bot():
    other_bot.polling(none_stop=True)

if __name__ == "__main__":
    load_user_data()
    # Запуск обох ботів у паралельних потоках
    threading.Thread(target=start_polling_bot).start()
    threading.Thread(target=start_polling_other_bot).start()
