import json
import requests
import os
from aiogram import Bot
from aiogram.dispatcher import Dispatcher
import psycopg2

DATABASE = os.getenv('DATABASE_URL')
TOKEN = os.getenv('BOT_TOKEN')
BOT_ID = TOKEN.split(':')[0]
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')
CHAT_ID = int(os.getenv('CHAT_ID'))
COLLECTION = os.getenv('COLLECTION')

WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.getenv('PORT', default=8000)

API_TOKEN = os.getenv('TONCENTER_API_KEY')

TONCENTER_BASE = 'https://toncenter.com/api/v2/'
headers = {
    'cookie': 'csrftoken=vO44viQbEDlbcKiLz56aaE8tLmjzc5XtVqUTZo6zgItxRNehF7VRGlCVdQR3dul9',
    'x-csrftoken': 'vO44viQbEDlbcKiLz56aaE8tLmjzc5XtVqUTZo6zgItxRNehF7VRGlCVdQR3dul9',
    'referer': 'https://beta.disintar.io/object/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'}

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

connect = psycopg2.connect(DATABASE)
cursor = connect.cursor()

english = json.loads(open('en.json', 'r').read())
english['my_nft'] = f'I have passed <a href="tg://user?id={BOT_ID}">verification</a>. This is my NFT:'

russian = json.loads(open('ru.json', 'rb').read())
russian['my_nft'] = f'Я прошёл <a href="tg://user?id={BOT_ID}">верификацию</a>. Это мой NFT:'


async def kick_user(tgid):
    """
    Лишение пользователя верификации и права присутствовать в чате.
    """
    try:
        cursor.execute(
            f"delete from verify where tgid = '{tgid}'")
        connect.commit()
    except Exception as e:
        print(e)
    try:
        await bot.ban_chat_member(CHAT_ID, tgid)
        await bot.unban_chat_member(CHAT_ID, tgid, only_if_banned=True)
    except Exception as e:
        print(e)
    try:
        await bot.send_chat_action(tgid, 'typing')
        await bot.send_message(tgid,
                               f'{russian["no_longer_owner"]}\n\n{english["no_longer_owner"]}')
    except Exception as e:
        print(e)


async def get_ton_addresses(address):
    response = \
        json.loads(requests.get(f'{TONCENTER_BASE}detectAddress?address={address}&api_key={API_TOKEN}').text)[
            'result']
    return {'b64': response['bounceable']['b64'],
            'b64url': response['bounceable']['b64url'],
            'n_b64': response['non_bounceable']['b64'],
            'n_b64url': response['non_bounceable']['b64url']}


async def get_disintar_nfts(address, limit):
    return json.loads(requests.post('https://beta.disintar.io/api/get_entities/', headers=headers,
                                    data={'entity_name': 'NFT', 'order_by': '[]',
                                          'filter_by': '[{"name":"owner__wallet_address","value":"' + address + '"},{"name":"collection__address","value":["' + COLLECTION + '"],"operator":"in"}]',
                                          'limit': limit,
                                          'page': 0}).text)['data']