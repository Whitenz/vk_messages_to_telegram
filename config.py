"""
Модуль с параметрами необходимые для парсинга и сохранения бэкапа.
Редактировать его не требуется, а личные параметры, такие как TOKEN, PEER_ID,
 MEMBER_NAMES, YOUR_TIMEZONE лучше хранить рядом в файле .env в формате
 ключ=значение. В конфиг они будут подтягиваться с помощью функции getenv.
"""

import argparse
import ast
import logging.config
import os
import re
from datetime import timedelta, timezone

from dotenv import load_dotenv

logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)

load_dotenv()

# версия VK API
API_VERSION = '5.131'
# задержка между запросами к API
REQUEST_DELAY = 0.4
# префикс названия текстового файла
FILE_MESSAGE_NAME = 'Чат WhatsApp с '
# типы скачиваемых документов
DOC_TYPES = {3: '.gif', 4: '.jpg'}
# замена отсылок на члена диалога в тексте его именем
REGEXP_USERNAME = re.compile(r'\[id\d*\|@\w*]')
# часовой пояс относительно UTC заданный целым числом, по умолчанию Мск (+3)
TIMEZONE = timezone(timedelta(hours=int(os.getenv('YOUR_TIMEZONE', 3))))
# токен вашего приложения VK для доступа к VK API
TOKEN = os.getenv('TOKEN')
# ID чата VK (необходимо прибавить +2000000000 к ID, если чат групповой)
PEER_ID = int(os.getenv('PEER_ID', 0))
# словарь с id участника диалога и имени контакта в телефонной книге
MEMBER_NAMES = ast.literal_eval(os.getenv('MEMBER_NAMES', '{}'))
# директория, где будет сохраняться бэкап
BACKUP_DIR = f'backup/{PEER_ID}/'


def get_args():
    """Функция возвращает аргументы, с которыми запущена программа."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=('Программа для экспорта сообщений из VK в Telegram.\n'
                     'Необходимо запускать с указанием аргументов-типов '
                     'данных, которые необходимо загружать из сообщений.\n'
                     'Описание возможных аргументов смотрите ниже.\n'
                     'Бэкап сохраняется в директорию "./backup/id чата/"'
                     )
    )

    parser.add_argument('--text',
                        action='store_true',
                        help='загружать текст из сообщений',
                        )
    parser.add_argument('--photo',
                        action='store_true',
                        help='загружать фотографии из сообщений',
                        )
    parser.add_argument('--doc',
                        action='store_true',
                        help='загружать документы из сообщений (.jpg, .gif)',
                        )
    args = parser.parse_args()
    if not any(vars(args).values()):
        parser.error('не передан ни один тип данных для парсинга сообщений')
    return args
