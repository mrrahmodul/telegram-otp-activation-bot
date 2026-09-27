"""
Telegram OTP Activation Bot using telebot with Hadi SMS API integration
Works with Pydroid 3 and standard Python environments.

This version has credentials hardcoded for direct use.

Install:
    pip install pyTelegramBotAPI httpx
"""

import logging
import re
import time
from threading import Thread
from typing import Any, Dict, Optional

import httpx
import telebot
from telebot import types

# ==========================================
# CONFIG - CREDENTIALS HARDCODED
# ==========================================
BOT_TOKEN = "8755895664:AAGBeBALGF0tkYt8diPtbyqJjcNhO_C60ws"
HADI_SMS_API_KEY = "QlJVQ0VBUzRohnRrZWlki0V0YYNXZWlUdIJValaIV0FGcpBCRoWGVQ=="
HADI_SMS_BASE_URL = "http://smshadi.net"

HADI_SMS_API_PREFIX = "/api/v1"
USE_TOKEN_PREFIX = False

OTP_TIMEOUT_SECONDS = 180
POLL_INTERVAL_SECONDS = 5

# ==========================================
# LOGGING
# ==========================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

print("=" * 60)
print("✅ Loading bot with updated credentials...")
print(f"✅ Bot Token loaded: {BOT_TOKEN[:20]}...")
print(f"✅ Hadi SMS Base URL: {HADI_SMS_BASE_URL}")
print("=" * 60)

try:
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
    print("✅ Bot initialized successfully!")
    print("=" * 60)
except Exception as e:
    print(f"❌ Failed to initialize bot: {e}")
    print("=" * 60)
    raise

# ==========================================
# SERVICE / COUNTRY OPTIONS
# ==========================================
SERVICE_OPTIONS = {
    "facebook": "Facebook",
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "telegram": "Telegram",
    "whatsapp": "WhatsApp",
    "snapchat": "Snapchat",
    "google": "Google",
    "twitter": "Twitter",
    "discord": "Discord",
    "viber": "Viber",
    "imo": "IMO",
    "linkedin": "LinkedIn",
    "uber": "Uber",
    "airbnb": "Airbnb",
}

COUNTRY_OPTIONS = {
    "US": "United States",
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "MY": "Myanmar",
    "AT": "Austria",
    "TR": "Turkey",
    "AE": "United Arab Emirates",
    "RU": "Russia",
    "UA": "Ukraine",
    "PL": "Poland",
    "CZ": "Czech Republic",
    "NL": "Netherlands",
    "SE": "Sweden",
    "NO": "Norway",
    "DK": "Denmark",
    "BR": "Brazil",
    "IN": "India",
    "ID": "Indonesia",
    "PH": "Philippines",
    "TH": "Thailand",
    "VN": "Vietnam",
    "SG": "Singapore",
    "HK": "Hong Kong",
    "JP": "Japan",
    "KR": "South Korea",
    "CN": "China",
    "MX": "Mexico",
    "AR": "Argentina",
    "ES": "Spain",
    "IT": "Italy",
}

USER_STATE: Dict[int, Dict[str, Any]] = {}

