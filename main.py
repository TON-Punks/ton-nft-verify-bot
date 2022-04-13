import logging

import requests
import asyncio
import aioschedule as schedule
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, InputTextMessageContent
from aiogram.utils.executor import start_webhook
from config import *


@dp.inline_handler()
async def inline_handler(query: types.InlineQuery):
    """
    Обработка запросов для inline-режима. Вывод списка NFT пользователя в конкретной коллекции
    """
    total_answer = []
    language = english if query.from_user.language_code != 'ru' else russian
    cursor.execute(f"select owner from verify where tgid = '{query.from_user.id}'")
    owner_address = cursor.fetchall()[0][0]
    disintar_address = (await get_ton_addresses(owner_address))['n_b64url']
    nfts = await get_disintar_nfts(disintar_address, 10)
    if len(nfts) == 0:
        nfts = await get_disintar_nfts(owner_address, 10)
    for i in range(len(nfts)):
        nft = nfts[i]
        name = nft['name']
        image = 'https://beta.disintar.io' + nft['image']
        address = nft['address']
        total_answer.append(types.InlineQueryResultArticle(id=name,
                                                           title=name,
                                                           thumb_url=image,
                                                           input_message_content=InputTextMessageContent(
                                                               message_text=f'{language["my_nft"]}\n\n<b>{name}</b><a href="{image}"> </a>\n\n<a href="https://beta.disintar.io/object/{address}">{language["disintar"]}</a>',
                                                               disable_web_page_preview=False,
                                                               parse_mode=ParseMode.HTML)))
    return await query.answer(total_answer, is_personal=True, cache_time=60)


@dp.message_handler(commands=['start'], lambda m: m.chat.id > 0)
async def start_message(msg: types.Message):
    """
    Приветствие
    """
    await bot.send_chat_action(msg.chat.id, 'typing')
    language = english if msg.from_user.language_code != 'ru' else russian
    cursor.execute(f"select * from verify where tgid = '{msg.from_user.id}'")
    verified = len(cursor.fetchall())
    if verified:
        await bot.send_message(msg.chat.id, language['already_verified'], reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text=language['get_privileges'], callback_data='privileges')))
    else:
        await bot.send_message(msg.chat.id, language['start_message'],
                            reply_markup=InlineKeyboardMarkup().add(
                                InlineKeyboardButton(text=language['start_verify'], callback_data='verify')))


@dp.callback_query_handler(lambda c: c.data == 'privileges')
async def privileges(callback_query: types.CallbackQuery):
    language = english if callback_query.from_user.language_code != 'ru' else russian
    cursor.execute(f"select * from verify where tgid = '{callback_query.from_user.id}'")
    verified = len(cursor.fetchall())
    if verified:
        link = await bot.create_chat_invite_link(CHAT_ID, name=f'{callback_query.from_user.id}',
                                                 creates_join_request=True)
        await bot.send_message(callback_query.message.chat.id,
                               f'{language["privileges"]}',
                               reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text=language['join_chat'], url=link.invite_link)).add(
                                   InlineKeyboardButton(text=language['nft_share'], switch_inline_query='')))
        await callback_query.answer()
    else:
        try:
            await callback_query.answer(language['not_verified'], show_alert=True)
        except:
            await bot.send_message(callback_query.message.chat.id, language['not_verified'])


@dp.callback_query_handler(lambda c: c.data == 'verify')
async def verify(callback_query: types.CallbackQuery):
    """
    Отправка сообщения с инструкцией по началу верификации
    """
    await bot.send_chat_action(callback_query.message.chat.id, 'typing')
    language = english if callback_query.from_user.language_code != 'ru' else russian
    await bot.send_message(callback_query.message.chat.id, language['send_nft'])
    try:
        await callback_query.answer()
    except:
        pass


@dp.callback_query_handler(lambda c: c.data != 'verify')
async def verify2(callback_query: types.CallbackQuery):
    """
    Проверка отправки перевода для верификации
    """
    await bot.send_chat_action(callback_query.message.chat.id, 'typing')
    language = english if callback_query.from_user.language_code != 'ru' else russian
    owner_address = callback_query.data
    cursor.execute(f"select * from verify where owner = '{owner_address}'")
    owner_verify = len(cursor.fetchall())
    owner_addresses = await get_ton_addresses(owner_address)
    try:
        if owner_verify != 0:
            raise AssertionError
        result = json.loads(requests.get(
            f'{TONCENTER_BASE}getTransactions?address=EQABh4JBalyRKN42tZB1jevT3BheWqHYjkhSv3zoHldqqRJs&limit=10&to_lt=0&archival=false',
            headers=headers).text)['result']
        isVerified = False
        for i in result:
            transaction = i['in_msg']
            value = transaction['value']
            msg = transaction['message']
            source = transaction['source']
            if (int(value) >= 10000000) and (msg == f"verify{callback_query.from_user.id}") and (
                    source == owner_addresses['b64url']):
                isVerified = True
                break
            else:
                print(value, msg, source, f"verify{callback_query.from_user.id}", owner_addresses)
        if isVerified:
            cursor.execute(
                f"insert into verify (tgid, owner) values ('{callback_query.from_user.id}', '{owner_addresses['b64url']}') on conflict do nothing")
            connect.commit()
            link = await bot.create_chat_invite_link(CHAT_ID, name=f'{callback_query.from_user.id}',
                                                     creates_join_request=True)
            await bot.send_message(callback_query.message.chat.id,
                                   f'{language["verified"]}{link.invite_link.split("://")[1]}',
                                   reply_markup=InlineKeyboardMarkup().add(
                                       InlineKeyboardButton(text=language['nft_share'], switch_inline_query='')))
        else:
            try:
                await callback_query.answer(language['dont_see'], show_alert=True)
            except:
                await bot.send_message(callback_query.message.chat.id, language['dont_see'])
    except Exception as e:
        try:
            await callback_query.answer(language['owner_verified'], show_alert=True)
        except:
            await bot.send_message(callback_query.message.chat.id, language['owner_verified'])
        print(e)
    try:
        await callback_query.answer()
    except:
        pass


