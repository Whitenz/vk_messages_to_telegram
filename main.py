import datetime
import os
import re
import sys
import time
from argparse import Namespace
from datetime import datetime
from typing import Optional

import vk

from config import (API_VERSION, BACKUP_DIR, DOC_TYPES, get_args, MEMBER_NAMES,
                    PEER_ID, REGEXP_USERNAME, REQUEST_DELAY, TOKEN, logger)
from services import download_file, format_timestamp

api = vk.API(access_token=TOKEN, v=API_VERSION)


def check_environment_variables() -> bool:
    """Функция проверяет доступность необходимых переменных окружения."""
    return all([TOKEN, PEER_ID])


def get_chat_title(peer_id: int) -> str:
    """Функция возвращает заголовок чата для создания файла бэкапа."""
    logger.info(f'Запрашиваю информацию о чате')
    try:
        response = api.messages.getConversationsById(peer_ids=peer_id)
    except Exception as error:
        sys.exit(f'Сбой при получении заголовка чата: {error}')
    type_chat = response['items'][0]['peer']['type']
    if type_chat == 'chat':
        return response['items'][0]['chat_settings']['title']
    elif type_chat == 'user':
        return MEMBER_NAMES.get(peer_id, f'id{peer_id}')
    return f'id{peer_id}'


def add_missing_members(peer_id: int, member_names: dict) -> None:
    """Функция дополняет словарь имен участников чата."""
    logger.info(f'Подгружаю недостающую информацию о членах чата')
    try:
        response = api.messages.getConversationMembers(peer_id=peer_id)
    except Exception as error:
        sys.exit(f'Сбой при загрузке информации о членах чата: {error}')
    for profile in response['profiles']:
        if profile['id'] not in member_names:
            fullname = f"{profile['first_name']} {profile['last_name']}"
            member_names |= {profile['id']: fullname}


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
            sys.exit(f'Сбой при загрузке сообщений: {error}')

        if not response['items']:
            logger.info(f'Все доступные сообщения загружены')
            break

        history_items.extend(response['items'])
        logger.info(f'Загружено {len(history_items)} сообщений')
        time.sleep(REQUEST_DELAY)
        offset += count
    return history_items


def parse_messages(items: list, args: Namespace) -> list:
    """Парсинг истории чата. Возвращает подготовленные сообщения."""
    start_date = format_timestamp(items[0]['date'])
    start_member = MEMBER_NAMES.get(items[0]['from_id'],
                                    f"id{items[0]['from_id']}")
    start_message = f'{start_date} - {start_member}: Ожидание сообщения'
    messages = [start_message]  # для корректного импорта в ТГ

    logger.info(f'Провожу парсинг сообщений и скачиваю файлы...')
    logger.info(f'Это может занять много времени и места на диске')

    for item in items:
        date = format_timestamp(item['date'])
        member = MEMBER_NAMES.get(item['from_id'], f"id{item['from_id']}")
        text = item['text']
        images = []
        docs = []

        if args.text and text:
            messages.append(f'{date} - {member}: {format_text(text)}')
        for attachment in item['attachments']:
            if args.photo and (photo := attachment.get('photo')):
                images.append(get_image_from_message(photo))
            if args.doc and (doc := attachment.get('doc')):
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
        return MEMBER_NAMES.get(int(member_id), f'id{member_id}')

    if REGEXP_USERNAME.search(original_text):
        return re.sub(REGEXP_USERNAME, convert_name, original_text)
    return original_text


def get_image_from_message(photo: dict) -> str:
    """
    Функция вытаскивает из объекта сообщения изображение в наилучшем качестве.
    Возвращает имя изображения.
    """
    max_size = max(photo['sizes'], key=lambda x: x['width'])
    url = max_size['url']
    image_name = f"{photo['owner_id']}_{photo['id']}.jpg"
    return download_file(url, image_name)


def get_file_from_message(doc: dict) -> Optional[str]:
    """
    Функция вытаскивает из объекта сообщения файл. Возвращает название.
    Если тип файла не указан в словаре DOC_TYPES, то возвращает None.
    """
    if doc['type'] in DOC_TYPES:
        doc_name = f"{doc['owner_id']}_{doc['id']}{DOC_TYPES[doc['type']]}"
        return download_file(doc['url'], doc_name)


def main():
    """Основная логика работы приложения."""
    start_time = datetime.now()
    args = get_args()
    if not check_environment_variables():
        sys.exit('Отсутствуют необходимые переменные окружения. '
                 'Работа программы завершена')

    chat_title = get_chat_title(peer_id=PEER_ID)
    add_missing_members(peer_id=PEER_ID, member_names=MEMBER_NAMES)
    history_items = get_history_items(peer_id=PEER_ID, offset=0)

    if history_items:
        if not os.path.exists(BACKUP_DIR) and not os.path.isdir(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

        messages = parse_messages(history_items, args)
        message_file = BACKUP_DIR + f'Чат WhatsApp с {chat_title}.txt'
        logger.info(f'Сохраняю сообщения в файл {message_file}')

        try:
            with open(message_file, mode='w', encoding='utf-8') as f:
                f.write('\n'.join(messages))
        except Exception as error:
            sys.exit(f'Ошибка при записи в файл {message_file}: {error}')

    else:
        logger.warning(f'В этом чате нет сообщений')

    end_time = datetime.now()
    logger.info(f'Затрачено секунд: {(end_time - start_time).total_seconds()}')


if __name__ == '__main__':
    main()
