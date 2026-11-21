#!/usr/bin/env python3
"""
Десктопний додаток чат-бота на Python на базі Groq API (Завдання 2).
Повністю автономний файл на базі Tkinter та requests.
"""

from datetime import datetime
import json
import os
import queue
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1"

FALLBACK_CHAT_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "allam-2-7b",
]

EXIT_COMMANDS = {"bye", "bye!", "bye.", "goodbye", "вихід", "бувай", "до побачення"}

THEME = {
    "bg_dark": "#181825",
    "bg_panel": "#1e1e2e",
    "bg_surface": "#313244",
    "bg_input": "#181825",
    "border": "#45475a",
    "text_primary": "#cdd6f4",
    "text_secondary": "#a6adc8",
    "accent_blue": "#89b4fa",
    "accent_green": "#a6e3a1",
    "accent_yellow": "#f9e2af",
    "accent_red": "#f38ba8",
    "btn_primary": "#f97316",
    "btn_primary_hover": "#ea580c",
    "btn_danger": "#ef4444",
    "btn_secondary": "#4b5563",
}


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


class GroqDesktopChatApp(tk.Tk):
    def __init__(self):
        super().__init__()
        load_env()
        self.title("⚡ Groq API Desktop Chat")
        self.geometry("880x680")
        self.minsize(650, 480)
        self.configure(bg=THEME["bg_dark"])

        self.api_key = os.environ.get("GROQ_API_KEY", "").strip()
        self.history = [{"role": "system", "content": "You are a helpful and polite AI assistant."}]
        self.is_generating = False
        self.stop_requested = False
        self.current_model = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Ініціалізація...")
        self.queue = queue.Queue()

        self._init_styles()
        self._build_ui()
        self._check_queue()

        if not self.api_key:
            self.after(200, self._prompt_api_key)
        else:
            self.after(100, self.refresh_models)

    def _init_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background=THEME["bg_dark"], foreground=THEME["text_primary"])
        style.configure(
            "TCombobox",
            fieldbackground=THEME["bg_surface"],
            background=THEME["bg_surface"],
            foreground=THEME["text_primary"],
            arrowcolor=THEME["text_primary"],
        )

    def _prompt_api_key(self):
        """Запитує API ключ у користувача, якщо його немає в env."""
        key = simpledialog.askstring("Groq API Key", "Введіть ваш Groq API Key (gsk_...):", parent=self)
        if key and key.strip():
            self.api_key = key.strip()
            self.refresh_models()
        else:
            self.conn_dot.config(fg=THEME["accent_red"])
            self.conn_lbl.config(text="API ключ відсутній", fg=THEME["accent_red"])
            self.status_var.set("❌ Вкажіть API ключ для роботи з Groq.")

    def _build_ui(self):
        # Верхня панель (Header)
        top_bar = tk.Frame(self, bg=THEME["bg_panel"], padx=12, pady=8)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        tk.Label(
            top_bar,
            text="⚡ Groq Chat",
            font=("Noto Sans", 13, "bold"),
            bg=THEME["bg_panel"],
            fg="#f97316",
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.conn_dot = tk.Label(top_bar, text="●", font=("Noto Sans", 12), bg=THEME["bg_panel"], fg=THEME["text_secondary"])
        self.conn_dot.pack(side=tk.LEFT)

        self.conn_lbl = tk.Label(top_bar, text="Перевірка...", font=("Noto Sans", 9), bg=THEME["bg_panel"], fg=THEME["text_secondary"])
        self.conn_lbl.pack(side=tk.LEFT, padx=(4, 15))

        tk.Label(top_bar, text="Модель:", font=("Noto Sans", 9), bg=THEME["bg_panel"], fg=THEME["text_secondary"]).pack(side=tk.LEFT, padx=(0, 4))
        self.combo = ttk.Combobox(top_bar, textvariable=self.current_model, state="readonly", width=22, font=("Noto Sans", 9))
        self.combo.pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            top_bar,
            text="🔄",
            command=self.refresh_models,
            bg=THEME["bg_surface"],
            fg=THEME["text_primary"],
            relief=tk.FLAT,
            padx=6,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            top_bar,
            text="🔑 Ключ",
            command=self._prompt_api_key,
            bg=THEME["bg_surface"],
            fg=THEME["text_primary"],
            relief=tk.FLAT,
            padx=6,
            font=("Noto Sans", 8),
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            top_bar,
            text="🗑️ Очистити",
            command=self.clear_chat,
            bg=THEME["btn_secondary"],
            fg=THEME["text_primary"],
            relief=tk.FLAT,
            padx=8,
            pady=2,
            font=("Noto Sans", 9),
            cursor="hand2",
        ).pack(side=tk.RIGHT)

        # Текстове поле історії чату
        chat_frame = tk.Frame(self, bg=THEME["bg_dark"], padx=10, pady=5)
        chat_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.chat_area = tk.Text(
            chat_frame,
            wrap=tk.WORD,
            bg=THEME["bg_panel"],
            fg=THEME["text_primary"],
            font=("Noto Sans", 10),
            padx=12,
            pady=10,
            relief=tk.FLAT,
            state=tk.DISABLED,
        )
        scrollbar = ttk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=self.chat_area.yview)
        self.chat_area.configure(yscrollcommand=scrollbar.set)
        self.chat_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.chat_area.tag_configure("time", foreground=THEME["text_secondary"], font=("Noto Sans", 8))
        self.chat_area.tag_configure("user_hdr", foreground=THEME["accent_blue"], font=("Noto Sans", 10, "bold"))
        self.chat_area.tag_configure("user_msg", foreground=THEME["text_primary"], font=("Noto Sans", 10), lmargin1=10, lmargin2=10)
        self.chat_area.tag_configure("bot_hdr", foreground="#f97316", font=("Noto Sans", 10, "bold"))
        self.chat_area.tag_configure("bot_msg", foreground=THEME["text_primary"], font=("Noto Sans", 10), lmargin1=10, lmargin2=10)
        self.chat_area.tag_configure("sys", foreground=THEME["accent_yellow"], font=("Noto Sans", 9, "italic"))

        # Нижня панель вводу
        bottom_frame = tk.Frame(self, bg=THEME["bg_panel"], padx=10, pady=8)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.input_entry = tk.Text(
            bottom_frame,
            height=3,
            wrap=tk.WORD,
            bg=THEME["bg_input"],
            fg=THEME["text_primary"],
            font=("Noto Sans", 10),
            padx=8,
            pady=6,
            relief=tk.FLAT,
            insertbackground=THEME["text_primary"],
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        self.input_entry.bind("<Return>", self._on_enter)
        self.input_entry.focus_set()

        btns = tk.Frame(bottom_frame, bg=THEME["bg_panel"])
        btns.pack(side=tk.RIGHT, fill=tk.Y)

        self.send_btn = tk.Button(
            btns,
            text="📤 Надіслати",
            command=self.send_message,
            bg=THEME["btn_primary"],
            fg="#ffffff",
            activebackground=THEME["btn_primary_hover"],
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=6,
            font=("Noto Sans", 9, "bold"),
            cursor="hand2",
        )
        self.send_btn.pack(side=tk.TOP, fill=tk.X, pady=(0, 4))

        self.stop_btn = tk.Button(
            btns,
            text="⏹️ Зупинити",
            command=self.stop_stream,
            bg=THEME["btn_danger"],
            fg="#ffffff",
            relief=tk.FLAT,
            padx=8,
            font=("Noto Sans", 8),
            cursor="hand2",
            state=tk.DISABLED,
        )
        self.stop_btn.pack(side=tk.BOTTOM, fill=tk.X)

        # Статус-бар
        status_bar = tk.Frame(self, bg=THEME["bg_dark"], padx=10, pady=3)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(status_bar, textvariable=self.status_var, font=("Noto Sans", 8), bg=THEME["bg_dark"], fg=THEME["text_secondary"]).pack(side=tk.LEFT)
        tk.Label(
            status_bar,
            text="Введіть «Bye» для виходу | Enter — надіслати, Shift+Enter — новий рядок",
            font=("Noto Sans", 8),
            bg=THEME["bg_dark"],
            fg=THEME["text_secondary"],
        ).pack(side=tk.RIGHT)

        self._print_sys("⚡ Підключено до Groq API. Введіть ваше запитання або «Bye» для завершення.")

    def refresh_models(self):
        if not self.api_key:
            return

        def _task():
            headers = {"Authorization": f"Bearer {self.api_key}"}
            try:
                res = requests.get(f"{GROQ_API_URL}/models", headers=headers, timeout=5)
                if res.status_code == 200:
                    models_data = res.json().get("data", [])
                    chat_models = [
                        m["id"] for m in models_data
                        if "whisper" not in m.get("id", "").lower()
                        and "prompt-guard" not in m.get("id", "").lower()
                        and "orpheus" not in m.get("id", "").lower()
                    ]
                    if "qwen/qwen3.8-27b" in chat_models:
                        chat_models.remove("qwen/qwen3.8-27b")
                        chat_models.insert(0, "qwen/qwen3.8-27b")
                    self.queue.put(("models", (True, chat_models)))
                    return
            except Exception:
                pass
            self.queue.put(("models", (False, FALLBACK_CHAT_MODELS)))

        threading.Thread(target=_task, daemon=True).start()

    def _on_enter(self, event):
        if not (event.state & 0x1):
            self.send_message()
            return "break"
        return None

    def send_message(self):
        if self.is_generating:
            return
        text = self.input_entry.get("1.0", tk.END).strip()
        if not text:
            return
        self.input_entry.delete("1.0", tk.END)

        clean = text.lower().strip(" \t\n\r.!,")
        if clean in EXIT_COMMANDS:
            self._handle_bye(text)
            return

        model = self.current_model.get()
        if not model:
            messagebox.showwarning("Увага", "Будь ласка, оберіть модель Groq!")
            return

        now = datetime.now().strftime("%H:%M:%S")
        self._append_text(f"\n[{now}] ", "time")
        self._append_text("Ви:\n", "user_hdr")
        self._append_text(f"{text}\n", "user_msg")

        self.history.append({"role": "user", "content": text})
        self.is_generating = True
        self.stop_requested = False
        self.send_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set(f"⚡ {model} генерує...")

        threading.Thread(target=self._stream_task, args=(model, list(self.history)), daemon=True).start()

    def _handle_bye(self, raw_input):
        now = datetime.now().strftime("%H:%M:%S")
        self._append_text(f"\n[{now}] ", "time")
        self._append_text("Ви:\n", "user_hdr")
        self._append_text(f"{raw_input}\n", "user_msg")

        self.input_entry.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)

        self._append_text(f"\n[{now}] ", "time")
        self._append_text("Бот:\n", "bot_hdr")
        self._append_text("До побачення! Було приємно поспілкуватися. Чат завершено. Вікно закриється...\n", "bot_msg")
        self._print_sys("🛑 Чат завершено за командою «Bye».")
        self.status_var.set("Завершення роботи...")
        self.after(2000, self.destroy)

    def _stream_task(self, model, history_copy):
        now = datetime.now().strftime("%H:%M:%S")
        self.queue.put(("start_bot", (model, now)))
        full_chunks = []
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": model, "messages": history_copy, "stream": True}
        try:
            with requests.post(f"{GROQ_API_URL}/chat/completions", headers=headers, json=payload, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if self.stop_requested:
                        break
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
                                full_chunks.append(content)
                                self.queue.put(("chunk", content))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            self.queue.put(("error", str(e)))

        self.queue.put(("done_bot", "".join(full_chunks)))

    def stop_stream(self):
        if self.is_generating:
            self.stop_requested = True

    def clear_chat(self):
        if self.is_generating:
            return
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete("1.0", tk.END)
        self.chat_area.config(state=tk.DISABLED)
        self.history = [{"role": "system", "content": "You are a helpful and polite AI assistant."}]
        self._print_sys("🗑️ Історію чату очищено.")

    def _append_text(self, text, tag):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, text, tag)
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    def _print_sys(self, text):
        self._append_text(f"\nℹ️ {text}\n", "sys")

    def _check_queue(self):
        try:
            while True:
                action, data = self.queue.get_nowait()
                if action == "models":
                    ok, models = data
                    if models:
                        self.conn_dot.config(fg="#a6e3a1")
                        self.conn_lbl.config(text="Groq онлайн", fg="#a6e3a1")
                        self.combo["values"] = models
                        if not self.current_model.get() or self.current_model.get() not in models:
                            self.current_model.set(models[0])
                        self.status_var.set(f"Готово. Обрано: {self.current_model.get()}")
                    else:
                        self.conn_dot.config(fg="#ef4444")
                        self.conn_lbl.config(text="Помилка API", fg="#ef4444")
                        self.status_var.set("❌ Не вдалося отримати моделі Groq")
                elif action == "start_bot":
                    m_name, t_str = data
                    self._append_text(f"\n[{t_str}] ", "time")
                    self._append_text(f"{m_name}:\n", "bot_hdr")
                elif action == "chunk":
                    self._append_text(data, "bot_msg")
                elif action == "error":
                    self._append_text(f"\n[Помилка: {data}]\n", "sys")
                elif action == "done_bot":
                    self._append_text("\n", "bot_msg")
                    if data.strip():
                        self.history.append({"role": "assistant", "content": data.strip()})
                    self.is_generating = False
                    self.send_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                    self.status_var.set("Готово")
        except queue.Empty:
            pass
        self.after(50, self._check_queue)


if __name__ == "__main__":
    app = GroqDesktopChatApp()
    app.mainloop()
