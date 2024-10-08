import sqlite3


from aiogram.types import Message
from keyboards import keyboards
from aiogram import Router, F
from aiogram.filters import StateFilter, Command

from aiogram.fsm.context import FSMContext
from random import randint
from classes.state_classes import Test, Statistics


router = Router()


accent_test = Test()
user_statistics = Statistics()
con = sqlite3.connect('db.sqlite')
cur = con.cursor()

@router.message(StateFilter(None), Command('accent_test'))
@router.message(StateFilter(None), F.text.lower() == 'правильное ударение')
async def start_test(message: Message, state: FSMContext):
    query = cur.execute(f'''
    SELECT id
    FROM test_type
    WHERE test_name = 'accent_test'
    ''')
    for test_index in query:
        accent_test.test_type_id = test_index[0]
    query = cur.execute(f'''
    SELECT question, right_answer
    FROM questions
    LEFT JOIN test_type
    ON questions.test_type_id = {accent_test.test_type_id}
    ORDER BY RANDOM()
    LIMIT 1
    ''')
    for question, right_answer in query:
        accent_test.question = question
        accent_test.right_answer = right_answer
    await state.set_state(accent_test.test_in_progress)
    await message.answer('Придумываю тест...\n'
                         'Выберите вариант, в котором правильно поставлено ударение\n'
                         'Учитывайте контекст, в круглых скобках\n'
                         'Напишите <b>СТОП</b>, чтобы узнать свои результаты и вернуться к выбору теста'
                         )
    await message.answer(accent_test.question,
                         reply_markup=keyboards.KEYBOARD_ANSWERS)


@router.message(accent_test.test_in_progress, F.text.isdigit())
async def process_answer(message: Message):
    if message.text == accent_test.right_answer:
        user_statistics.right_answers_count += 1
        user_statistics.all_questions += 1
        await message.answer('Правильно!')
    else:
        user_statistics.all_questions += 1
        await message.answer('Неправильно...')
    query = cur.execute(f'''
        SELECT question, right_answer 
        FROM questions
        LEFT JOIN test_type
        ON questions.test_type_id = {accent_test.test_type_id}
        ORDER BY RANDOM()
        LIMIT 1
    ''')
    for question, right_answer in query:
        accent_test.question = question
        accent_test.right_answer = right_answer
    await message.answer(accent_test.question, reply_markup=keyboards.KEYBOARD_ANSWERS)


@router.message(accent_test.test_in_progress, F.text.lower() == 'стоп')
async def cancel_test(message: Message, state: FSMContext):
    user_right_answers_percent = user_statistics.count_right_percent()
    await message.answer(
        f'Ваш результат: {user_right_answers_percent}%\n'
        f'Решено правильно: {user_statistics.right_answers_count}\n'
        f'Всего вопросов: {user_statistics.all_questions}\n'
    )
    user_statistics.clear_stats()
    await state.clear()
    await message.answer('Возврат к выбору теста...',
                         reply_markup=keyboards.KEYBOARD_CHOOSING_TEST)
