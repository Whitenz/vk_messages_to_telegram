import time
import vk

from config import MEMBER_NAMES, API_VERSION, PEER_ID, TOKEN
from date_format import get_date

api = vk.API(access_token=TOKEN, v=API_VERSION)


def get_history(peer_id, count=200, rev=0, group=False, sleep_time=0.4):
    if group:
        peer_id = 2000000000 + int(peer_id)

    time.sleep(sleep_time)
    return api.messages.getHistory(
        count=count,
        peer_id=peer_id,
        rev=rev,
    )


def get_messages(history: dict) -> list:
    items = history['items']
    temp = []

    for item in items:
        date = get_date(item['date'])
        member = MEMBER_NAMES.get(item['from_id'])
        text = item['text']
        urls = []
        for attachment in item['attachments']:
            photo = attachment.get('photo')
            if photo:
                urls.append(photo['sizes'][-1]['url'])

        message = f'{date} - {member}: {text}'
        temp.append(message)
        if urls:
            for url in urls:
                temp.append(f'{date} - {member}: {url} (файл добавлен)')

    return temp


def main():
    history = get_history(peer_id=PEER_ID, group=True, rev=1)
    messages = get_messages(history)

    with open('messages.txt', 'w') as f:
        for message in messages:
            f.write(f'{message}\n')


if __name__ == '__main__':
    main()
