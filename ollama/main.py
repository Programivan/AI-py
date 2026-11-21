#!/usr/bin/env python3
import json
import sys
import requests

OLLAMA_URL = "http://localhost:11434"
EXIT_COMMANDS = {"bye", "bye!", "bye.", "goodbye", "вихід", "бувай", "до побачення"}


def get_available_models():
    """Отримує список встановлених локальних моделей Ollama."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            return [m["name"] for m in resp.json().get("models", []) if "name" in m]
    except Exception:
        pass
    return []


def select_model():
    """Вибір моделі користувачем."""
    models = get_available_models()
    if not models:
        print("⚠️ Не знайдено завантажених моделей в Ollama.")
        user_choice = input("Введіть назву моделі вручну [llama3.2:3b]: ").strip()
        return user_choice if user_choice else "llama3.2:3b"

    print("\n--- Доступні моделі Ollama ---")
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
            print(f"Введіть число від 1 до {len(models)}.")
        elif choice in models:
            return choice
        else:
            return choice


def main():
    print("=" * 55)
    print("🤖 Локальний LLM Чат-бот (Ollama CLI)")
    print("Введіть «Bye» для завершення розмови.")
    print("=" * 55)

    # Перевірка з'єднання з Ollama
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if resp.status_code != 200:
            print("❌ Ollama повернула статус помилки.")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ Не вдалося підключитися до Ollama.")
        print("Переконайтеся, що Ollama запущена ('ollama serve').")
        sys.exit(1)

    model = select_model()
    print(f"\n🚀 Активна модель: {model}")
    print("Розпочніть спілкування (напишіть 'Bye' для виходу):\n")

    history = [
        {"role": "system", "content": "You are a helpful AI assistant."}
    ]

    while True:
        try:
            user_input = input("👤 Ви: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n🤖 Бот: До побачення!")
            break

        if not user_input:
            continue

        # Перевірка на завершення чату
        clean_input = user_input.lower().strip(" \t\n\r.!,")
        if clean_input in EXIT_COMMANDS:
            print("🤖 Бот: До побачення! Чат завершено.\n")
            break

        history.append({"role": "user", "content": user_input})

        print(f"🤖 {model}: ", end="", flush=True)
        assistant_reply = []

        try:
            payload = {
                "model": model,
                "messages": history,
                "stream": True,
            }
            with requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line:
                        chunk = json.loads(line.decode("utf-8"))
                        content = chunk.get("message", {}).get("content", "")
                        print(content, end="", flush=True)
                        assistant_reply.append(content)
                        if chunk.get("done", False):
                            break
            print("\n")
        except Exception as e:
            print(f"\n❌ Помилка: {e}\n")

        full_reply = "".join(assistant_reply).strip()
        if full_reply:
            history.append({"role": "assistant", "content": full_reply})


if __name__ == "__main__":
    main()
