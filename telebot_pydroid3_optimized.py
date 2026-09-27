"""
Telegram OTP Bot for Pydroid 3 - Fully Optimized Version

This version is specifically designed to work reliably on Pydroid 3 (Android).
It includes:
- Proper error handling and logging
- Sys.exit prevention
- Background thread safety
- Reduced resource usage
- Explicit polling loop with error recovery
- Compatible with Pydroid 3 environment

Install in Pydroid 3:
pip install pyTelegramBotAPI httpx

Run: python telebot_pydroid.py
"""

import logging
import os
import re
import sys
import time
import traceback
from threading import Thread
from typing import Any, Dict, Optional

try:
    import httpx
    import telebot
    from telebot import types
except ImportError as e:
    print(f"ERROR: Missing required package: {e}")
    print("Please install: pip install pyTelegramBotAPI httpx")
    sys.exit(1)

# ==========================================
# CONFIG
# ==========================================
# IMPORTANT: Set these before running!
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
HADI_SMS_API_KEY = os.getenv("HADI_SMS_API_KEY", "YOUR_HADI_SMS_API_KEY_HERE")
HADI_SMS_BASE_URL = os.getenv("HADI_SMS_BASE_URL", "https://api.hadisms.com")

HADI_SMS_API_PREFIX = "/api/v1"
USE_TOKEN_PREFIX = False

# Poll settings
OTP_TIMEOUT_SECONDS = 180
POLL_INTERVAL_SECONDS = 5

# Pydroid 3 specific settings
MAX_RECONNECT_ATTEMPTS = 10
RECONNECT_DELAY_SECONDS = 5

