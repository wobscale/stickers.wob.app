#!/usr/bin/env python3

import botocore.session
import json
import os


def any_left(request, done_stickers):
    for k, v in request.items():
        if k in ('email', 'address'):
            continue
        elif k in done_stickers:
            continue
        else:
            if v > 0:
                return True
    return False


if __name__ == '__main__':
    session = botocore.session.get_session()
    s3 = session.create_client('s3')

    with open(os.path.join(os.path.dirname(__file__), '..', 'stickers.json')) as f:
        stickers = iter(json.load(f).keys())

    fetched = dict()
    done_stickers = set()

    def cb(sticker, uuid):
        if uuid not in fetched:
            fetched[uuid] = json.load(s3.get_object(
                Bucket='stickers-submissions-352b2c6b-d476-4ab5-8f84-83d9f455ccf9',
                Key=f'done/{uuid}',
            )['Body'])
        print(f'Envelope for "{fetched[uuid]["address"][0]}"')
        done = '' if any_left(fetched[uuid], done_stickers) else ' ------> Envelope done'
        if fetched[uuid].get(sticker, 0):
            print(f'Drop {fetched[uuid][sticker]} of "{sticker}"{done}')
        else:
            print(f'-> Skip envelope{done}')

    for sticker in stickers:
        done_stickers.add(sticker)
        print(f'Grab the "{sticker}" stickers...')
        while True:
            response = input('Scan barcode (or "quit"): ')
            if response == 'quit':
                break
            cb(sticker, response)
