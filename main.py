import sys
import time
import ast
import os
import datetime

import vk
import logging.config
from dotenv import load_dotenv

from date_format import get_date

load_dotenv()

API_VERSION = '5.131'  # версия VK API
REQUEST_DELAY = 0.4  # Задержка между запросами к API
TOKEN = os.getenv('TOKEN')  # токен вашего приложения VK для доступа к VK API
# словарь с id членов диалога и имени контакта в телефонной книге
# например, {0000000: 'Александр Пушкин'}
MEMBER_NAMES = ast.literal_eval(os.getenv('MEMBER_NAMES'))
PEER_ID = os.getenv('PEER_ID')  # ID чата в VK
GROUP = os.getenv('GROUP')  # ID принадлежит групповому чату?

api = vk.API(access_token=TOKEN, v=API_VERSION)

logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)


def check_environment_variables() -> bool:
    """Функция проверяет доступность необходимых переменных окружения."""
    return all([TOKEN, MEMBER_NAMES, PEER_ID, GROUP])


def get_history_items(peer_id, offset=0, count=200, group=0):
    if group:
        peer_id += 2000000000
    items = []

    logger.info(f'Начинаем загрузку сообщений')
    while True:
        try:
            request = api.messages.getHistory(
                offset=offset,
                count=count,
                peer_id=peer_id,
                rev=1,
            )
        except Exception as error:
            logger.error(f'Сбой при загрузке: {error}')
            sys.exit()
        if not request['items']:
            logger.info(f'Больше сообщений нет')
            break

        offset += 200
        items.extend(request['items'])
        logger.info(f'Загружено {len(items)} сообщений')
        time.sleep(REQUEST_DELAY)

    return items


def get_messages(items: list) -> list:
    messages = []

    logger.info(f'Провожу парсинг сообщений')
    for item in items:
        date = get_date(item['date'])
        member = MEMBER_NAMES.get(item['from_id'])
        text = item['text']
        urls = []

        if text:
            messages.append(f'{date} - {member}: {text}')

        for attachment in item['attachments']:
            if photo := attachment.get('photo'):
                url = next((photo['sizes'][i]['url'] for i in
                            range(len(photo['sizes'])) if
                            photo['sizes'][i]['type'] == 'w'),
                           photo['sizes'][-1]['url'])
                urls.append(url)

        if urls:
            for url in urls:
                messages.append(f'{date} - {member}: {url} (файл добавлен)')

    return messages


def main():
    """Основная логика работы приложения."""
    start_time = datetime.datetime.now()

    if not check_environment_variables():
        logger.critical(
            'Отсутствуют необходимые переменные окружения'
            'Работа программы завершена'
        )
        sys.exit()

    items = get_history_items(peer_id=int(PEER_ID), group=int(GROUP), offset=0)

    if items:
        messages = get_messages(items)
        file_name = 'backup_chat.txt'
        logger.info(f'Сохраняю сообщения в файл {file_name}')
        with open(file_name, 'w') as f:
            for message in messages:
                f.write(f'{message}\n')
    else:
        logger.info(f'В этом чате нет сообщений')

    end_time = datetime.datetime.now()
    time_delta = end_time - start_time
    logger.info(f'Затрачено секунд: {time_delta.total_seconds()}')


if __name__ == '__main__':
    main()
