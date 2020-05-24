import sqlite3
from telebot import types
import config
import time
from threading import Thread

thread_count = 0


class Logic:
    def __init__(self, bot):
        self.command_all_post = 'SELECT * FROM posts'
        self.bot = bot

    def __time_convert(self, mode, time_data):
        """
        :param mode: unix or time/ если выбрано unix - переведет форматированный ввод в unix время
                                    если выбрано time - переведет unix в нормальное время
        :param time_data:
        :return:
        """
        if mode == 'unix':
            data = int(time.mktime(time.strptime(time_data, '%d-%m-%Y %H:%M:%S'))) + 10775
        elif mode == 'time':
            data = time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(time_data))
        return data

    def __execute_sql(self, command):
        """
        выполняет команду sql
        :param command: команда
        :return: вывод от команды
        """
        base = sqlite3.connect(config.DATABASE)
        cur = base.cursor()
        cur.execute(command)
        result = cur.fetchall()
        base.commit()
        cur.close()
        base.close()
        return result

    def inline_markup(*args):
        """
        создает клавиатуру
        :param args: передаем кортэж кортэжей типа ((текст, значение),(текст, значение))
        :return: клавиатуру с заданными кнопками
        """
        keyboard = types.InlineKeyboardMarkup()
        for item in args:
            text, calldata = item
            callback_button = types.InlineKeyboardButton(text=text, callback_data=calldata)
            keyboard.add(callback_button)
        return keyboard

    def start(self, id):
        """
        Вызывается при первом включении бота и добавляет пользователя в базу
        :param id:
        :return:
        """
        try:
            command = f'INSERT INTO users VALUES ({id}, 0, 0)'
            self.__execute_sql(command)
        except:
            pass

    def get_state(self, mode, id):
        """
        Выдает значение состояния по моду
        :param mode: если mode==user выдает состояние в котором сидит пользователь,
                        если mode==post выдает Выбранный в данный момент пост
        :param id: id пользователя
        :return: возвращает состояние
        """
        result = ''
        if mode == 'user':
            command = f'SELECT * FROM users WHERE ID = {id}'
            result = self.__execute_sql(command)[0][1]

        elif mode == 'post':
            command = f"SELECT * FROM users WHERE ID = {id}"
            result = self.__execute_sql(command)[0][2]
        return result

    def set_state(self, mode, id, state):
        """
        назначаем состояние пользователя или поста
        :param mode: указываем user при изменении состояния пользователя,
                    указываем post при изменении состояния поста
        :param id: id поста или пользователя
        :param state: указываем новое состояние
        :return:
        """
        if mode == 'user':
            command = f'UPDATE users SET state = {state} WHERE id = {id}'
            self.__execute_sql(command)
        elif mode == 'post':
            command = f'UPDATE users SET state_post = {state} WHERE id = {id}'
            self.__execute_sql(command)

    def get_all_post(self, mode):
        """
        Возвращает строку со всеми записями в базе данных
        :param mode: Конечная строка, если mode==create - надпись редактирования
                                        если mode==del - надпись удаления
        :return: возвращает строку
        """
        results = self.__execute_sql(self.command_all_post)
        text = f'Выбери цифру поста {config.Emoji.check}:\n'
        for item in results:
            if item[2]:
                post_time = self.__time_convert('time', item[2] - 10775)
            else:
                post_time = 'время не назначено'

            post = f'{item[0]}. {item[1]}\n{post_time}\n\n'
            text += post
        if mode == 'create':
            text += 'Какой будем редактирвоать?'
        elif mode == 'del':
            text += 'Какой будем удалять?'
        else:
            pass
        return text

    def get_time(self, post_id):
        command = f'SELECT * FROM posts WHERE id = {post_id}'
        result = self.__execute_sql(command)[0][2]
        return result

    def save_post(self, text):
        commands = f'INSERT INTO posts(item) VALUES ("{text}")', f'SELECT id FROM posts WHERE item = "{text}"'
        result = ''
        for cmd in commands:
            result = self.__execute_sql(cmd)
        return result

    def quantity_posts(self):
        result = self.__execute_sql(self.command_all_post)
        quantity = (item[0] for item in result)
        return quantity

    def redactor_post(self, mode, post_id, text=''):
        """
        редактирование или удаление поста
        :param mode: указывавем update при изменении, del при удалении, time при изменении времени
        :param post_id: указываем id поста
        :param text: указываем только при изменении
        :return:
        """
        if mode == 'update':
            command = f'UPDATE posts SET item = "{text}" WHERE id = {post_id}'
            self.__execute_sql(command)
        elif mode == 'del':
            command = f'DELETE FROM posts WHERE id = {post_id}'
            self.__execute_sql(command)
        elif mode == 'time':
            try:
                clock = self.__time_convert('unix', text)
                post_id = self.get_state(mode='post', id=post_id)
                command = f'UPDATE posts SET time = {clock} WHERE id = {post_id}'
                self.__execute_sql(command)
                return True
            except:
                return False

    def send_now(self, bot, call):
        post_id = self.get_state(mode='post', id=call.message.chat.id)
        text_post = self.__execute_sql(f'SELECT item FROM posts WHERE id = {post_id}')[0]
        for channel in config.CHANNEL_NAMES:
            bot.send_message(channel, text_post)
        self.redactor_post(mode='del', post_id=post_id)
        self.set_state(mode='user', id=call.message.chat.id, state=0)
        self.set_state(mode='post', id=call.message.chat.id, state=0)

    def create_thread(self, post_id):
        th = Thread(target=self.send_time, args=(post_id,))
        th.start()

    def send_time(self, post_id):
        while True:
            if time.time() > self.get_time(post_id):
                text = self.__execute_sql(f'SELECT item FROM posts WHERE id = {post_id}')
                for channel in config.CHANNEL_NAMES:
                    self.bot.send_message(channel, text)
                self.redactor_post(mode='del', post_id=post_id)
                break
            else:
                time.sleep(20)
