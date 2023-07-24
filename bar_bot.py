from telebot import types, TeleBot
from google.google_sheets_api import GoogleSheetsAPI
from google.google_drive_api import GoogleDriveAPI
from utils.user_data import UserData
from utils.languages import Languages
from utils.action_buttons import ActionButtons
from utils.messages import Messages
from utils.menu import Menu

class BarBot:
    def __init__(self, bot_token: str, admin_chat_id: int, google_sheets_api: GoogleSheetsAPI, google_drive_api: GoogleDriveAPI):
        self.bot = TeleBot(bot_token)
        self.user_data = UserData(google_sheets_api)
        self.languages = Languages(google_sheets_api)
        self.action_buttons = ActionButtons(google_sheets_api, self.languages)
        self.messages = Messages(google_sheets_api, self.languages)
        self.menu = Menu(google_sheets_api, google_drive_api, self.languages)
        self.admin_chat_id = admin_chat_id

        self.bot.message_handler(commands=['start'])(self.start)
        self.bot.message_handler(func=lambda message: message.text == '↩')(self.handle_back_action)
        self.bot.message_handler(func=lambda message: message.text in self.languages.get_all_languages())(self.handle_language_selection)
        self.bot.message_handler(func=lambda message: message.text in self.action_buttons.get_button_names_by_action('menu'))(self.handle_menu_selection)
        self.bot.message_handler(func=lambda message: message.text in self.menu.get_all_category_names())(self.handle_menu_category_selection)
        self.bot.message_handler(func=lambda message: message.text in self.menu.get_all_titles())(self.handle_menu_category_title_selection)
        self.bot.message_handler(func=lambda message: message.text in self.action_buttons.get_button_names_by_action('complaints_and_suggestions'))(self.handle_complaints_and_suggestions_selection)
        self.bot.message_handler(func=lambda message: message.text)(self.handle_message_from_user)

    def __del__(self):
        try:
            self.save_state()
        except Exception as e:
            print(f"Error while saving state in __del__: {e}")

    def handle_back_action(self, message):
        try:
            id = str(message.chat.id)
            current_state = self.user_data.get_current_state(id)

            if  current_state == 'handle_menu_selection':
                selected_language = self.user_data.get_selected_language(id)
                message.text = selected_language
                self.handle_language_selection(message)

            elif current_state == 'handle_menu_category_selection':
                action = 'menu'
                selected_language = self.user_data.get_selected_language(id)
                button_name = self.action_buttons.get_button_name_by_action_and_language(action, selected_language)
                message.text = button_name
                self.handle_menu_selection(message)

            elif current_state == 'handle_complaints_and_suggestions_selection':
                selected_language = self.user_data.get_selected_language(id)
                message.text = selected_language
                self.handle_language_selection(message)

            else:
                message.text = 'start'
                self.start(message)

        except Exception as e:
            self.save_state()
            raise e

    def start_polling(self):
        self.bot.polling(none_stop=True)

    def start(self, message):
        try:
            id = str(message.chat.id)
            self.user_data.set_id(id)
            self.user_data.set_current_state(id, 'start')

            languages = self.languages.get_all_languages()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for language in languages:
                markup.add(types.KeyboardButton(language))
            text = 'Choose language'
            self.bot.send_message(id, text, reply_markup=markup)
        except Exception as e:
            self.save_state()
            raise e

    def handle_language_selection(self, message):
        try:
            id = str(message.chat.id)
            selected_language = message.text
            self.user_data.set_selected_language(id, selected_language)
            self.user_data.set_current_state(id, 'handle_language_selection')

            button_names = self.action_buttons.get_button_names_by_language(selected_language)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for button_name in button_names:
                markup.add(types.KeyboardButton(button_name))
            markup.add(types.KeyboardButton('↩'))
            text = self.messages.get_message_by_key_and_language('select_action', selected_language)
            self.bot.send_message(id, text, reply_markup=markup)
        except Exception as e:
            self.save_state()
            raise e

    def handle_menu_selection(self, message):
        try:
            id = str(message.chat.id)
            button_name = message.text
            selected_action = self.action_buttons.get_selected_action_by_button_name(button_name)
            selected_language = self.user_data.get_selected_language(id)
            self.user_data.set_selected_action(id, selected_action)
            self.user_data.set_current_state(id, 'handle_menu_selection')

            category_names = self.menu.get_category_names_by_language(selected_language)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for category in category_names:
                markup.add(types.KeyboardButton(category))
            markup.add(types.KeyboardButton('↩'))
            text = self.messages.get_message_by_key_and_language('select_category', selected_language)
            self.bot.send_message(id, text, reply_markup=markup)
        except Exception as e:
            self.save_state()
            raise e

    def handle_menu_category_selection(self, message):
        try:
            id = str(message.chat.id)
            selected_language = self.user_data.get_selected_language(id)
            selected_category = message.text
            self.user_data.set_selected_category(id, selected_category)
            self.user_data.set_current_state(id, 'handle_menu_category_selection')

            dishes_title = self.menu.get_dishes_titles_by_category_and_language(selected_category, selected_language)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for dish_data in dishes_title:
                text = dish_data["text"]
                markup.add(types.KeyboardButton(text))
            markup.add(types.KeyboardButton('↩'))
            text = self.messages.get_message_by_key_and_language('choose_dish', selected_language)
            self.bot.send_message(id, text, reply_markup=markup)
        except Exception as e:
            self.save_state()
            raise e

    def handle_menu_category_title_selection(self, message):
        try:
            id = str(message.chat.id)
            selected_language = self.user_data.get_selected_language(id)
            selected_title = message.text
            dish_data = self.menu.get_dish_data_by_title_and_language(selected_title, selected_language)
            if dish_data is not None:
                text = dish_data['text']
                image = dish_data['image']
                if image:
                    self.bot.send_photo(message.chat.id, image, caption=text, parse_mode='HTML')
                else:
                    self.bot.send_message(message.chat.id, text, parse_mode='HTML')
        except Exception as e:
            self.save_state()
            raise e

    def handle_complaints_and_suggestions_selection(self, message):
        try:
            id = str(message.chat.id)
            selected_language = self.user_data.get_selected_language(id)
            self.user_data.set_current_state(id, 'handle_complaints_and_suggestions_selection')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton('↩'))
            text = self.messages.get_message_by_key_and_language('write_complaint', selected_language)
            self.bot.send_message(id, text, reply_markup=markup)
        except Exception as e:
            self.save_state()
            raise e

    def handle_message_from_user(self, message):
        try:
            id = str(message.chat.id)
            selected_language = self.user_data.get_selected_language(id)
            message.text = selected_language
            self.handle_language_selection(message)
            complaints_and_suggestions_message = message.from_user.first_name + ' ' + message.from_user.last_name + ' Написал(а) вам: "' + message.text + '", свяжитесь с ним/ней чтобы обсудить это.'
            self.bot.send_message(admin_chat_id, complaints_and_suggestions_message)

            text = self.messages.get_message_by_key_and_language('complaint_consideration', selected_language)
            self.bot.send_message(id, text)

            message.text = selected_language
            self.handle_language_selection(message)

        except Exception as e:
            self.save_state()
            raise e

    def save_state(self):
        self.user_data.save_all_data()
        pass
