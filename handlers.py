from aiogram import types
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.types import Message, MediaGroup
from aiogram.types import InputMediaDocument
from aiogram.dispatcher.filters.state import State, StatesGroup
import re
from datetime import datetime

incomes = []
expenses = []
income_categories = ['Зарплата', 'Продажа', 'Другое']
expense_categories = ['Продукты', 'Рестораны', 'Другое']


class Form(StatesGroup):
    add_custom_income_category = State()
    add_income_amount = State()
    add_custom_expense_category = State()
    add_expense_amount = State()
    statement_start_date = State()
    statement_end_date = State()


async def start_command(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Добавить доход", "Добавить расход", "Получить выписку из банка")
    await message.answer("Добро пожаловать в Money Keeper Bot!", reply_markup=kb)


async def begin_command(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Добавить доход", "Добавить расход", "Получить выписку из банка")
    await message.answer("Выберите действие", reply_markup=kb)


async def add_income(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for category in income_categories:
        kb.add(category)
    kb.add("Назад")
    await message.answer("Выберите категорию:", reply_markup=kb)


async def select_income_category(message: types.Message):
    if message.text == "Другое":
        await message.answer("Введите название категории:")
        await Form.add_custom_income_category.set()
    elif message.text == "Назад":
        await begin_command(message)
    else:
        await message.answer("Введите сумму:")
        await Form.add_income_amount.set()


async def add_expense(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for category in expense_categories:
        kb.add(category)
    kb.add("Назад")
    await message.answer("Выберите категорию:", reply_markup=kb)


async def select_expense_category(message: types.Message):
    if message.text == "Другое":
        await message.answer("Введите название категории:")
        await Form.add_custom_expense_category.set()
    elif message.text == "Назад":
        await begin_command(message)
    else:
        await message.answer("Введите сумму:")
        await Form.add_expense_amount.set()


async def request_statement(message: types.Message):
    await message.answer("Введите дату начала (dd.mm.yyyy):")
    await Form.statement_start_date.set()


async def custom_income_category(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['custom_income_category'] = message.text
    await message.answer("Введите сумму:")
    await Form.add_income_amount.set()


async def save_income(message: types.Message, state: FSMContext):
    if message.text == 'Назад':
        await state.finish()
        await begin_command(message)
    else:
        try:
            income_amount = float(message.text)
            async with state.proxy() as data:
                category = data.get('custom_income_category', message.text)
                incomes.append({"category": category, "amount": income_amount})
            await message.answer("Отлично! Ваш доход записан.")
            await state.finish()
            await begin_command(message)
        except ValueError:
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("Назад")
            await message.answer("Введите корректную сумму:", reply_markup=kb)
            await Form.add_expense_amount.set()


async def custom_expense_category(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['custom_expense_category'] = message.text
    await message.answer("Введите сумму:")
    await Form.add_expense_amount.set()


async def save_expense(message: types.Message, state: FSMContext):
    if message.text == 'Назад':
        await state.finish()
        await begin_command(message)
    else:
        try:
            expense_amount = float(message.text)
            async with state.proxy() as data:
                category = data.get('custom_expense_category', message.text)
                expenses.append({"category": category, "amount": expense_amount})
            await message.answer("Отлично! Ваш расход записан.")
            await state.finish()
            await begin_command(message)
        except ValueError:
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("Назад")
            await message.answer("Введите корректную сумму:", reply_markup=kb)
            await Form.add_expense_amount.set()


async def get_statement_start_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['start_date'] = message.text
    if re.search("^(0[0-9]|1[0-9]|2[0-9]|3[0-1])(.|-)(0[1-9]|1[0-2])(.|-|)20[0-9][0-9]$", data['start_date']):
        await message.answer("Введите дату окончания (dd.mm.yyyy):")
        await Form.statement_end_date.set()
    else:
        if message.text == "Назад":
            await state.finish()
            await begin_command(message)
        else:
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("Назад")
            await message.answer("Введите корректную дату начала", reply_markup=kb)
            await Form.statement_start_date.set()


async def get_statement_end_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['end_date'] = message.text
    if re.search("^(0[0-9]|1[0-9]|2[0-9]|3[0-1])(.|-)(0[1-9]|1[0-2])(.|-|)20[0-9][0-9]$",
                 data['end_date']) and datetime.strptime(data['start_date'], '%d.%m.%Y') < datetime.strptime(
            data['end_date'], '%d.%m.%Y'):
        media = MediaGroup()
        media.attach(InputMediaDocument(open('pdf.pdf', 'rb')))
        await message.reply_media_group(media=media)
        await message.answer('Выписка получена')
        await state.finish()
        await begin_command(message)
    else:
        if message.text == "Назад":
            await state.finish()
            await begin_command(message)
        else:
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("Назад")
            await message.answer("Введите корректную дату окончания", reply_markup=kb)
            await Form.statement_end_date.set()


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_command, Command("start"))
    dp.register_message_handler(add_income, Text(equals="Добавить доход"))
    dp.register_message_handler(select_income_category, Text(equals=['Зарплата', 'Продажа', 'Другое', 'Назад']))
    dp.register_message_handler(add_expense, Text(equals="Добавить расход"))
    dp.register_message_handler(select_expense_category, Text(equals=['Продукты', 'Рестораны', 'Другое', 'Назад']))
    dp.register_message_handler(request_statement, Text(equals="Получить выписку из банка"))
    dp.register_message_handler(custom_income_category, state=Form.add_custom_income_category)
    dp.register_message_handler(save_income, state=Form.add_income_amount)
    dp.register_message_handler(custom_expense_category, state=Form.add_custom_expense_category)
    dp.register_message_handler(save_expense, state=Form.add_expense_amount)
    dp.register_message_handler(get_statement_start_date, state=Form.statement_start_date)
    dp.register_message_handler(get_statement_end_date, state=Form.statement_end_date)