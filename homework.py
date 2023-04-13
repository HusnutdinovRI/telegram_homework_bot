
from telegram import Bot
from telegram.ext import CommandHandler, Updater
from telegram import ReplyKeyboardMarkup
from dotenv import load_dotenv
import time
import requests
import os
import logging
import sys
from logging import StreamHandler

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
handler = StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

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
    """Проверяет наличие обязательных пременных окружения."""
    if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.critical('Отсутствуют обязательные переменные окружения.')
        sys.exit()
    return True


def send_message(bot, message):
    """Отправляет сообщение в месседжер"""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.debug('Сообщение успешно отпавлено')


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту"""
    try:
        payload = {'from_date': int(timestamp)}
        homework_statuses = requests.get(ENDPOINT, headers=HEADERS,
                                         params=payload)
        if homework_statuses.status_code != 200:
            raise requests.RequestException(
                'Сбой доступа к эндпойнту'
            )
        return homework_statuses.json()
    except requests.RequestException as error:
        return RuntimeError(error)


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    print(type(response))
    if 'homeworks' not in response:
        logger.error('Отсуствуюет ключ homeworks')
        raise KeyError('Отсуствуюет ключ homeworks')
    if not isinstance(response, dict):
        logger.error(f'Тип данных {type(response)}отличается от ожидаемого')
        raise TypeError('Ожидаемыый типа данных - словарь')
    if not isinstance(response.get('homeworks'), list):
        logger.error('Тип данных отличается от ожидаемого')
        raise TypeError('Ожидаемыый типа данных - список')
    return response


def parse_status(homework):
    '''Извлекает статус работы.'''
    homework_name = homework.get('homework_name')
    if 'homework_name' not in homework:
        logger.error('Отсуствуюет ключ homework_name')
        raise KeyError('Отсуствуюет ключ homework_name')
    try:
        homework_status = homework.get('status')
        verdict = HOMEWORK_VERDICTS[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except KeyError:
        logger.error('API домашки возвращает недокументированный статус '
                     'домашней работы либо домашку без статуса')


def main():
    """Основная логика работы бота."""  
    bot = Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            timestamp = int(time.time())
            response = get_api_answer(timestamp)
            check_tokens()   
            check_response(response)
            homework = response.get('homeworks')[0]
            message = parse_status(homework)
            send_message(bot, message)        
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}' )
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
