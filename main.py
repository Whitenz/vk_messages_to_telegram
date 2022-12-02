import time
from pprint import pprint

import vk

from config import *
from date_format import get_date

api = vk.API(access_token=TOKEN, v=API_VERSION)


def get_history_items(peer_id, offset=0, count=200, group=False):
    peer_id = int(peer_id)
    if group:
        peer_id += 2000000000

    items = []
    while True:
        request = api.messages.getHistory(
            offset=offset,
            count=count,
            peer_id=peer_id,
            rev=1,
        )
        if not request['items']:
            break

        items.extend(request['items'])
        offset += 200
        time.sleep(REQUEST_DELAY)

    return items


def get_messages(items: list) -> list:
    messages = []

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
    items = get_history_items(peer_id=PEER_ID, group=GROUP, offset=0)
    pprint(items)
    messages = get_messages(items)

    with open('messages.txt', 'w') as f:
        for message in messages:
            f.write(f'{message}\n')


if __name__ == '__main__':
    main()
