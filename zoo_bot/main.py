import asyncio
import json
import logging

from aiogram import Bot, Dispatcher, types, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InputFile
from aiogram.filters import Command
from aiogram import F
from collections import Counter

API_TOKEN = ""

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()
router = Router()

class Quiz(StatesGroup):
    Q1 = State()
    Q2 = State()
    Q3 = State()
    Q4 = State()

questions = [
    {
        "text": "Какой отдых вам ближе?",
        "options": [
            {"text": "Спокойный и уединённый", "traits": ["интроверт", "спокойствие"]},
            {"text": "Активный и экстремальный", "traits": ["энергия", "активность"]},
            {"text": "Исследовать новое", "traits": ["любопытство", "интеллект"]}
        ]
    },
    {
        "text": "Где бы вы хотели жить?",
        "options": [
            {"text": "В горах", "traits": ["независимость"]},
            {"text": "В воде или рядом с ней", "traits": ["гибкость", "интуиция"]},
            {"text": "В лесу", "traits": ["осторожность", "наблюдательность"]}
        ]
    },
    {
        "text": "Какая ваша любимая еда?",
        "options": [
            {"text": "Овощи и фрукты", "traits": ["здоровье"]},
            {"text": "Мясо", "traits": ["сила", "смелость"]},
            {"text": "Рыба и морепродукты", "traits": ["интуиция", "вода"]}
        ]
    },
    {
        "text": "Какой ваш главный плюс?",
        "options": [
            {"text": "Верность и забота", "traits": ["преданность"]},
            {"text": "Решительность и сила", "traits": ["сила", "смелость"]},
            {"text": "Ум и наблюдательность", "traits": ["интеллект", "наблюдательность"]}
        ]
    }
]

animals = [
    {
        "name": "Дикобраз",
        "traits": ["интроверт", "спокойствие", "наблюдательность"],
        "description": "Да ты дикобраз! Независимый, немного колючий, но очень заботливый по отношению к своим. Именно такой живёт в Московском зоопарке.",
        "image": "porcupine.jpg"
    },
    {
        "name": "Тигр",
        "traits": ["сила", "смелость", "энергия", "активность"],
        "description": "Ты — тигр! Яркий, смелый и решительный. Как наш амурский тигр, ты не боишься идти вперёд.",
        "image": "tiger.jpg"
    },
    {
        "name": "Выдра",
        "traits": ["гибкость", "вода", "интуиция", "здоровье"],
        "description": "Ты — выдра! Весёлый, общительный и отлично адаптируешься к любой ситуации. Наши выдры тебя поймут!",
        "image": "otter.jpg"
    },
    {
        "name": "Филин",
        "traits": ["интеллект", "наблюдательность", "осторожность"],
        "description": "Ты — филин! Умный, проницательный и тихий наблюдатель. Настоящий ночной стратег, как наш филин в зоопарке.",
        "image": "owl.jpg"
    }
]

user_data = {}


@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(Quiz.Q1)
    await state.update_data(traits=[])
    await send_question(message, 0)

def build_keyboard(question):
    kb = InlineKeyboardBuilder()
    for idx, opt in enumerate(question["options"]):
        kb.button(text=opt["text"], callback_data=str(idx))
    return kb.as_markup()

async def send_question(message: Message, index: int):
    q = questions[index]
    await message.answer(q["text"], reply_markup=build_keyboard(q))

@dp.callback_query(Quiz.Q1, F.data.in_(["0", "1", "2"]))
async def answer_q1(callback: CallbackQuery, state: FSMContext):
    await process_answer(callback, state, 0, Quiz.Q2)

@dp.callback_query(Quiz.Q2, F.data.in_(["0", "1", "2"]))
async def answer_q2(callback: CallbackQuery, state: FSMContext):
    await process_answer(callback, state, 1, Quiz.Q3)

@dp.callback_query(Quiz.Q3, F.data.in_(["0", "1", "2"]))
async def answer_q3(callback: CallbackQuery, state: FSMContext):
    await process_answer(callback, state, 2, Quiz.Q4)

@dp.callback_query(Quiz.Q4, F.data.in_(["0", "1", "2"]))
async def answer_q4(callback: CallbackQuery, state: FSMContext):
    await process_answer(callback, state, 3, None)
    await show_result(callback.message, state)
    await state.clear()

async def process_answer(callback: CallbackQuery, state: FSMContext, question_idx: int, next_state):
    idx = int(callback.data)
    traits = questions[question_idx]["options"][idx]["traits"]
    data = await state.get_data()
    data["traits"].extend(traits)
    await state.update_data(traits=data["traits"])
    await callback.answer()
    if next_state:
        await state.set_state(next_state)
        await send_question(callback.message, question_idx + 1)

async def show_result(message: Message, state: FSMContext):
    data = await state.get_data()
    trait_counter = Counter(data["traits"])
    scored = []
    for animal in animals:
        score = sum(trait_counter[t] for t in animal["traits"])
        scored.append((score, animal))
    best = sorted(scored, key=lambda x: x[0], reverse=True)[0][1]

    img = InputFile(best["image"])
    text = f"{best['description']}\n\nХочешь узнать, как стать опекуном?"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Узнать больше ", url="https://moscowzoo.ru/support/guardianship/")],
            [InlineKeyboardButton(text="Попробовать ещё раз", callback_data="restart")]
        ]
    )
    await message.answer_photo(photo=img, caption=text, reply_markup=kb)

@dp.callback_query(F.data == "restart")
async def restart(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Quiz.Q1)
    await state.update_data(traits=[])
    await callback.answer()
    await send_question(callback.message, 0)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot))
