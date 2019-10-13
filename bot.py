from glob import glob
import logging
from random import choice

from emoji import emojize
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler

import settings

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='bot.log'
                    )


def greet_user(bot, update, user_data):
    emo = get_user_emo(user_data)
    user_data['emo'] = emo
    text = 'Привет {}'.format(emo)
    contact_button = KeyboardButton('Контактные данные', request_contact=True)
    location_button = KeyboardButton('Геолокация', request_location=True)
    my_keyboard = ReplyKeyboardMarkup([['Прислать котика', 'Сменить аватарку'], [contact_button, location_button]])
    logging.info(text)
    update.message.reply_text(text, reply_markup=my_keyboard)


def talk_to_me(bot, update, user_data):
    emo = get_user_emo(user_data)
    user_text = 'Привет {} {}! Ты написал: {}'.format(update.message.chat.first_name, emo, update.message.text)
    logging.info('User: %s, Chat id: %s, Message: %s', update.message.chat.username,
                                                        update.message.chat.id,
                                                        update.message.text)
    update.message.reply_text(user_text)


def send_cat_picture(bot, update, user_data):
    cat_list = glob('images/cat*.jp*g')
    cat_pic = choice(cat_list)
    bot.send_photo(chat_id=update.message.chat.id, photo=open(cat_pic, 'rb'))


def get_user_emo(user_data):
    if 'emo' in user_data:
        return user_data['emo']
    else:
        user_data['emo'] = emojize(choice(settings.USER_EMOJI), use_aliases=True)
        return user_data['emo']


def change_avatar(bot, update, user_data):
    if 'emo' in user_data:
        del user_data['emo']
    emo = get_user_emo(user_data)
    update.message.reply_text('Готово: {}'.format(emo))


def get_contact(bot, update, user_data):
    print(update.message.contact)
    update.message.reply_text('Готово {}'.format(get_user_emo(user_data)))


def get_location(bot, update, user_data):
    print(update.message.location)
    update.message.reply_text('Спасибо {}'.format(get_user_emo(user_data)))


def get_keyboard():
    contact_button = KeyboardButton('Контактные данные', request_contact=True)
    location_button = KeyboardButton('Геолокация', request_location=True)
    my_keyboard = ReplyKeyboardMarkup([['Прислать котика', 'Сменить аватарку'], [contact_button, location_button]], resize_keyboard=True)

    return my_keyboard


def main():
    mybot = Updater(settings.API_KEY)

    logging.info('Бот запускается')

    dp = mybot.dispatcher
    dp.add_handler(CommandHandler("start", greet_user, pass_user_data=True))
    dp.add_handler(CommandHandler("cat", send_cat_picture, pass_user_data=True))
    dp.add_handler(RegexHandler('^(Прислать котика)$', send_cat_picture, pass_user_data=True))
    dp.add_handler(RegexHandler('^(Сменить аватарку)$', change_avatar, pass_user_data=True))
    dp.add_handler(MessageHandler(Filters.contact, get_contact, pass_user_data=True))
    dp.add_handler(MessageHandler(Filters.location, get_location, pass_user_data=True))

    dp.add_handler(MessageHandler(Filters.text, talk_to_me, pass_user_data=True))

    mybot.start_polling()
    mybot.idle()


main()
