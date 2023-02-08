import asyncio
import time
import sqlite3
import aioschedule

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from aiogram import Dispatcher, Bot, types, executor
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.markdown import hlink

Token_bot = '5224662237:AAHinmeM1NgsnRAqHIS1Vk55PzOgSwS0i_M'

loop = asyncio.get_event_loop()

bot = Bot(token=Token_bot)
dp = Dispatcher(bot, loop=loop, storage=MemoryStorage())

class Form(StatesGroup):
    last_course = State()
    buy_or_sell = State()
    transaction_amount = State()

@dp.message_handler(commands=['new'])
async def new(message: types.Message):
    await bot.send_message(message.chat.id, 'Курс покупки')

    await Form.last_course.set()

@dp.message_handler(state=Form.last_course)
async def last_course(message: types.Message, state: FSMContext):
    await state.update_data(last_course=message.text)

    user_data = await state.get_data()

    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    One = KeyboardButton('0')
    Two = KeyboardButton('1')
    markup.add(One, Two)

    await bot.send_message(message.chat.id, 'Предмет транзакции\n\n0 - покупка\n1 - продажа', reply_markup=markup)

    await Form.buy_or_sell.set()

@dp.message_handler(state=Form.buy_or_sell)
async def buy_or_sell(message: types.Message, state: FSMContext):
    await state.update_data(buy_or_sell=message.text)

    user_data = await state.get_data()

    await bot.send_message(message.chat.id, 'Сумма транзакции (только цифры)')
    await Form.transaction_amount.set()

@dp.message_handler(state=Form.transaction_amount)
async def transaction_amount(message: types.Message, state: FSMContext):
    await state.update_data(transaction_amount=message.text)

    user_data = await state.get_data()

    await state.finish()

    await bot.send_message(message.chat.id, 'Транзакция внесена')

    try:
        con = sqlite3.connect('data_buy.db')
        cur = con.cursor()

        cur.execute('INSERT INTO information_transaction(last_course, buy_or_sell, transaction_amount) VALUES(?, ?, ?)', [user_data.get('last_course'), user_data.get('buy_or_sell'), user_data.get('transaction_amount')])
        con.commit()
    finally:
        cur.close()
        con.close()

async def analysis():
    url = 'https://p2p.binance.com/ru'
    s = Service('C:/Users/User/Desktop/All/Activity/Python/Задачи/chromedriver.exe')

    try:
        con = sqlite3.connect('data_buy.db')
        cur = con.cursor()

        last_course = cur.execute('SELECT last_course FROM information_transaction').fetchall()[-1][0]
        status_last_transaction = cur.execute('SELECT buy_or_sell FROM information_transaction').fetchall()[-1][0]

    finally:
        cur.close()
        con.close()

    try:
        driver = webdriver.Chrome(service=s)
        driver.get(url=url)
        driver.set_window_size(1920, 1080)
        time.sleep(2)

        if status_last_transaction == 0:
            sell = driver.find_element(By.XPATH, '//div[text()="Продать"]').click()
            time.sleep(2)

        BTC = driver.find_element(By.XPATH, '//h2[text()="BTC"]').click()
        time.sleep(2)

        payment_method = driver.find_element(By.XPATH, '//*[@id="C2Cpaymentfilter_searchbox_payment"]').click()
        time.sleep(2)

        tinkoff = driver.find_element(By.XPATH, '//div[text()="Тинькофф"]').click()
        time.sleep(2)

        input_sum = driver.find_element(By.XPATH, '//*[@id="C2Csearchamount_searchbox_amount"]')
        input_sum.clear()
        input_sum.send_keys('10000')
        time.sleep(2)

        search = driver.find_element(By.XPATH, '//button[text()="Поиск"]').click()
        time.sleep(2)

        response_search = driver.page_source
    finally:
        driver.close()
        driver.quit()

    soup_search = BeautifulSoup(response_search, 'lxml')
    card = soup_search.find('div', 'css-1mf6m87').find('div', 'css-ovjtyv')

    name_seller = card.find('a', id='C2Cofferlistsell_link_merchant').text
    link_seller = card.find('a', id='C2Cofferlistsell_link_merchant').get('href')
    cost = card.find('div', 'css-1m1f8hn').text.replace(',', '')

    lining = hlink(f'{name_seller}', f'https://p2p.binance.com{link_seller}')

    if status_last_transaction == 0:
        if float(cost) >= (float(last_course) + (float(last_course) * 0.015)):
            await bot.send_message(chat_id=520794257,
                                   text=f'''{lining} предложил выгодный офер.\n\nСделка выгодна на {round((float(cost) - float(last_course)) / float(last_course) * 100), 2}%''',
                                   parse_mode='HTML')
    elif status_last_transaction == 1:
        if float(cost) <= (float(last_course) - (float(last_course) * 0.015)):
            await bot.send_message(chat_id=520794257,
                                   text=f'''{lining} предложил выгодный офер.\n\nСделка выгодна на {round((float(cost) - float(last_course)) / float(last_course) * 100), 2}%''',
                                   parse_mode='HTML')
async def scheduler():
    aioschedule.every(20).minutes.do(analysis)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(_):
    asyncio.create_task(scheduler())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)