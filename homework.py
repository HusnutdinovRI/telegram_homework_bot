import telegram
import time
import requests
import os
import logging
import sys

from logging import StreamHandler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

logger = logging.getLogger()
logger.setLevel(logging.ERROR)
handler = StreamHandler(stream=sys.stdout)

TELEGRAM_TOKEN: str = str(os.getenv('TELEGRAM_TOKEN'))
PRACTICUM_TOKEN: str = str(os.getenv('PRACTICUM_TOKEN'))
TELEGRAM_CHAT_ID: str = str(os.getenv('TELEGRAM_CHAT_ID'))

RETRY_PERIOD: int = 600
ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: dict = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS: dict = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> None:
    """Проверяет наличие обязательных пременных окружения."""
    if (PRACTICUM_TOKEN is None
       or TELEGRAM_TOKEN is None
       or TELEGRAM_CHAT_ID is None):
        logging.critical('Отсутствуют обязательные переменные окружения.')
        sys.exit()


def send_message(bot, message) -> None:
    """Отправляет сообщение в месседжер."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.TelegramError as error:
        logging.error(error)
    logging.debug('Сообщение успешно отпавлено')


def get_api_answer(timestamp) -> dict:
    """Делает запрос к эндпоинту."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code != 200:
            logging.error('Проблема доступа к эндпойнту')
            raise RuntimeError('Проблема доступа к эндпойнту')
        return response.json()
    except requests.RequestException:
        logging.error('Проблема доступа к эндпойнту')
        return {}


def check_response(response) -> None:
    """Проверяет ответ API на соответствие документации."""
    if type(response) != dict or type(response.get('homeworks')) != list:
        logger.error('Тип данных отличается от ожидаемого')
        raise TypeError('Тип данных отличается от ожидаемого')
    if 'homeworks' not in response:
        logger.error('Отсуствуюет ключ homeworks')
        raise KeyError('Отсуствуюет ключ homeworks')


def parse_status(homework) -> str:
    """Извлекает статус работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if 'homework_name' not in homework:
        logger.error('Отсуствуюет ключ homework_name')
        raise KeyError('Отсуствуюет ключ homework_name')
    if homework_status is None:
        logger.error('API домашки возвращает пустой статус')
        raise KeyError('API домашки возвращает пустой статус')
    if homework_status not in HOMEWORK_VERDICTS:
        logger.error('API домашки возвращает недокументированный статус')
        raise KeyError('API домашки возвращает недокументированный статус')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> None:
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            check_tokens()
            timestamp = int(time.time())
            response = get_api_answer(timestamp)
            check_response(response)
            if response['homeworks']:
                homework = response['homeworks'][0]
                message = parse_status(homework)
                send_message(bot, message)
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
