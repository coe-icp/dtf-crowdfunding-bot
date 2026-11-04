import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import sqlite3
import database

TOKEN = "8624024011:AAF1Vfh6oBM618EpdcXp6OHt0iRhUt0qMxE"

bot = Bot(token=TOKEN)
dp = Dispatcher()

class UserStates(StatesGroup):
    waiting_for_wallet = State()
    waiting_for_diamond_tx = State()

def register_user(user_id, username, referrer_id=None):
    conn = sqlite3.connect('dtf_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, referred_by FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute('''
            INSERT INTO users (user_id, username, referred_by, bronze_points)
            VALUES (?, ?, ?, 1)
        ''', (user_id, username, referrer_id))
        
        if referrer_id and referrer_id != user_id:
            cursor.execute('''
                UPDATE users SET gold_points = gold_points + 1 WHERE user_id = ?
            ''', (referrer_id,))
    else:
        if user[1] is None and referrer_id and referrer_id != user_id:
            cursor.execute('''
                UPDATE users SET referred_by = ? WHERE user_id = ?
            ''', (referrer_id, user_id))
            cursor.execute('''
                UPDATE users SET gold_points = gold_points + 1 WHERE user_id = ?
            ''', (referrer_id,))
            
    conn.commit()
    conn.close()

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    # پاک کردن هرگونه وضعیت معلق قبلی کاربر برای جلوگیری از باگ فریز شدن
    await state.clear()
    
    database.init_db()
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
        except ValueError:
            pass
            
    register_user(user_id, username, referrer_id)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 پروفایل و امتیازهای من", callback_data="profile")
    builder.button(text="💎 بخش حامیان (الماس)", callback_data="diamond_section")
    builder.button(text="🥇 دعوت از دوستان (طلا)", callback_data="gold_section")
    builder.button(text="🥉 جامعه عمومی (برنز)", callback_data="bronze_section")
    builder.adjust(1)
    
    ref_text = f"\n\n🎁 (شما از طریق لینک معرفی وارد شدید و امتیاز دریافت کردید!)" if referrer_id and referrer_id != user_id else ""
    
    await message.answer(
        f"سلام {message.from_user.first_name} عزیز! به ربات رسمی تأمین مالی و پاداش **DTF** خوش آمدید.{ref_text}\n\n"
        "با عضویت در این ربات، ۱ امتیاز برنز دریافت کردید. از دکمه‌های زیر برای مدیریت حساب و بررسی امتیازها استفاده کنید:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "profile")
async def show_profile(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    conn = sqlite3.connect('dtf_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT evm_wallet, bronze_points, gold_points, diamond_points, deposit_status FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    wallet = row[0] if row and row[0] else "هنوز ثبت نشده ❌"
    bronze = row[1] if row else 1
    gold = row[2] if row else 0
    diamond = row[3] if row else 0
    dep_status = row[4] if row else "none"
    
    status_text = "تأیید شده ✅" if dep_status == "approved" else ("در انتظار بررسی ⏳" if dep_status == "pending" else "ثبت نشده ❌")
    
    builder = InlineKeyboardBuilder()
