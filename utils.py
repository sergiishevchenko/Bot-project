from emoji import emojize
from random import choice
import settings
from telegram import ReplyKeyboardMarkup, KeyboardButton
from clarifai.rest import ClarifaiApp


def get_user_emo(user_data):
    if 'emo' in user_data:
        return user_data['emo']
    else:
        user_data['emo'] = emojize(choice(settings.USER_EMOJI), use_aliases=True)
        return user_data['emo']


def get_keyboard():
    contact_button = KeyboardButton('Контактные данные', request_contact=True)
    location_button = KeyboardButton('Геолокация', request_location=True)
    my_keyboard = ReplyKeyboardMarkup([['Прислать котика', 'Сменить аватарку'], [contact_button, location_button]], resize_keyboard=True)

    return my_keyboard


def is_cat(file_name):
    image_has_cat = False
    app = ClarifaiApp(api_key=settings.CLARIFAI_API_KEY)
    model = app.public_models.general_model
    response = model.predict_by_filename(file_name, max_concepts=5)
    import pprint
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(response)
    if response['status']['code'] == 10000:
        for concept in response['outputs'][0]['data']['concepts']:
            if concept['name'] == 'cat':
                image_has_cat = True
    return image_has_cat


if __name__ == "__main__":
    print(is_cat('images/cat1.jpeg'))
    print(is_cat('images/not_cat1.jpeg'))
