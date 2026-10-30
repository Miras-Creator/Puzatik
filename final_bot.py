# -*- coding: utf-8 -*-
import os
import time
import requests
import urllib3
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# НАСТРОЙКА ТОКЕНОВ (Всё проверено лично)
TOKEN = '9082711296:AAHyt1rQxc6KtleEc-dduVHDB86_ILbeebw'
BOT_USERNAME = "puzatik"
API_URL = f"https://telegram.org{TOKEN}"

# Вечный официальный ключ авторизации ИИ Сбера
GIGACHAT_CREDENTIALS = "N2MwOTU0YjYtOWFlYi00YzgxLWIyNzEtZjVhYjI0ZWM1ZDgxOmY5NTE2MTRiLTdmYjEtNGU0YS1iNWRjLTc3NThlMWVhMGJiNA=="
g_token = ""
g_token_expires = 0

user_context = {}

SYSTEM_INSTRUCTION = (
    "Ты — реальный живой парень с Кавказа по имени Пузатик. Общайся естественно, "
    "по-простецки, по-братски, используй живой разговорный русский язык с кавказским акцентом "
    "(обязательно используй слова: уцы, жи есть, брат, ле, хата, чистый, вабабай, эээ, дон). "
    "Отвечай коротко, емко, просто, как обычный человек в мессенджере. Избегай фраз роботов."
)

def get_g_token():
    """Официальное получение ключа доступа к ИИ Сбера"""
    global g_token, g_token_expires
    if time.time() < g_token_expires: return g_token
    try:
        res = requests.post(
            "https://sberbank.ru",
            headers={"Authorization": f"Bearer {GIGACHAT_CREDENTIALS}", "Content-Type": "application/x-www-form-urlencoded"},
            data={"scope": "GIGACHAT_API_PERS"},
            verify=False, timeout=10
        )
        g_token = res.json()["access_token"]
        g_token_expires = time.time() + 25 * 60
        return g_token
    except:
        return None

def ask_ai_sber(chat_id, user_text):
    """Мгновенный пацанский ответ от ИИ Сбера без зависаний"""
    global user_context
    iam_token = get_g_token()
    if not iam_token: 
        return "Эээ, уцы, голова чет раскалывается жи есть, повтори по-братски позже?"
        
    if chat_id not in user_context:
        user_context[chat_id] = []
    user_context[chat_id].append({'role': 'user', 'content': user_text})
    
    # Формируем историю диалога для Сбера
    messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
    for msg in user_context[chat_id][-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    try:
        res = requests.post(
            "https://sberbank.ru",
            headers={"Authorization": f"Bearer {iam_token}", "Content-Type": "application/json"},
            json={"model": "GigaChat", "messages": messages, "temperature": 0.8},
            verify=False, timeout=10
        )
        ai_reply = res.json()["choices"]["message"]["content"].strip()
        user_context[chat_id].append({'role': 'assistant', 'content': ai_reply})
        if len(user_context[chat_id]) > 12:
            user_context[chat_id] = user_context[chat_id][-10:]
        return ai_reply
    except:
        if user_context[chat_id] and user_context[chat_id][-1]['role'] == 'user':
            user_context[chat_id].pop()
        return "Эээ, ле, че-то в натуре сеть заморосила жи есть! Напиши еще раз, уцы!"

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Alive")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

def bot_loop():
    try:
        requests.get(f"{API_URL}/deleteWebhook", timeout=10)
        requests.get(f"{API_URL}/getUpdates", params={'offset': -1, 'timeout': 1}, timeout=10)
        print("[СТАРТ] Бот Пузатик успешно запущен!")
    except:
        pass
    
    offset = 0
    while True:
        try:
            res = requests.get(f"{API_URL}/getUpdates", params={'offset': offset, 'timeout': 20}, timeout=25)
            if res.status_code != 200:
                time.sleep(1)
                continue
            data = res.json()
            for update in data.get('result', []):
                offset = update['update_id'] + 1
                message_data = update.get("message") or update.get("channel_post")
                if not message_data or 'text' not in message_data:
                    continue
                
                chat_id = message_data['chat']['id']
                user_text = message_data["text"]
                chat_type = message_data["chat"]["type"]
                
                should_respond = False
                if chat_type == "private":
                    should_respond = True
                elif chat_type in ["group", "supergroup"]:
                    reply_to = message_data.get("reply_to_message")
                    if reply_to and reply_to.get("from", {}).get("id") == 9082711296:
                        should_respond = True
                    elif BOT_USERNAME.lower() in user_text.lower() or "пузатик" in user_text.lower():
                        should_respond = True
                elif chat_type == "channel":
                    should_respond = True

                if not should_respond:
                    continue
                
                if user_text.startswith('/'):
                    if user_text in ['/start', '/clear', f'/start@{BOT_USERNAME}', f'/clear@{BOT_USERNAME}']:
                        user_context[chat_id] = []
                        try: requests.post(f"{API_URL}/sendMessage", json={'chat_id': chat_id, 'text': 'Здарова, уцы! Я Пузатик, жи есть. Память очистил, давай потрещим, ле!'}, timeout=10)
                        except: pass
                    continue
                
                try: requests.post(f"{API_URL}/sendChatAction", json={'chat_id': chat_id, 'action': 'typing'}, timeout=5)
                except: pass
                
                reply_text = run_reply = ask_ai_sber(chat_id, user_text)
                
                try:
                    requests.post(f"{API_URL}/sendMessage", json={'chat_id': chat_id, 'text': reply_text}, timeout=10)
                except:
                    pass
        except:
            time.sleep(2)

if __name__ == '__main__':
    threading.Thread(target=run_health_server, daemon=True).start()
    bot_loop()
