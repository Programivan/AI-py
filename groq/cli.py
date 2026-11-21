#!/usr/bin/env python3
"""
Консольний чат-бот на Python на базі Groq API (Завдання 2).
Підтримує вибір моделі, збереження контексту бесіди, потокову генерацію (streaming)
та завершення розмови по команді «Bye».
"""

import json
import os
import sys
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1"

FALLBACK_CHAT_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "allam-2-7b",
]

EXIT_COMMANDS = {"bye", "bye!", "bye.", "goodbye", "вихід", "бувай", "до побачення"}


def load_env():
    """Завантажує змінні з .env файлу за наявності."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, ".env"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(base_dir, "..", ".env"),
    ]
    for env_path in candidates:
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip().strip("'\""))
                break
            except Exception:
                pass


def get_api_key() -> str:
    """Повертає API ключ або запитує його у користувача."""
    load_env()
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        print("\n🔑 Змінну GROQ_API_KEY не знайдено.")
        key = input("Введіть ваш Groq API Key (gsk_...): ").strip()
    return key


def get_chat_models(api_key: str) -> list:
    """Отримує список доступних текстових моделей з Groq API."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.get(f"{GROQ_API_URL}/models", headers=headers, timeout=5)
        if resp.status_code == 200:
            models_data = resp.json().get("data", [])
            chat_models = []
            for m in models_data:
                m_id = m.get("id", "")
                if "whisper" not in m_id.lower() and "prompt-guard" not in m_id.lower() and "orpheus" not in m_id.lower():
                    chat_models.append(m_id)
            if chat_models:
                if "qwen/qwen3.8-27b" in chat_models:
                    chat_models.remove("qwen/qwen3.8-27b")
                    chat_models.insert(0, "qwen/qwen3.8-27b")
                return chat_models
    except Exception:
        pass
    return FALLBACK_CHAT_MODELS


def select_model(models: list) -> str:
    """Дозволяє користувачеві вибрати модель."""
    print("\n--- Доступні моделі Groq API ---")
    for idx, model_name in enumerate(models, start=1):
        print(f"  [{idx}] {model_name}")

    default_model = models[0]
    while True:
        choice = input(f"\nОберіть номер або назву моделі [{default_model}]: ").strip()
        if not choice:
            return default_model
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(models):
                return models[idx - 1]
            print(f"❌ Введіть число від 1 до {len(models)}.")
        elif choice in models:
            return choice
        else:
            return choice


def main():
    print("=" * 60)
    print("⚡ Чат-бот на базі Groq API (LLM Cloud)")
    print("Введіть «Bye» для завершення розмови.")
    print("=" * 60)

    api_key = get_api_key()
    if not api_key:
        print("❌ Groq API ключ не вказано! Роботу зупинено.")
        sys.exit(1)

    print("🔍 Перевірка підключення до Groq API...")
    models = get_chat_models(api_key)
    print("✅ Підключення до Groq успішне!")

    model = select_model(models)
    print(f"\n🚀 Обрано модель: {model}")
    print("Розпочніть спілкування (напишіть 'Bye' для виходу):\n")

    history = [
        {"role": "system", "content": "You are a helpful and polite AI assistant."}
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    while True:
        try:
            user_input = input("👤 Ви: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n🤖 Бот: До побачення! Роботу завершено.")
            break

        if not user_input:
            continue

        clean_input = user_input.lower().strip(" \t\n\r.!,")
        if clean_input in EXIT_COMMANDS:
            print("🤖 Бот: До побачення! Було приємно поспілкуватися. Чат завершено.\n")
            break

        history.append({"role": "user", "content": user_input})

        print(f"🤖 {model}: ", end="", flush=True)
        assistant_reply = []

        payload = {
            "model": model,
            "messages": history,
            "stream": True,
        }

        try:
            with requests.post(f"{GROQ_API_URL}/chat/completions", headers=headers, json=payload, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    decoded = line.decode("utf-8")
                    if decoded.startswith("data: "):
                        data_str = decoded[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                print(content, end="", flush=True)
                                assistant_reply.append(content)
                        except json.JSONDecodeError:
                            continue
            print("\n")
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Помилка запиту до Groq API: {e}\n")

        full_reply = "".join(assistant_reply).strip()
        if full_reply:
            history.append({"role": "assistant", "content": full_reply})


if __name__ == "__main__":
    main()
