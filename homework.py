import time
import os
import logging
import sys
import telegram
import requests

from http import HTTPStatus
from logging import StreamHandler
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s'
                              '- %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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


def check_tokens() -> bool:
    """Проверяет наличие обязательных пременных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message) -> None:
    """Отправляет сообщение в месседжер."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.TelegramError as error:
        logger.error(error)
    else:
        logger.debug('Сообщение успешно отпавлено')


def get_api_answer(timestamp) -> dict:
    """Делает запрос к эндпоинту."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code != HTTPStatus.OK:
            raise RuntimeError('Проблема доступа к эндпойнту')
        return response.json()
    except requests.RequestException:
        raise RuntimeError('Проблема доступа к эндпойнту')


def check_response(response) -> None:
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict) or not isinstance(
            response.get('homeworks'), list):
        raise TypeError('Тип данных отличается от ожидаемого')
    if response.get('homeworks') is None:
        raise KeyError('Отсуствуюет ключ homeworks')


def parse_status(homework) -> str:
    """Извлекает статус работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if 'homework_name' not in homework:
        raise KeyError('Отсуствуюет ключ homework_name')
    if homework_status is None:
        raise KeyError('API домашки возвращает пустой статус')
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError('API домашки возвращает недокументированный статус')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствуют обязательные переменные окружения')
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            timestamp = int(time.time())
            response = get_api_answer(timestamp)
            check_response(response)
            if response.get('homeworks') is not None:
                homework = response['homeworks'][0]
                message = parse_status(homework)
                send_message(bot, message)
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
