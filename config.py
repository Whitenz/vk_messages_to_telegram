import ast
import os

from dotenv import load_dotenv

load_dotenv()

API_VERSION = '5.131'  # версия VK API
REQUEST_DELAY = 0.4  # Sleep time between request to API
TOKEN = os.getenv('TOKEN')  # токен вашего приложения VK для доступа к VK API
# словарь с id членов диалога и имени контакта в телефонной книге
# например, {0000000: 'Александр Пушкин'}
MEMBER_NAMES = ast.literal_eval(os.getenv('MEMBER_NAMES'))
PEER_ID = os.getenv('PEER_ID')  # ID чата в VK
GROUP = os.getenv('GROUP')  # ID принадлежит групповому чату?
