import datetime
import os
import re
import sys
import time
from datetime import datetime
from typing import Optional

import vk

from config import (API_VERSION, BACKUP_DIR, DOC_TYPES, logger, MEMBER_NAMES,
                    PEER_ID, REGEXP_USERNAME, REQUEST_DELAY, TOKEN)
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
        logger.error(f'Сбой при получении заголовка чата: {error}')
        sys.exit()
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
        logger.error(f'Сбой при загрузке информации о членах чата: {error}')
        sys.exit()
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
    """Парсинг истории чата. Возвращает подготовленные сообщения."""
    messages = []
    logger.info(f'Провожу парсинг сообщений и скачиваю файлы...')
    logger.info(f'Это может занять много времени и места на диске')

    for item in items:
        date = format_timestamp(item['date'])
        member = MEMBER_NAMES.get(item['from_id'], f"id{item['from_id']}")
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

    if REGEXP_USERNAME.search(original_text):
        return re.sub(REGEXP_USERNAME, convert_name, original_text)
    return original_text


def get_image_from_message(photo: dict) -> str:
    """
    Функция вытаскивает из объекта сообщения изображение.
    Возвращает имя изображения.
    """
    image_name = f"{photo['owner_id']}_{photo['id']}.jpg"
    sizes = sorted(photo['sizes'], key=lambda d: d['type'])
    url = next((sizes[i]['url'] for i in range(len(sizes)) if
                sizes[i]['type'] == 'w'), sizes[-1]['url'])
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

    if not check_environment_variables():
        logger.critical('Отсутствуют необходимые переменные окружения. '
                        'Работа программы завершена')
        sys.exit()

    chat_title = get_chat_title(peer_id=PEER_ID)
    add_missing_members(peer_id=PEER_ID, member_names=MEMBER_NAMES)
    history_items = get_history_items(peer_id=PEER_ID, offset=0)

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

    end_time = datetime.now()
    time_delta = end_time - start_time
    logger.info(f'Затрачено секунд: {time_delta.total_seconds()}')


if __name__ == '__main__':
    main()
