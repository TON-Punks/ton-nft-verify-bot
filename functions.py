import asyncio
import json
import logging

import requests

from address import detect_address
from config import russian, english, bot, cursor, connect, CHAT_ID, COLLECTION


async def kick_user(tgid):
    """
    Лишение пользователя верификации и права присутствовать в чате.
    """
    try:
        cursor.execute(
            f"delete from verify where tgid = '{tgid}'")
        connect.commit()
    except Exception as e:
        logging.error(f"Failed to Delete {tgid} from Database\n"
                      f"{e}")
    try:
        await bot.ban_chat_member(CHAT_ID, tgid)
        await bot.unban_chat_member(CHAT_ID, tgid, only_if_banned=True)
    except Exception as e:
        logging.warning(f"Failed to Kick {tgid} from Chat {CHAT_ID}\n"
                        f"{e}")
    try:
        await bot.send_chat_action(tgid, 'typing')
        await bot.send_message(tgid,
                               f'{russian["no_longer_owner"]}\n\n{english["no_longer_owner"]}')
    except Exception as e:
        logging.warning(f"Failed to Send Message to {tgid}\n"
                        f"{e}")


async def get_ton_addresses(address):
    addresses = detect_address(address)
    return {'b64': addresses['bounceable']['b64'],
            'b64url': addresses['bounceable']['b64url'],
            'n_b64': addresses['non_bounceable']['b64'],
            'n_b64url': addresses['non_bounceable']['b64url'],
            'raw': addresses['raw_form']}


async def get_user_nfts(address):
    address = detect_address(address)['bounceable']['b64url']
    await asyncio.sleep(1)
    nfts = []
    all_nfts = json.loads(requests.get(f"https://tonapi.io/v1/nft/getItemsByOwnerAddress?account={address}").text)['nft_items']
    await asyncio.sleep(1)
    sell_nfts = json.loads(requests.get(f"https://tonapi.io/v1/nft/getNftForSale?account={address}").text)
    for market in sell_nfts:
        all_nfts += sell_nfts[market]
    for nft in all_nfts:
        try:
            nft = nft['nft']
        except:
            pass
        try:
            collection = nft['collection_address']
            if (await get_ton_addresses(collection))['b64url'] != COLLECTION:
                name = nft['metadata']['name']
                address = detect_address(nft['address'])['bounceable']['b64url']
                image = nft['metadata']['image']
                nfts += [{'address': address, 'name': name, 'image': image}]
        except:
            pass
    return nfts
