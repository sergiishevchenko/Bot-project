from glob import glob
import logging
import os
from random import choice

from telegram import ReplyKeyboardRemove, ReplyKeyboardMarkup, ParseMode, error
from telegram.ext import ConversationHandler
from telegram.ext import messagequeue as mq
from db import db, get_or_create_user, get_user_emo, toggle_subscription, get_subscribed
from utils import get_keyboard, is_cat
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from emoji import emojize


def greet_user(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
    emo = get_user_emo(db, user)
    user_data['emo'] = emo
    text = 'Привет {}'.format(emo)
    logging.info(text)
    update.message.reply_text(text, reply_markup=get_keyboard())


def talk_to_me(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
    emo = get_user_emo(db, user)
    user_text = 'Привет {} {}! Ты написал: {}'.format(user['first_name'], emo, update.message.text)
    logging.info('User: %s, Chat id: %s, Message: %s', user['username'],
                                                        update.message.chat.id,
                                                        update.message.text)
    update.message.reply_text(user_text, reply_markup=get_keyboard())


def send_cat_picture(bot, update, user_data):
    cat_list = glob('images/cat*.jp*g')
    cat_pic = choice(cat_list)
    inlinekbd = [[InlineKeyboardButton(emojize(":thumbs_up:"), callback_data='cat_good'),
                    InlineKeyboardButton(emojize(":thumbs_down:"), callback_data='cat_bad')]]
    kbd_markup = InlineKeyboardMarkup(inlinekbd)
    bot.send_photo(chat_id=update.message.chat.id, photo=open(cat_pic, 'rb'), reply_markup=kbd_markup)


def change_avatar(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
    if 'emo' in user:
        del user['emo']
    emo = get_user_emo(db, user)
    update.message.reply_text('Готово: {}'.format(emo), reply_markup=get_keyboard())


def get_contact(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
    print(update.message.contact)
    update.message.reply_text('Готово {}'.format(get_user_emo(db, user)), reply_markup=get_keyboard())


def get_location(bot, update, user_data):
    user = get_or_create_user(db, update.effective_user, update.message)
    print(update.message.location)
    update.message.reply_text('Спасибо {}'.format(get_user_emo(db, user)), reply_markup=get_keyboard())


def check_user_photo(bot, update, user_data):
    update.message.reply_text("Обрабатываю фото")
    os.makedirs('downloads', exist_ok=True)
    photo_file = bot.getFile(update.message.photo[-1].file_id)
    filename = os.path.join('downloads', '{}.jpg'.format(photo_file.file_id))
    photo_file.download(filename)
    if is_cat(filename):
        update.message.reply_text("Обнаружен котик, добавляю в библиотеку.")
        new_filename = os.path.join('images', 'cat_{}.jpg'.format(photo_file.file_id))
        os.rename(filename, new_filename)
    else:
        os.remove(filename)
        update.message.reply_text("Тревога, котик не обнаружен!")


def anketa_start(bot, update, user_data):
    update.message.reply_text("Как вас зовут? Напишите имя и фамилию", reply_markup=ReplyKeyboardRemove())
    return "name"


def anketa_get_name(bot, update, user_data):
    user_name = update.message.text
    if len(user_name.split(" ")) < 2:
        update.message.reply_text("Пожалуйста, напишите имя и фамилию")
        return "name"
    else:
        user_data["anketa_name"] = user_name
        reply_keyboard = [["1", "2", "3", "4", "5"]]

        update.message.reply_text(
            "Понравился ли вам курс? Оцените по шкале от 1 до 5",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return "rating"


def anketa_rating(bot, update, user_data):
    user_data["anketa_rating"] = update.message.text

    update.message.reply_text(""" Оставьте комментарий в свободной форме
или пропустите этот шаг, введя /cancel""")
    return "comment"


def anketa_comment(bot, update, user_data):
    user_data["anketa_comment"] = update.message.text
    user_text = """
<b>Имя Фамилия:</b> {anketa_name}
<b>Оценка:</b> {anketa_rating}
<b>Комментарий:</b> {anketa_comment}""".format(**user_data)

    update.message.reply_text(user_text, reply_markup=get_keyboard(),
                                parse_mode=ParseMode.HTML)
    return ConversationHandler.END


def anketa_skip_comment(bot, update, user_data):
    user_text = """
<b>Имя Фамилия:</b> {anketa_name}
<b>Оценка:</b> {anketa_rating}""".format(**user_data)

    update.message.reply_text(user_text, reply_markup=get_keyboard(),
                                parse_mode=ParseMode.HTML)
    return ConversationHandler.END


def dontknow(bot, update, user_data):
    update.message.reply_text('Не понимаю')


def subscribe(bot, update):
    user = get_or_create_user(db, update.effective_user, update.message)
    if not user.get('subscribed'):
        toggle_subscription(db, user)
    update.message.reply_text("Вы подписались, наберите /unsubscribe чтобы отписаться")


def inline_button_pressed(bot, update):
    query = update.callback_query
    if query.data in ['cat_good', 'cat_bad']:
        text = "Круто" if query.data == "cat_good" else "Печаль"

        bot.edit_message_caption(caption=text, chat_id=query.message.chat_id, message_id=query.message.message_id)


@mq.queuedmessage
def send_updates(bot, job):
    for user in get_subscribed(db):
        try:
            bot.sendMessage(chat_id=user['chat_id'], text="BUZZZ!")
        except error.BadRequest:
            print('Chat {} not found'.format(user['chat_id']))


def unsubscribe(bot, update):
    user = get_or_create_user(db, update.effective_user, update.message)
    if not user.get('subscribed'):
        toggle_subscription(db, user)
        update.message.reply_text("Спасибо, что были с нами!")
    else:
        update.message.reply_text("Вы не подписаны, наберите /subscribe чтобы подписаться")


def set_alarm(bot, update, args, job_queue):
    try:
        seconds = abs(int(args[0]))
        job_queue.run_once(alarm, seconds, context=update.message.chat_id)
    except (IndexError, ValueError):
        update.message.reply_text("Введите число секунд после команды /alarm")


@mq.queuedmessage
def alarm(bot, job):
    bot.send_message(chat_id=job.context, text="Сработал будильник!")
