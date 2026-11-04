import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database

# توکن ربات تلگرام (تنظیم شده با توکن واقعی شما)
TOKEN = "8624024011:AAF1Vfh6oBM618EpdcXp6OHt0iRhUt0qMxE"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# حالت‌های مختلف مکالمه کاربر با ربات (FSM)
class UserStates(StatesGroup):
    waiting_for_wallet = State()
    waiting_for_txid = State()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    
    # بررسی اینکه آیا کاربر جدید است یا قبلا ثبت‌نام کرده
    # (در اینجا به طور پیش‌فرض یک امتیاز برنز می‌گیرد)
    database.init_db()
    
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 پروفایل و کیف پول من", callback_data="profile")
    builder.button(text="💎 بخش حامیان (الماس)", callback_data="diamond_section")
    builder.button(text="🥇 دعوت از دوستان (طلا)", callback_data="gold_section")
    builder.button(text="🥉 جامعه عمومی (برنز)", callback_data="bronze_section")
    builder.adjust(1)
    
    await message.answer(
        f"سلام {message.from_user.first_name} عزیز! به ربات رسمی تأمین مالی و پاداش **DTF** خوش آمدید.\n\n"
        "با عضویت در این ربات، ۱ امتیاز برنز دریافت کردید. از دکمه‌های زیر برای مدیریت حساب و دریافت امتیازهای بیشتر استفاده کنید:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "profile")
async def show_profile(callback: types.CallbackQuery):
    await callback.message.answer("بخش پروفایل و ثبت کیف پول EVM (به زودی کامل‌تر می‌شود).")
    await callback.answer()

@dp.callback_query(F.data == "diamond_section")
async def diamond_section(callback: types.CallbackQuery):
    await callback.message.answer("💎 بخش حامیان الماس (مخصوص واریز ۶ دلاری و دریافت امتیاز الماس و لینک کانال اختصاصی).")
    await callback.answer()

@dp.callback_query(F.data == "gold_section")
async def gold_section(callback: types.CallbackQuery):
    await callback.message.answer("🥇 بخش امتیاز طلا (لینک رفرال شما برای دعوت دوستان).")
    await callback.answer()

@dp.callback_query(F.data == "bronze_section")
async def bronze_section(callback: types.CallbackQuery):
    await callback.message.answer("🥉 بخش جامعه برنز (دسترسی به اخبار و کانال عمومی).")
    await callback.answer()

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
