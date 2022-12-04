import re
import sys
import time
import ast
import os
import datetime
from typing import Optional

import requests
import vk
import logging.config
from dotenv import load_dotenv

from date_format import get_date

load_dotenv()

API_VERSION = '5.131'  # версия VK API
REQUEST_DELAY = 0.4  # задержка между запросами к API
FILE_MESSAGE_NAME = 'Чат WhatsApp с '
TOKEN = os.getenv('TOKEN')  # токен вашего приложения VK для доступа к VK API
# словарь с id членов диалога и имени контакта в телефонной книге
# например, {0000000: 'Александр Пушкин'}
MEMBER_NAMES = ast.literal_eval(os.getenv('MEMBER_NAMES'))
PEER_ID = int(os.getenv('PEER_ID'))  # ID чата VK (+2000000000, если групповой)
DOC_TYPES = {3: '.jpg', 4: '.gif'}
BACKUP_DIR = f'backup/{PEER_ID}/'
REGEXP = re.compile(r'\[id\d*\|@\w*]')

logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)
api = vk.API(access_token=TOKEN, v=API_VERSION)


def check_environment_variables() -> bool:
    """Функция проверяет доступность необходимых переменных окружения."""
    return all([TOKEN, MEMBER_NAMES, PEER_ID])


def get_chat_title(peer_id: int) -> str:
    """Функция возвращает заголовок чата для создания файла бэкапа."""
    try:
        response = api.messages.getConversationsById(peer_ids=peer_id)
    except Exception as error:
        logger.error(f'Чат не найден: {error}')
        sys.exit()
    return response['items'][0]['chat_settings']['title']


def get_history_items(peer_id: int, offset: int = 0, count: int = 200) -> list:
    """
    Функция загружает историю чата.
    offset - начальное сообщение для загрузки, count - кол-во сообщений.
    """
    history_items = []
    logger.info(f'Начинаем загрузку сообщений')
    while True:
        try:
            response = api.messages.getHistory(offset=offset,
                                               count=count,
                                               peer_id=peer_id,
                                               rev=1)
        except Exception as error:
            logger.error(f'Сбой при загрузке сообщений: {error}')
            sys.exit()

        if not response['items']:
            logger.info(f'Все доступные сообщения загружены')
            break
        history_items.extend(response['items'])
        logger.info(f'Загружено {len(history_items)} сообщений')
        time.sleep(REQUEST_DELAY)
        offset += count
    return history_items


def parse_messages(items: list) -> list:
    """Парсинг объектов истории чата и сохранения бэкапа."""
    messages = []
    logger.info(f'Провожу парсинг сообщений и скачиваю файлы...')
    logger.info(f'Это может занять много времени и места на диске')

    for item in items:
        date = get_date(item['date'])
        member = MEMBER_NAMES.get(item['from_id'], f"id_{item['from_id']}")
        text = item['text']
        images = []
        docs = []

        if text:
            messages.append(f'{date} - {member}: {format_text(text)}')

        for attachment in item['attachments']:
            if photo := attachment.get('photo'):
                images.append(get_image_from_message(photo))
            if doc := attachment.get('doc'):
                if doc_url := get_file_from_message(doc):
                    docs.append(doc_url)

        for image in images:
            messages.append(f'{date} - {member}: {image} (файл добавлен)')
        for doc in docs:
            messages.append(f'{date} - {member}: {doc} (файл добавлен)')

    return messages


def format_text(original_text: str) -> str:
    def convert_name(match_obj):
        member_id = re.search(r'\d+', match_obj.group()).group(0)
        return MEMBER_NAMES.get(int(member_id), f'id_{member_id}')

    if REGEXP.search(original_text):
        return re.sub(REGEXP, convert_name, original_text)
    return original_text


def get_image_from_message(photo: dict) -> str:
    """Функция вытаскивает из объекта сообщения изображение."""
    image_name = f"{photo['owner_id']}_{photo['id']}.jpg"
    sizes = sorted(photo['sizes'], key=lambda d: d['type'])
    url = next((sizes[i]['url'] for i in range(len(sizes)) if
                sizes[i]['type'] == 'w'), sizes[-1]['url'])
    return download_file(url, image_name)


def get_file_from_message(doc: dict) -> Optional[str]:
    """
    Функция вытаскивает из объекта сообщения файл.
    Если тип файла не указан в словаре DOC_TYPES, то возвращает None.
    """
    if doc['type'] in DOC_TYPES:
        doc_name = f"{doc['owner_id']}_{doc['id']}{DOC_TYPES[doc['type']]}"
        return download_file(doc['url'], doc_name)


def download_file(url: str, file_name: str) -> str:
    """Функция скачивает файл по ссылке, возвращает название файла."""
    path_to_file = BACKUP_DIR + file_name
    try:
        if not os.path.exists(path_to_file):
            with open(path_to_file, 'wb') as f:
                f.write(requests.get(url).content)
    except Exception as error:
        logger.error(f'Ошибка при скачивании или записи файла: {error}')
    return file_name


def main():
    """Основная логика работы приложения."""
    start_time = datetime.datetime.now()

    if not check_environment_variables():
        logger.critical('Отсутствуют необходимые переменные окружения'
                        'Работа программы завершена')
        sys.exit()

    chat_title = get_chat_title(peer_id=PEER_ID)
    history_items = get_history_items(peer_id=PEER_ID, offset=15300)

    if history_items:
        if not os.path.exists(BACKUP_DIR) and not os.path.isdir(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

        messages = parse_messages(history_items)
        message_file = BACKUP_DIR + f'Чат WhatsApp с {chat_title}.txt'
        logger.info(f'Сохраняю сообщения в файл {message_file}')
        with open(message_file, 'w') as f:
            for message_file in messages:
                f.write(f'{message_file}\n')
    else:
        logger.warning(f'В этом чате нет сообщений')

    end_time = datetime.datetime.now()
    time_delta = end_time - start_time
    logger.info(f'Затрачено секунд: {time_delta.total_seconds()}')


if __name__ == '__main__':
    main()
