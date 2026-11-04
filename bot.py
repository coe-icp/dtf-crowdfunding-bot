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
async def cmd_start(message: types.Message):
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
    builder.button(text="✏️ ثبت یا تغییر کیف پول EVM", callback_data="set_wallet")
    builder.button(text="🔙 بازگشت به منوی اصلی", callback_data="main_menu")
    builder.adjust(1)
    
    text = (
        f"👤 **پروفایل و دارایی‌های شما در DTF:**\n\n"
        f"🔹 آدرس کیف پول EVM:\n`{wallet}`\n\n"
        f"🥉 امتیاز برنز (جامعه): {bronze}\n"
        f"🥇 امتیاز طلا (دعوت دوستان): {gold}\n"
        f"💎 امتیاز الماس (حامیان): {diamond}\n"
        f"وضعیت حامی ویژه: {status_text}\n"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "set_wallet")
async def ask_wallet(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("لطفاً آدرس کیف پول EVM خود (شروع با 0x...) را ارسال کنید:")
    await state.set_state(UserStates.waiting_for_wallet)
    await callback.answer()

@dp.message(UserStates.waiting_for_wallet)
async def save_wallet(message: types.Message, state: FSMContext):
    wallet_address = message.text.strip()
    if not wallet_address.startswith("0x") or len(wallet_address) < 40:
        await message.answer("❌ آدرس کیف پول نامعتبر است. لطفاً یک آدرس معتبر EVM (شروع با 0x) ارسال کنید:")
        return
        
    user_id = message.from_user.id
    conn = sqlite3.connect('dtf_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET evm_wallet = ? WHERE user_id = ?', (wallet_address, user_id))
    conn.commit()
    conn.close()
    
    await state.clear()
    await message.answer("✅ آدرس کیف پول EVM شما با موفقیت ثبت شد!")

@dp.callback_query(F.data == "gold_section")
async def gold_section(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    conn = sqlite3.connect('dtf_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT gold_points FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    my_gold = row[0] if row else 0
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 بازگشت به منوی اصلی", callback_data="main_menu")
    
    text = (
        f"🥇 **بخش امتیاز طلا (دعوت از دوستان):**\n\n"
        f"تا کنون `{my_gold}` نفر با لینک اختصاصی شما وارد شده‌اند!\n\n"
        f"با ارسال لینک زیر به دوستانتان، به ازای هر ورود موفق ۱ امتیاز طلا (سهم از استخر ۲ میلیون DTF) دریافت کنید:\n\n"
        f"🔗 لینک اختصاصی شما:\n`{ref_link}`"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "diamond_section")
async def diamond_section(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 ارسال رسید / TXID واریز ۶ تتر", callback_data="submit_diamond")
    builder.button(text="🔙 بازگشت به منوی اصلی", callback_data="main_menu")
    builder.adjust(1)
    
    text = (
        "💎 **بخش حامیان الماس:**\n\n"
        "مخصوص حامیان گرامی؛ بدون هیچ‌گونه انتظار سود، ۱٪ از نقدینگی بین تمام الماس‌ها توزیع خواهد شد.\n\n"
        "برای پیوستن به این بخش، مبلغ ۶ USDT (در شبکه دلخواه) به آدرس زیر واریز کرده و سپس روی دکمه‌ی زیر جهت ثبت رسید کلیک کنید:\n\n"
        "📍 آدرس کیف پول دریافت:\n`0xYourWalletAddressHereForTest`"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "submit_diamond")
async def ask_diamond_tx(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("لطفاً کد تراکنش (TXID) یا جزئیات واریز ۶ تتر خود را ارسال کنید:")
    await state.set_state(UserStates.waiting_for_diamond_tx)
    await callback.answer()

@dp.message(UserStates.waiting_for_diamond_tx)
async def save_diamond_tx(message: types.Message, state: FSMContext):
    txid = message.text.strip()
    user_id = message.from_user.id
    
    conn = sqlite3.connect('dtf_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET deposit_status = ? WHERE user_id = ?', ('pending', user_id))
    conn.commit()
    conn.close()
    
    await state.clear()
    await message.answer("✅ رسید واریز شما ثبت شد و در صف بررسی ادمین قرار گرفت. پس از تأیید، امتیاز الماس و دسترسی‌های شما فعال خواهد شد!")

@dp.callback_query(F.data == "main_menu")
async def back_to_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 پروفایل و امتیازهای من", callback_data="profile")
    builder.button(text="💎 بخش حامیان (الماس)", callback_data="diamond_section")
    builder.button(text="🥇 دعوت از دوستان (طلا)", callback_data="gold_section")
    builder.button(text="🥉 جامعه عمومی (برنز)", callback_data="bronze_section")
    builder.adjust(1)
    
    await callback.message.edit_text(
        "منوی اصلی ربات تأمین مالی **DTF**:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@dp.callback_query(F.data == "bronze_section")
async def bronze_section(callback: types.CallbackQuery):
    builder.button(text="🔙 بازگشت به منوی اصلی", callback_data="main_menu")
    await callback.message.edit_text("🥉 **جامعه برنز:** دسترسی به اخبار و استخر ۱ میلیون عددی DTF.", reply_markup=builder.as_markup())
    await callback.answer()

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
