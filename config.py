import ast
import os

from dotenv import load_dotenv

load_dotenv()

API_VERSION = '5.131'

# token your vk app
TOKEN = os.getenv('TOKEN')
# dict with members id:'contact's name'
MEMBER_NAMES = ast.literal_eval(os.getenv('MEMBER_NAMES'))
# VK chat id
PEER_ID = os.getenv('PEER_ID')