# ==========================================
# LOGGING - PYDROID 3 OPTIMIZED
# ==========================================
def setup_logging():
    """Setup logging that works reliably in Pydroid 3"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.expanduser("~/Pydroid3/logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "telegram_bot.log")
    
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Bot started on Pydroid 3")
    logger.info(f"Bot Token: {BOT_TOKEN[:10]}...")
    logger.info(f"Hadi SMS API Key: {HADI_SMS_API_KEY[:10]}...")
    logger.info(f"Logs saved to: {log_file}")
    logger.info("=" * 60)
    
    return logger

logger = setup_logging()

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
    "BR": "Brazil",
    "IN": "India",
    "CN": "China",
    "JP": "Japan",
}

USER_STATE = {}

# ==========================================
# BOT INITIALIZATION - PYDROID 3 SAFE
# ==========================================
try:
    bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
    logger.info("✅ Bot initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize bot: {e}")
    logger.error(traceback.format_exc())
    print("ERROR: Could not initialize bot. Check your BOT_TOKEN")
    sys.exit(1)

# ==========================================
# HADI SMS CLIENT - ERROR RESILIENT
# ==========================================
class HadiSmsClient:
    """Hadi SMS API client optimized for Pydroid 3"""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(30.0)
        logger.info(f"HadiSmsClient initialized with URL: {self.base_url}")

    def _auth_header(self) -> Dict[str, str]:
        if USE_TOKEN_PREFIX:
            auth = f"Token {self.api_key}"
        else:
            auth = f"Bearer {self.api_key}"
        
        return {
            "Authorization": auth,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self.base_url}{HADI_SMS_API_PREFIX}{path}"

    def get_balance(self) -> Dict[str, Any]:
        try:
            logger.debug("Fetching balance from Hadi SMS")
            response = httpx.get(
                self._url("/balance"),
                headers=self._auth_header(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Balance response: {result}")
            return result
        except httpx.RequestError as e:
            logger.error(f"Network error fetching balance: {e}")
            return {"status": "error", "error": f"Network error: {str(e)}"}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching balance: {e.status_code} - {e.response.text}")
            return {"status": "error", "error": f"HTTP {e.status_code}: {e.response.text}"}
        except Exception as e:
            logger.exception(f"Unexpected error fetching balance: {e}")
            return {"status": "error", "error": str(e)}

    def request_number(self, service: str, country: str) -> Dict[str, Any]:
        payload = {
            "service": service.lower(),
            "country": country.upper(),
        }
        try:
            logger.info(f"Requesting number: service={service}, country={country}")
            response = httpx.post(
                self._url("/order"),
                headers=self._auth_header(),
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Order response: {result}")
            return result
        except httpx.RequestError as e:
            logger.error(f"Network error requesting number: {e}")
            return {"status": "error", "error": f"Network error: {str(e)}"}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error requesting number: {e.status_code} - {e.response.text}")
            return {"status": "error", "error": f"HTTP {e.status_code}: {e.response.text}"}
        except Exception as e:
            logger.exception(f"Unexpected error requesting number: {e}")
            return {"status": "error", "error": str(e)}

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        try:
            logger.debug(f"Getting order status for {order_id}")
            response = httpx.get(
                self._url(f"/order/{order_id}/status"),
                headers=self._auth_header(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return {"status": "error", "error": str(e)}

    def get_sms(self, order_id: str) -> Dict[str, Any]:
        try:
            logger.debug(f"Fetching SMS for order {order_id}")
            response = httpx.get(
                self._url(f"/order/{order_id}/sms"),
                headers=self._auth_header(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching SMS: {e}")
            return {"status": "error", "error": str(e)}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        try:
            logger.info(f"Cancelling order {order_id}")
            response = httpx.post(
                self._url(f"/order/{order_id}/cancel"),
                headers=self._auth_header(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
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
    return SERVICE_OPTIONS.get(service_key, service_key.title())

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

def build_main_keyboard(user_state: Dict[str, Any]) -> types.InlineKeyboardMarkup:
    service = format_service_name(user_state.get("service", "facebook"))
    country = format_country_name(user_state.get("country", "US"))

    markup = types.InlineKeyboardMarkup()
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
        row.append(types.InlineKeyboardButton(f"{countries[i][1]}", callback_data=f"set_country:{countries[i][0]}"))
        if i + 1 < len(countries):
            row.append(types.InlineKeyboardButton(f"{countries[i + 1][1]}", callback_data=f"set_country:{countries[i + 1][0]}"))
        markup.row(*row)
    markup.add(types.InlineKeyboardButton("← Back", callback_data="main_menu"))
    return markup

# ==========================================
# OTP POLLING - THREAD SAFE FOR PYDROID
# ==========================================
def poll_hadi_sms_for_otp(order_id: str, chat_id: int, user_state: Dict[str, Any]) -> None:
    """Poll Hadi SMS for OTP - optimized for Pydroid 3"""
    logger.info(f"[OTP POLL] Starting for order_id={order_id}, chat_id={chat_id}")
    started_at = time.time()

    try:
        while time.time() - started_at < OTP_TIMEOUT_SECONDS:
            try:
                response = hadisms.get_sms(order_id)

                if response.get("status") == "error":
                    logger.warning(f"[OTP POLL] API error: {response.get('error')}")
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
                            logger.info(f"[OTP POLL] OTP found: {otp}")
                            try:
                                bot.send_message(
                                    chat_id,
                                    f"✅ <b>OTP Received!</b>\n\nCode: <code>{otp}</code>\n\nMessage: {text}",
                                    parse_mode="HTML",
                                )
                            except Exception as e:
                                logger.error(f"[OTP POLL] Error sending OTP message: {e}")
                            return

                time.sleep(POLL_INTERVAL_SECONDS)

            except Exception as e:
                logger.error(f"[OTP POLL] Error in polling loop: {e}")
                time.sleep(POLL_INTERVAL_SECONDS)

        # Timeout
        logger.warning(f"[OTP POLL] Timeout after {OTP_TIMEOUT_SECONDS}s")
        try:
            bot.send_message(
                chat_id,
                "⏰ <b>Timeout</b>\n\nNo SMS received within 3 minutes.\nYou can request a new number.",
                parse_mode="HTML",
                reply_markup=build_main_keyboard(user_state),
            )
        except Exception as e:
            logger.error(f"[OTP POLL] Error sending timeout message: {e}")

    except Exception as e:
        logger.exception(f"[OTP POLL] Unexpected error: {e}")

# ==========================================
# MESSAGE HANDLERS
# ==========================================
@bot.message_handler(commands=["start"])
def handle_start(message):
    try:
        user_id = message.from_user.id
        user_state = get_user_state(user_id)
        logger.info(f"[START] User {user_id} started bot")
        
        bot.send_message(
            message.chat.id,
            "👋 <b>Welcome to OTP Activation Bot</b>\n\n"
            "Powered by Hadi SMS API\n\n"
            "Choose an action below:",
            parse_mode="HTML",
            reply_markup=build_main_keyboard(user_state),
        )
    except Exception as e:
        logger.exception(f"[START] Error: {e}")

@bot.message_handler(commands=["help"])
def handle_help(message):
    try:
        user_id = message.from_user.id
        user_state = get_user_state(user_id)
        logger.info(f"[HELP] User {user_id} requested help")
        
        bot.send_message(
            message.chat.id,
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
            "✅ Real-time OTP delivery",
            parse_mode="HTML",
            reply_markup=build_main_keyboard(user_state),
        )
    except Exception as e:
        logger.exception(f"[HELP] Error: {e}")

@bot.message_handler(commands=["balance"])
def handle_balance(message):
    try:
        user_id = message.from_user.id
        user_state = get_user_state(user_id)
        logger.info(f"[BALANCE] User {user_id} checking balance")

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

        text = f"💰 <b>Hadi SMS Account Balance</b>\n\nBalance: <code>{balance}</code> {currency}"
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=build_main_keyboard(user_state),
        )
    except Exception as e:
        logger.exception(f"[BALANCE] Error: {e}")

@bot.message_handler(commands=["status"])
def handle_status(message):
    try:
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

        logger.info(f"[STATUS] User {user_id} checking order {order_id}")

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
    except Exception as e:
        logger.exception(f"[STATUS] Error: {e}")

# ==========================================
# CALLBACK HANDLERS
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def callback_main_menu(call):
    try:
        user_id = call.from_user.id
        user_state = get_user_state(user_id)
        logger.debug(f"[CALLBACK] Main menu for user {user_id}")
        
        bot.edit_message_text(
            "📋 <b>Main Menu</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=build_main_keyboard(user_state),
        )
    except Exception as e:
        logger.exception(f"[CALLBACK] Error in main_menu: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "get_number")
def callback_get_number(call):
    try:
        user_id = call.from_user.id
        user_state = get_user_state(user_id)
        service = user_state.get("service", "facebook")
        country = user_state.get("country", "US")

        logger.info(f"[CALLBACK] User {user_id} requesting number: {service} / {country}")

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
                f"❌ <b>Error Requesting Number</b>\n\nError: {result.get('error')}",
                parse_mode="HTML",
                reply_markup=build_main_keyboard(user_state),
            )
            return

        order_id = result.get("id") or result.get("order_id") or result.get("orderId") or result.get("data", {}).get("id")
        phone = result.get("phone") or result.get("number") or result.get("data", {}).get("phone") or result.get("data", {}).get("number")
        price = result.get("price") or result.get("data", {}).get("price") or "N/A"

        if not order_id or not phone:
            logger.error(f"[CALLBACK] Invalid response: {result}")
            bot.send_message(
                call.message.chat.id,
                f"❌ <b>Invalid Response</b>\n\nCould not parse order details.",
                parse_mode="HTML",
                reply_markup=build_main_keyboard(user_state),
            )
            return

        user_state["last_order_id"] = str(order_id)
        user_state["current_number"] = phone

        text = (
            f"✅ <b>Number Received!</b>\n\n"
            f"📱 Phone: <code>{phone}</code>\n"
            f"📋 Service: {format_service_name(service)}\n"
            f"🌍 Country: {format_country_name(country)}\n"
            f"💵 Price: {price}\n"
            f"🆔 Order ID: <code>{order_id}</code>\n\n"
            f"<i>Waiting for SMS verification code...</i>"
        )

        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=build_main_keyboard(user_state),
        )

        # Start polling in background thread
        poll_thread = Thread(
            target=poll_hadi_sms_for_otp,
            args=(str(order_id), call.message.chat.id, user_state),
            daemon=True,
        )
        poll_thread.start()
        logger.info(f"[CALLBACK] Started polling thread for order {order_id}")

    except Exception as e:
        logger.exception(f"[CALLBACK] Error in get_number: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "new_number")
def callback_new_number(call):
    try:
        user_id = call.from_user.id
        user_state = get_user_state(user_id)
        logger.info(f"[CALLBACK] User {user_id} requesting new number")

        old_order_id = user_state.get("last_order_id")
        if old_order_id:
            try:
                hadisms.cancel_order(str(old_order_id))
                logger.info(f"[CALLBACK] Cancelled previous order {old_order_id}")
            except Exception as e:
                logger.warning(f"[CALLBACK] Could not cancel order: {e}")

        callback_get_number(call)
    except Exception as e:
        logger.exception(f"[CALLBACK] Error in new_number: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "change_service")
def callback_change_service(call):
    try:
        logger.debug(f"[CALLBACK] Change service menu")
        bot.edit_message_text(
            "📱 <b>Select a Service</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=build_service_keyboard(),
        )
    except Exception as e:
        logger.exception(f"[CALLBACK] Error in change_service: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_service:"))
def callback_set_service(call):
    try:
        user_id = call.from_user.id
        user_state = get_user_state(user_id)
        service = call.data.split(":", 1)[1]
        user_state["service"] = service
        
        logger.info(f"[CALLBACK] User {user_id} set service to {service}")

        bot.edit_message_text(
            f"✅ <b>Service Updated</b>\n\nNow set to: <code>{format_service_name(service)}</code>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=build_main_keyboard(user_state),
        )
    except Exception as e:
        logger.exception(f"[CALLBACK] Error in set_service: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "change_country")
def callback_change_country(call):
    try:
        logger.debug(f"[CALLBACK] Change country menu")
        bot.edit_message_text(
            "🌍 <b>Select a Country</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=build_country_keyboard(),
        )
    except Exception as e:
        logger.exception(f"[CALLBACK] Error in change_country: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_country:"))
def callback_set_country(call):
    try:
        user_id = call.from_user.id
        user_state = get_user_state(user_id)
        country = call.data.split(":", 1)[1]
        user_state["country"] = country
        
        logger.info(f"[CALLBACK] User {user_id} set country to {country}")

        bot.edit_message_text(
            f"✅ <b>Country Updated</b>\n\nNow set to: <code>{format_country_name(country)}</code>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=build_main_keyboard(user_state),
        )
    except Exception as e:
        logger.exception(f"[CALLBACK] Error in set_country: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "check_balance")
def callback_check_balance(call):
    try:
        user_id = call.from_user.id
        user_state = get_user_state(user_id)
        logger.info(f"[CALLBACK] User {user_id} checking balance")

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
    except Exception as e:
        logger.exception(f"[CALLBACK] Error in check_balance: {e}")

# ==========================================
# FALLBACK
# ==========================================
@bot.message_handler(func=lambda message: True)
def fallback_handler(message):
    try:
        user_id = message.from_user.id
        user_state = get_user_state(user_id)
        logger.debug(f"[MESSAGE] Unknown message from user {user_id}: {message.text}")
        
        bot.send_message(
            message.chat.id,
            "I didn't understand that. Please use the buttons below:",
            reply_markup=build_main_keyboard(user_state),
        )
    except Exception as e:
        logger.exception(f"[FALLBACK] Error: {e}")

# ==========================================
# BOT POLLING - PYDROID 3 OPTIMIZED
# ==========================================
def start_bot_polling():
    """Start bot polling with error recovery for Pydroid 3"""
    logger.info("=" * 60)
    logger.info("STARTING BOT POLLING")
    logger.info("=" * 60)
    
    reconnect_attempts = 0
    
    while True:
        try:
            logger.info(f"🚀 Bot polling started (attempt {reconnect_attempts + 1})")
            print("✅ Bot is running in polling mode")
            print("📡 Listening for messages...")
            print("Press Ctrl+C to stop\n")
            
            # This will run indefinitely
            bot.infinity_polling(timeout=10, long_polling_timeout=10)
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user (Ctrl+C)")
            print("\n✋ Bot stopped by user")
            break
            
        except Exception as e:
            reconnect_attempts += 1
            logger.error(f"❌ Polling error (attempt {reconnect_attempts}): {e}")
            logger.error(traceback.format_exc())
            
            if reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
                logger.critical(f"Max reconnect attempts ({MAX_RECONNECT_ATTEMPTS}) reached. Stopping bot.")
                print(f"❌ Max reconnect attempts reached. Bot stopped.")
                break
            
            logger.info(f"Reconnecting in {RECONNECT_DELAY_SECONDS}s...")
            print(f"⚠️  Reconnecting in {RECONNECT_DELAY_SECONDS}s... (attempt {reconnect_attempts}/{MAX_RECONNECT_ATTEMPTS})\n")
            time.sleep(RECONNECT_DELAY_SECONDS)

# ==========================================
# MAIN ENTRY POINT
# ==========================================
if __name__ == "__main__":
    try:
        logger.info("Python process started")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Platform: {sys.platform}")
        
        # Validate configuration
        if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            logger.critical("❌ BOT_TOKEN not set!")
            print("ERROR: Please set BOT_TOKEN environment variable")
            print("Or edit the script and replace YOUR_TELEGRAM_BOT_TOKEN_HERE with your actual bot token")
            sys.exit(1)
        
        if HADI_SMS_API_KEY == "YOUR_HADI_SMS_API_KEY_HERE":
            logger.critical("❌ HADI_SMS_API_KEY not set!")
            print("ERROR: Please set HADI_SMS_API_KEY environment variable")
            print("Or edit the script and replace YOUR_HADI_SMS_API_KEY_HERE with your actual API key")
            sys.exit(1)
        
        logger.info("✅ Configuration validated")
        start_bot_polling()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\n✋ Application stopped")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        logger.critical(traceback.format_exc())
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
