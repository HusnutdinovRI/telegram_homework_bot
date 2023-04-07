from telegram import Bot
from telegram.ext import CommandHandler, Updater
from telegram import ReplyKeyboardMarkup
from dotenv import load_dotenv
import time
import telegram
import requests
import os
import logging
import pprint

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

updater = Updater(token=TELEGRAM_TOKEN)

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    if (not PRACTICUM_TOKEN
       or not TELEGRAM_TOKEN
       or not TELEGRAM_CHAT_ID):
        return False
    return True


def send_message(bot, message):
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(timestamp):
    payload = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    return homework_statuses.json()


def check_response(response):
    if ('homeworks' not in response
       or 'current_date' not in response):
        return False
    return True


def parse_status(homework):
    homework_name = homework['homeworks'][0]['lesson_name']
    homework_status = homework['homeworks'][0]['status']
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    homework = get_api_answer(timestamp)
    while True:
        try:
            response = get_api_answer(timestamp)
            if not check_response(response):
                raise Exception
            if not response['homeworks'][0]['status']:
                time.sleep(RETRY_PERIOD)
                break
            message = parse_status(response)
            send_message(bot, message)
        except IndexError as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
        
        ...


if __name__ == '__main__':
    main()