# ==========================================
# HADI SMS CLIENT
# ==========================================
class HadiSmsClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = 30.0

    def _auth_header(self) -> Dict[str, str]:
        auth = f"Token {self.api_key}" if USE_TOKEN_PREFIX else f"Bearer {self.api_key}"
        return {
            "Authorization": auth,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self.base_url}{HADI_SMS_API_PREFIX}{path}"

    def get_services(self) -> Dict[str, Any]:
        try:
            response = httpx.get(self._url("/services"), headers=self._auth_header(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.exception("Failed to fetch Hadi SMS services")
            return {"status": "error", "error": str(e)}

    def get_countries(self) -> Dict[str, Any]:
        try:
            response = httpx.get(self._url("/countries"), headers=self._auth_header(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.exception("Failed to fetch Hadi SMS countries")
            return {"status": "error", "error": str(e)}

    def get_balance(self) -> Dict[str, Any]:
        try:
            response = httpx.get(self._url("/balance"), headers=self._auth_header(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.exception("Failed to fetch Hadi SMS balance")
            return {"status": "error", "error": str(e)}

    def request_number(self, service: str, country: str) -> Dict[str, Any]:
        payload = {"service": service.lower(), "country": country.upper()}
        try:
            response = httpx.post(
                self._url("/order"),
                headers=self._auth_header(),
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.exception("Failed to request number from Hadi SMS")
            return {"status": "error", "error": str(e)}

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        try:
            response = httpx.get(
                self._url(f"/order/{order_id}/status"),
                headers=self._auth_header(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.exception(f"Failed to get order status for {order_id}")
            return {"status": "error", "error": str(e)}

    def get_sms(self, order_id: str) -> Dict[str, Any]:
        try:
            response = httpx.get(
                self._url(f"/order/{order_id}/sms"),
                headers=self._auth_header(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.exception(f"Failed to fetch SMS for order {order_id}")
            return {"status": "error", "error": str(e)}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        try:
            response = httpx.post(
                self._url(f"/order/{order_id}/cancel"),
                headers=self._auth_header(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.exception(f"Failed to cancel order {order_id}")
            return {"status": "error", "error": str(e)}

hadisms = HadiSmsClient(HADI_SMS_API_KEY, HADI_SMS_BASE_URL)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_user_state(user_id: int) -> Dict[str, Any]:
    if user_id not in USER_STATE:
        USER_STATE[user_id] = {
            "service": "facebook",
            "country": "US",
            "provider": "hadisms",
            "current_number": None,
            "last_order_id": None,
        }
    return USER_STATE[user_id]

def format_service_name(service_key: str) -> str:
    return SERVICE_OPTIONS.get(service_key.lower(), service_key.title())

def format_country_name(country_key: str) -> str:
    return COUNTRY_OPTIONS.get(country_key.upper(), country_key.upper())

def extract_otp_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    match = re.search(r"\b(\d{4,6})\b", text)
    if match:
        return match.group(1)
    match = re.search(r"code[\s:]+(\d{4,6})", text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

# ==========================================
# KEYBOARDS
# ==========================================
def build_main_keyboard(user_state: Dict[str, Any]) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    service = format_service_name(user_state.get("service", "facebook"))
    country = format_country_name(user_state.get("country", "US"))

    markup.row(
        types.InlineKeyboardButton("💳 Get Number", callback_data="get_number"),
        types.InlineKeyboardButton("🔄 Request New", callback_data="new_number"),
    )
    markup.row(
        types.InlineKeyboardButton(f"📱 Service: {service}", callback_data="change_service"),
        types.InlineKeyboardButton(f"🌍 Country: {country}", callback_data="change_country"),
    )
    markup.add(types.InlineKeyboardButton("💰 Check Balance", callback_data="check_balance"))
    return markup

def build_service_keyboard() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    services = sorted(SERVICE_OPTIONS.items())
    for i in range(0, len(services), 2):
        row = []
        row.append(types.InlineKeyboardButton(services[i][1], callback_data=f"set_service:{services[i][0]}"))
        if i + 1 < len(services):
            row.append(types.InlineKeyboardButton(services[i + 1][1], callback_data=f"set_service:{services[i + 1][0]}"))
        markup.row(*row)
    markup.add(types.InlineKeyboardButton("← Back", callback_data="main_menu"))
    return markup

def build_country_keyboard() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    countries = sorted(COUNTRY_OPTIONS.items())
    for i in range(0, len(countries), 2):
        row = []
        row.append(types.InlineKeyboardButton(f"{countries[i][1]} ({countries[i][0]})", callback_data=f"set_country:{countries[i][0]}"))
        if i + 1 < len(countries):
            row.append(types.InlineKeyboardButton(f"{countries[i + 1][1]} ({countries[i + 1][0]})", callback_data=f"set_country:{countries[i + 1][0]}"))
        markup.row(*row)
    markup.add(types.InlineKeyboardButton("← Back", callback_data="main_menu"))
    return markup

# ==========================================
# OTP POLLING
# ==========================================
def poll_hadi_sms_for_otp(order_id: str, chat_id: int, user_state: Dict[str, Any]) -> None:
    started_at = time.time()
    logger.info(f"Starting OTP polling for order_id={order_id}")

    while time.time() - started_at < OTP_TIMEOUT_SECONDS:
        try:
            response = hadisms.get_sms(order_id)

            if response.get("status") == "error":
                logger.warning(f"Hadi SMS get_sms error: {response.get('error')}")
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            sms_messages = response.get("sms") or response.get("messages") or response.get("data") or []

            if isinstance(sms_messages, dict):
                sms_messages = [sms_messages]

            if isinstance(sms_messages, list):
                for item in sms_messages:
                    if not isinstance(item, dict):
                        continue

                    text = item.get("text") or item.get("message") or item.get("sms") or ""
                    otp = extract_otp_from_text(str(text))
                    if otp:
                        bot.send_message(chat_id, f"✅ <b>OTP Received!</b>\n\nCode: <code>{otp}</code>\n\nMessage: {text}", parse_mode="HTML")
                        logger.info(f"OTP sent to user {chat_id}")
                        return

            time.sleep(POLL_INTERVAL_SECONDS)

        except Exception as e:
            logger.exception(f"Error during Hadi SMS polling: {e}")
            time.sleep(POLL_INTERVAL_SECONDS)

    logger.warning(f"OTP polling timed out after {OTP_TIMEOUT_SECONDS}s")
    bot.send_message(
        chat_id,
        "⏰ <b>Timeout</b>\n\nNo SMS received within 3 minutes.\nYou can request a new number.",
        parse_mode="HTML",
        reply_markup=build_main_keyboard(user_state),
    )

# ==========================================
# TELEGRAM HANDLERS
# ==========================================
@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = message.from_user.id
    user_state = get_user_state(user_id)
    text = (
        "👋 <b>Welcome to OTP Activation Bot</b>\n\n"
        "Powered by Hadi SMS API\n\n"
        "Choose an action below:"
    )
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=build_main_keyboard(user_state),
    )

@bot.message_handler(commands=["help"])
def handle_help(message):
    user_id = message.from_user.id
    user_state = get_user_state(user_id)
    text = (
        "ℹ️ <b>Available Commands</b>\n\n"
        "<b>Commands:</b>\n"
        "/start - Open main menu\n"
        "/help - Show this help\n"
        "/balance - Check Hadi SMS balance\n"
        "/status - Check last order status\n\n"
        "<b>Features:</b>\n"
        "✅ Get fresh phone numbers\n"
        "✅ Auto-detect verification codes\n"
        "✅ Multi-service support\n"
        "✅ Multi-country support\n"
        "✅ Real-time OTP delivery\n"
        "✅ Balance tracking\n"
        "✅ Order management"
    )
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=build_main_keyboard(user_state),
    )

@bot.message_handler(commands=["balance"])
def handle_balance(message):
    user_id = message.from_user.id
    user_state = get_user_state(user_id)

    bot.send_message(message.chat.id, "🔄 Checking balance...")
    result = hadisms.get_balance()

    if result.get("status") == "error":
        bot.send_message(
            message.chat.id,
            f"❌ Failed to get balance: {result.get('error')}",
            reply_markup=build_main_keyboard(user_state),
        )
        return

    balance = result.get("balance") or result.get("amount") or "Unknown"
    currency = result.get("currency") or "USD"

    text = (
        f"💰 <b>Hadi SMS Account Balance</b>\n\n"
        f"Balance: <code>{balance}</code> {currency}"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=build_main_keyboard(user_state),
    )

@bot.message_handler(commands=["status"])
def handle_status(message):
    user_id = message.from_user.id
    user_state = get_user_state(user_id)
    order_id = user_state.get("last_order_id")

    if not order_id:
        bot.send_message(
            message.chat.id,
            "No active order. Get a number first!",
            reply_markup=build_main_keyboard(user_state),
        )
        return

    bot.send_message(message.chat.id, "🔍 Checking order status...")
    order_status = hadisms.get_order_status(order_id)

    if order_status.get("status") == "error":
        bot.send_message(
            message.chat.id,
            f"❌ Error: {order_status.get('error')}",
            reply_markup=build_main_keyboard(user_state),
        )
        return

    phone = order_status.get("phone") or "N/A"
    status = order_status.get("status") or "unknown"
    service = order_status.get("service") or "N/A"
    country = order_status.get("country") or "N/A"

    text = (
        f"📊 <b>Order Status</b>\n\n"
        f"Order ID: <code>{order_id}</code>\n"
        f"Phone: <code>{phone}</code>\n"
        f"Service: {service}\n"
        f"Country: {country}\n"
        f"Status: <b>{status.upper()}</b>"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=build_main_keyboard(user_state),
    )

# ==========================================
# CALLBACKS
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def callback_main_menu(call):
    user_id = call.from_user.id
    user_state = get_user_state(user_id)
    bot.edit_message_text(
        "📋 <b>Main Menu</b>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=build_main_keyboard(user_state),
    )

@bot.callback_query_handler(func=lambda call: call.data == "get_number")
def callback_get_number(call):
    user_id = call.from_user.id
    user_state = get_user_state(user_id)
    service = user_state.get("service", "facebook")
    country = user_state.get("country", "US")

    bot.edit_message_text(
        f"🔄 <b>Requesting Number...</b>\n\n"
        f"Service: {format_service_name(service)}\n"
        f"Country: {format_country_name(country)}\n\n"
        f"<i>Please wait...</i>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
    )

    result = hadisms.request_number(service, country)

    if result.get("status") == "error":
        bot.send_message(
            call.message.chat.id,
            f"❌ <b>Error Requesting Number</b>\n\n"
            f"Error: {result.get('error')}",
            parse_mode="HTML",
            reply_markup=build_main_keyboard(user_state),
        )
        return

    order_id = (
        result.get("id")
        or result.get("order_id")
        or result.get("orderId")
        or (result.get("data") or {}).get("id")
    )
    phone = (
        result.get("phone")
        or result.get("number")
        or (result.get("data") or {}).get("phone")
        or (result.get("data") or {}).get("number")
    )
    price = result.get("price") or (result.get("data") or {}).get("price") or "N/A"

    if not order_id or not phone:
        bot.send_message(
            call.message.chat.id,
            f"❌ <b>Invalid Response</b>\n\n"
            f"Could not parse order details.\n\n"
            f"Response: {result}",
            parse_mode="HTML",
            reply_markup=build_main_keyboard(user_state),
        )
        return

    user_state["last_order_id"] = str(order_id)
    user_state["current_number"] = phone

    bot.send_message(
        call.message.chat.id,
        (
            f"✅ <b>Number Received!</b>\n\n"
            f"📱 Phone: <code>{phone}</code>\n"
            f"📋 Service: {format_service_name(service)}\n"
            f"🌍 Country: {format_country_name(country)}\n"
            f"💵 Price: {price}\n"
            f"🆔 Order ID: <code>{order_id}</code>\n\n"
            f"<i>Waiting for SMS verification code...</i>"
        ),
        parse_mode="HTML",
        reply_markup=build_main_keyboard(user_state),
    )

    logger.info(f"Starting background OTP polling for order {order_id}")
    poll_thread = Thread(
        target=poll_hadi_sms_for_otp,
        args=(str(order_id), call.message.chat.id, user_state),
        daemon=True,
    )
    poll_thread.start()

@bot.callback_query_handler(func=lambda call: call.data == "new_number")
def callback_new_number(call):
    user_id = call.from_user.id
    user_state = get_user_state(user_id)
    old_order_id = user_state.get("last_order_id")
    if old_order_id:
        try:
            hadisms.cancel_order(str(old_order_id))
            logger.info(f"Cancelled previous order {old_order_id}")
        except Exception as e:
            logger.warning(f"Could not cancel order {old_order_id}: {e}")

    callback_get_number(call)

@bot.callback_query_handler(func=lambda call: call.data == "change_service")
def callback_change_service(call):
    bot.edit_message_text(
        "📱 <b>Select a Service</b>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=build_service_keyboard(),
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_service:"))
def callback_set_service(call):
    user_id = call.from_user.id
    user_state = get_user_state(user_id)
    service = call.data.split(":", 1)[1]
    user_state["service"] = service

    bot.edit_message_text(
        f"✅ <b>Service Updated</b>\n\nNow set to: <code>{format_service_name(service)}</code>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=build_main_keyboard(user_state),
    )

@bot.callback_query_handler(func=lambda call: call.data == "change_country")
def callback_change_country(call):
    bot.edit_message_text(
        "🌍 <b>Select a Country</b>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=build_country_keyboard(),
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_country:"))
def callback_set_country(call):
    user_id = call.from_user.id
    user_state = get_user_state(user_id)
    country = call.data.split(":", 1)[1]
    user_state["country"] = country

    bot.edit_message_text(
        f"✅ <b>Country Updated</b>\n\nNow set to: <code>{format_country_name(country)}</code>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=build_main_keyboard(user_state),
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_balance")
def callback_check_balance(call):
    user_id = call.from_user.id
    user_state = get_user_state(user_id)
    bot.edit_message_text(
        "💰 <b>Fetching Balance...</b>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
    )
    result = hadisms.get_balance()
    if result.get("status") == "error":
        bot.send_message(
            call.message.chat.id,
            f"❌ Error: {result.get('error')}",
            reply_markup=build_main_keyboard(user_state),
        )
        return

    balance = result.get("balance") or result.get("amount") or "Unknown"
    currency = result.get("currency") or "USD"
    text = f"💰 <b>Account Balance</b>\n\nBalance: <code>{balance}</code> {currency}"

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=build_main_keyboard(user_state),
    )

# ==========================================
# FALLBACK TEXT HANDLER
# ==========================================
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    user_state = get_user_state(user_id)
    bot.send_message(
        message.chat.id,
        "I didn't understand that. Please use the buttons below:",
        reply_markup=build_main_keyboard(user_state),
    )

# ==========================================
# START BOT - POLLING LOOP (KEEPS RUNNING)
# ==========================================
def main():
    print("\n" + "=" * 60)
    print("✅ BOT CONFIGURATION:")
    print(f"   Bot Token: {BOT_TOKEN[:20]}...")
    print(f"   Hadi SMS Base URL: {HADI_SMS_BASE_URL}")
    print(f"   API Prefix: {HADI_SMS_API_PREFIX}")
    print("=" * 60)
    print("📡 Starting polling loop...")
    print("📡 Waiting for messages...")
    print("📡 Press Ctrl+C to stop the bot")
    print("=" * 60)
    
    logger.info("Bot polling loop started")
    
    # Keep trying to poll even if there are temporary connection issues
    while True:
        try:
            print("\n🟢 Bot is now listening for messages...")
            logger.info("Starting infinity_polling...")
            
            # This is the main loop that keeps the bot running
            bot.infinity_polling(
                none_stop=True,
                interval=0,
                timeout=30
            )
            
        except KeyboardInterrupt:
            print("\n" + "=" * 60)
            print("✋ Bot stopped by user (Ctrl+C pressed)")
            print("=" * 60)
            logger.info("Bot stopped by user")
            break
            
        except Exception as e:
            print(f"\n❌ Connection error: {e}")
            print("🔄 Reconnecting in 5 seconds...")
            logger.exception(f"Polling error: {e}")
            time.sleep(5)
            print("🟢 Attempting to reconnect...")

# ==========================================
# MAIN ENTRY POINT - STARTS IMMEDIATELY
# ==========================================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.exception(f"Fatal error in main: {e}")

# Call main() immediately to ensure it runs even on mobile environments
print("\n📡 Initiating bot startup...")
try:
    main()
except KeyboardInterrupt:
    print("\n✋ Bot stopped.")
except Exception as e:
    print(f"\n❌ Startup failed: {e}")
    logger.exception(f"Startup exception: {e}")