@dp.message_handler(lambda m: m.chat.id > 0)
async def check_nft(msg: types.Message):
    """
    Проверка на наличие NFT и его/их принадлежность к коллекции. Отправка сообщения с реквизитами.
    """
    await bot.send_chat_action(msg.chat.id, 'typing')
    language = english if msg.from_user.language_code != 'ru' else russian
    try:
        await asyncio.sleep(1)
        owner_address = (await get_ton_addresses(msg.text))['b64url']
        cursor.execute(f"select * from verify where owner = '{owner_address}'")
        response = cursor.fetchall()
        cursor.execute(f"select * from contest where owner = '{owner_address}'")
        contest = cursor.fetchall()
        if len(response) == 0:
            await asyncio.sleep(1)
            disintar_address = (await get_ton_addresses(owner_address))['n_b64url']
            nfts = await get_disintar_nfts(disintar_address, 1)
            if len(nfts) == 0:
                nfts = await get_disintar_nfts(owner_address, 1)
            if len(nfts) != 0 or len(contest) > 0:
                await bot.send_message(msg.chat.id,
                                        f'{language["send"]} <a href="http://qrcoder.ru/code/?ton%3A%2F%2Ftransfer%2FEQABh4JBalyRKN42tZB1jevT3BheWqHYjkhSv3zoHldqqRJs%3Famount%3D10000000%26text%3Dverify{msg.from_user.id}&4&0"> </a><b>0.01 TON</b>\n\n{language["from"]} <code>{owner_address}</code>\n\n{language["to"]} <code>EQABh4JBalyRKN42tZB1jevT3BheWqHYjkhSv3zoHldqqRJs</code>\n\n'
                                        f'{language["comment"]} <code>verify{msg.from_user.id}</code>\n\n{language["scan_qr"]}',
                                        parse_mode=ParseMode.HTML,
                                        reply_markup=InlineKeyboardMarkup().add(
                                            InlineKeyboardButton(text=language['done'],
                                                                callback_data=owner_address)))
            else:
                await msg.reply(language['no_nfts'])
        else:
            await msg.reply(language['owner_verified'])
    except Exception as e:
        await bot.send_message(msg.chat.id, language['is_it_ton'])
        print(e)


@dp.chat_join_request_handler()
async def islegal(update: types.ChatJoinRequest):
    """
    Обработка запросов на вступление в закрытый чат. Если ссылка не предназначалась пользователю, заявка отклоняется.
    """
    if update.invite_link.creator.id == int(BOT_ID):
        if str(update.invite_link.name) == str(update.from_user.id):
            await update.approve()
        else:
            await update.decline()
        await bot.revoke_chat_invite_link(CHAT_ID, update.invite_link.invite_link)


async def on_startup(dispatcher):
    """
    Создание таблиц в БД, если этого не было сделано ранее
    verify: основная таблица со связками пользователь-адрес
    contest: таблица для хранения адресов, которые не нуждаются в проверке на наличие NFT
    """
    try:
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS verify (tgid int8 NOT NULL, "owner" text NULL, CONSTRAINT verify_tgid_key UNIQUE (tgid));')
        cursor.execute('CREATE TABLE IF NOT EXISTS contest ("owner" text NOT NULL);')
        connect.commit()
    except:
        pass
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    asyncio.create_task(scheduler())


async def on_shutdown(dispatcher):
    await bot.delete_webhook()


async def scheduler():
    schedule.every(90).minutes.do(check_holders)
    while True:
        await schedule.run_pending()
        await asyncio.sleep(1)


async def check_holders():
    """
    Регулярная проверка на наличие у пользователей NFT. В случае продажи и/или передачи всех NFT, верификация снимается
    """
    cursor.execute(f"select * from verify")
    response = cursor.fetchall()
    owners = [x for x in response if x[1] is not None and x[1] != '']
    for owner in owners:
        try:
            tgid, owner_address = owner
            disintar_address = (await get_ton_addresses(owner_address))['n_b64url']
            nfts = await get_disintar_nfts(disintar_address, 1)
            if len(nfts) == 0:
                nfts = await get_disintar_nfts(owner_address, 1)
            cursor.execute(f"select * from contest where owner = '{owner_address}'")
            contest = cursor.fetchall()
            if len(nfts) + len(contest) == 0:
                await kick_user(tgid)
        except Exception as e:
            print(e)
        await asyncio.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
