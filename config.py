"""
Модуль с параметрами необходимые для парсинга и сохранения бэкапа.
Редактировать его не требуется, а личные параметры, такие как TOKEN, PEER_ID,
 MEMBER_NAMES, YOUR_TIMEZONE лучше хранить рядом в файле .env в формате
 ключ=значение. В конфиг они будут подтягиваться с помощью функции getenv.
"""

import ast
import logging.config
import os
import re
from datetime import timedelta, timezone

from dotenv import load_dotenv

logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)

load_dotenv()

API_VERSION = '5.131'  # версия VK API
REQUEST_DELAY = 0.4  # задержка между запросами к API
FILE_MESSAGE_NAME = 'Чат WhatsApp с '  # префикс названия текстового файла
DOC_TYPES = {3: '.gif', 4: '.jpg'}  # типы скачиваемых документов
REGEXP_USERNAME = re.compile(r'\[id\d*\|@\w*]')  # замена отсылок на члена диалога в тексте его именем
TIMEZONE = timezone(timedelta(hours=int(os.getenv('YOUR_TIMEZONE', 3))))  # часовой пояс относительно UTC
TOKEN = os.getenv('TOKEN')  # токен вашего приложения VK для доступа к VK API
PEER_ID = int(os.getenv('PEER_ID', 0))  # ID чата VK (+2000000000, если групповой)
MEMBER_NAMES = ast.literal_eval(os.getenv('MEMBER_NAMES', '{}'))  # словарь с id членов диалога и имени контакта в телефонной книге
BACKUP_DIR = f'backup/{PEER_ID}/'
