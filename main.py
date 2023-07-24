import configparser
from bar_bot import BarBot
from google.google_drive_api import GoogleDriveAPI
from google.google_sheets_api import GoogleSheetsAPI

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("config.ini")

    bot_token = config.get("Credentials", "bot_token")
    credentials_file = config.get("Credentials", "credentials_file")
    spreadsheet_id = config.get("Credentials", "spreadsheet_id")
    admin_chat_id = config.get("Credentials", "admin_chat_id")

    google_drive_api = GoogleDriveAPI(credentials_file)
    google_sheets_api = GoogleSheetsAPI(credentials_file, spreadsheet_id)
    bot = BarBot(bot_token, admin_chat_id, google_sheets_api, google_drive_api)
    bot.start_polling()
