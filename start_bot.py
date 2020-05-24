from telebot import TeleBot
from telebot import apihelper
import config
import logic_bot

bot = TeleBot(config.TOKEN)
apihelper.proxy = {'https': 'socks5h://508519294:ekCx3RuA@grsst.s5.opennetwork.cc:999'}

log_bot = logic_bot.Logic(bot)


@bot.message_handler(func=lambda message: True, commands=['start'])
def start(message):
    bot.send_message(message.chat.id, config.TextMenu.START, reply_markup=config.start_markup)
    log_bot.start(message.chat.id)


@bot.message_handler(func=lambda message: config.State.CREATE == log_bot.get_state(mode='user', id=message.chat.id))
def create(message):
    post_id = log_bot.save_post(message.text)[0][0]
    log_bot.set_state(mode='user', id=message.chat.id, state=7)
    log_bot.set_state(mode='post', id=message.chat.id, state=post_id)
    bot.send_message(message.chat.id, config.TextMenu.SAVE + config.TextMenu.CHOICE_TIME,
                     reply_markup=config.saved_markup)


@bot.message_handler(
    func=lambda message: config.State.REDACTOR_CHOICE == log_bot.get_state(mode='user', id=message.chat.id))
def redactor_choice(message):
    if message.text.isdigit() and int(message.text) in log_bot.quantity_posts():
        bot.send_message(message.chat.id, config.TextMenu.NEW_POST)
        log_bot.set_state(mode='post', id=message.chat.id, state=int(message.text))
        log_bot.set_state(mode='user', id=message.chat.id, state=3)
    else:
        bot.send_message(message.chat.id, config.TextMenu.NOPE_POST)


@bot.message_handler(
    func=lambda message: config.State.REDACTOR_COMMIT == log_bot.get_state(mode='user', id=message.chat.id))
def redactor_commit(message):
    state_post = log_bot.get_state(mode='post', id=message.chat.id)
    log_bot.redactor_post(mode='update', post_id=state_post, text=message.text)
    bot.send_message(message.chat.id, f'Пост - {state_post} обновлен! {config.Emoji.reload}')
    log_bot.set_state(mode='user', id=message.chat.id, state=0)


@bot.message_handler(func=lambda message: config.State.DEL_CHOICE == log_bot.get_state(mode='user', id=message.chat.id))
def delete_choice(message):
    if message.text.isdigit() and int(message.text) in log_bot.quantity_posts():
        log_bot.redactor_post(mode='del', post_id=message.text)
        log_bot.set_state(mode='user', id=message.chat.id, state=0)
        bot.send_message(message.chat.id, config.TextMenu.DEL_POST)
    else:
        bot.send_message(message.chat.id, config.TextMenu.NOPE_POST)


@bot.message_handler(func=lambda message: config.State.SET_TIME == log_bot.get_state(mode='user', id=message.chat.id))
def set_time(message):
    if log_bot.redactor_post(mode='time', post_id=message.chat.id, text=message.text):
        bot.send_message(message.chat.id, config.TextMenu.TIME)
        log_bot.set_state(mode='user', id=message.chat.id, state=0)
        post_id = log_bot.get_state(mode='post', id=message.chat.id)
        log_bot.create_thread(post_id)
    else:
        bot.send_message(message.chat.id, config.TextMenu.DEFAULT_TIME)
        return


@bot.message_handler(
    func=lambda message: config.State.REDACTOR_TIME == log_bot.get_state(mode='user', id=message.chat.id))
def redactor_time(message):
    if log_bot.redactor_post(mode='time', post_id=message.chat.id, text=message.text):
        bot.send_message(message.chat.id, config.TextMenu.TIME)
        log_bot.set_state(mode='user', id=message.chat.id, state=0)
    else:
        bot.send_message(message.chat.id, config.TextMenu.DEFAULT_TIME)
        return


@bot.message_handler(
    func=lambda message: config.State.REDACTOR_POSTS == log_bot.get_state(mode='user', id=message.chat.id))
def select_time_or_post(message):
    bot.send_message(message.chat.id, config.TextMenu.WHAT_DO)


@bot.message_handler(
    func=lambda message: config.State.CHOICE_TIME == log_bot.get_state(mode='user', id=message.chat.id))
def choice_time(message):
    if message.text.isdigit() and int(message.text) in log_bot.quantity_posts():
        bot.send_message(message.chat.id, config.TextMenu.EXAMPLE_TIME)
        log_bot.set_state(mode='post', id=message.chat.id, state=int(message.text))
        log_bot.set_state(mode='user', id=message.chat.id, state=7)
    else:
        bot.send_message(message.chat.id, config.TextMenu.NOPE_POST)


@bot.message_handler(content_types=['text'])
def start(message):
    bot.send_message(message.chat.id, config.TextMenu.MAIN_MENU, reply_markup=config.start_markup)



# ------ОБРАБОТКА КНОПОК -----------------------------

@bot.callback_query_handler(func=lambda call: call.data == 'create')
def call_create(call):
    bot.send_message(call.message.chat.id, config.TextMenu.POST)
    log_bot.set_state(mode='user', id=call.message.chat.id, state=1)


@bot.callback_query_handler(func=lambda call: call.data == 'send_now')
def call_now(call):
    if log_bot.get_state(mode='post', id=call.message.chat.id):
        log_bot.send_now(bot, call)
        bot.send_message(call.message.chat.id, config.TextMenu.SEND_POST)
    else:
        bot.send_message(call.message.chat.id, 'Снова отправить нельзя)')


@bot.callback_query_handler(func=lambda call: call.data == 'send_time')
def call_time(call):
    if log_bot.get_state(mode='post', id=call.message.chat.id):
        bot.send_message(call.message.chat.id, config.TextMenu.EXAMPLE_TIME)
        log_bot.set_state(mode='user', id=call.message.chat.id, state=5)
    else:
        bot.send_message(call.message.chat.id, 'Пост уже отправлен))')


@bot.callback_query_handler(func=lambda call: call.data == 'redactor_posts')
def call_redactor(call):
    bot.send_message(call.message.chat.id, config.TextMenu.WHAT_DO, reply_markup=config.redactor_markup)
    log_bot.set_state(mode='user', id=call.message.chat.id, state=8)


@bot.callback_query_handler(func=lambda call: call.data == 'redactor')
def call_all(call):
    log_bot.set_state(mode='user', id=call.message.chat.id, state=2)
    text = log_bot.get_all_post(mode='create')
    bot.send_message(call.message.chat.id, text, reply_markup=config.cancel_markup)


@bot.callback_query_handler(func=lambda call: call.data == 'change_time')
def call_redact_time(call):
    log_bot.set_state(mode='user', id=call.message.chat.id, state=6)
    text = log_bot.get_all_post(mode='create')
    bot.send_message(call.message.chat.id, text, reply_markup=config.cancel_markup)


@bot.callback_query_handler(func=lambda call: call.data == 'del')
def call_del(call):
    log_bot.set_state(mode='user', id=call.message.chat.id, state=4)
    text = log_bot.get_all_post(mode='del')
    bot.send_message(call.message.chat.id, text, reply_markup=config.cancel_markup)


@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def cancel(call):
    log_bot.set_state(mode='user', id=call.message.chat.id, state=0)
    bot.send_message(call.message.chat.id, config.TextMenu.MAIN_MENU, reply_markup=config.start_markup)


if __name__ == '__main__':
    bot.infinity_polling()
