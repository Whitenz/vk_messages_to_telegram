import os
import sys
from datetime import datetime

import requests

from config import BACKUP_DIR, TIMEZONE


def format_timestamp(timestamp: str) -> str:
    """Функция форматирует UNIX-время в формат мессенджера Whatsapp."""
    return datetime.fromtimestamp(
        int(timestamp), TIMEZONE).strftime('%d.%m.%Y, %H:%M')


def download_file(url: str, file_name: str) -> str:
    """Функция скачивает файл по ссылке, возвращает название файла."""
    path_to_file = BACKUP_DIR + file_name
    if not os.path.exists(path_to_file):
        try:
            with open(path_to_file, 'wb') as f:
                f.write(requests.get(url).content)
        except Exception as error:
            sys.exit(f'Ошибка при скачивании или записи файла: {error}')
    return file_name
