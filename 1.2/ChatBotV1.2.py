import base64
import requests
import json
from difflib import get_close_matches
from dotenv import load_dotenv
import os
import tkinter as tk
from tkinter import messagebox, ttk
import pyttsx3

load_dotenv(".env")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")
FILE_PATH = os.getenv("FILE_PATH")


def read_aloud():
    selected_item = chat_box.get(chat_box.curselection())

    engine = pyttsx3.init()

    voice = engine.getProperty('voices')
    engine.setProperty('voice', voice[1].id)

    engine.setProperty('rate', 100)

    engine.say(selected_item[5:])

    engine.runAndWait()


def insert_text_with_newline(widget, text, max_chars_per_line=50):
    lines = [text[i:i + max_chars_per_line] for i in range(0, len(text), max_chars_per_line)]
    for line in lines:
        widget.insert(tk.END, line)


def load_knowledge_base_from_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    data = response.json()
    content = data["content"]
    sha = data["sha"]

    decoded_content = base64.b64decode(content).decode("utf-8")
    knowledge_base = json.loads(decoded_content)
    return knowledge_base, sha


def save_knowledge_base_to_github(data, sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

    modified_content = json.dumps(data, indent=2)

    payload = {
        "message": "Update knowledge base",
        "content": base64.b64encode(modified_content.encode("utf-8")).decode("utf-8"),
        "sha": sha
    }

    response = requests.put(url, headers=headers, json=payload)

    if response.status_code == 200:
        chat_box.insert(tk.END, "Bot: Thank you! I learned a new response!")
    else:
        messagebox.showerror("Error", "Somethings went wrong!")


def find_best_match(user_question, questions):
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.6)
    return matches[0] if matches else None


def get_answer_for_question(question, knowledge_base):
    for q in knowledge_base["questions"]:
        if q["question"] == question:
            return q["answer"]


def send_message(event=None):
    if message_var.get() != "":
        message = message_var.get()
        insert_text_with_newline(chat_box, f"You: {message}", 50)
    else:
        messagebox.showerror("Error", "Message can't be empty!")
    message_entry.delete(0, tk.END)
    response(message)


def new_response(m):
    knowledge_base, sha = load_knowledge_base_from_github()
    new_response_window = tk.Toplevel()
    new_response_window.geometry("250x120")
    new_response_window.title("I'm learning ...")
    ttk.Label(new_response_window, text="Type the answer or 'skip' to skip:").pack()
    new_answer = tk.StringVar()
    en = ttk.Entry(new_response_window, textvariable=new_answer)
    en.pack()

    def submit_response():
        answer = new_answer.get()
        if answer.lower() != "skip":
            knowledge_base["questions"].append({"question": m, "answer": answer})
            save_knowledge_base_to_github(knowledge_base, sha)
        new_response_window.destroy()

    ttk.Button(new_response_window, text="Submit", command=submit_response).pack()

    new_response_window.mainloop()


def response(msg):
    knowledge_base, sha = load_knowledge_base_from_github()
    best_match = find_best_match(msg, [q["question"] for q in knowledge_base["questions"]])
    if best_match:
        answer = get_answer_for_question(best_match, knowledge_base)
        insert_text_with_newline(chat_box, f"Bot: {answer}", 50)
    else:
        chat_box.insert(tk.END, "Bot: I don't know the answer. Can you teach me?")
        new_response(msg)


root = tk.Tk()
root.title("Chat Bot")

frame = tk.Frame(root)
scrollbar = ttk.Scrollbar(frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

chat_box = tk.Listbox(frame, height=15, width=50, yscrollcommand=scrollbar.set)
chat_box.pack(side=tk.LEFT, fill=tk.BOTH)

scrollbar.config(command=chat_box.yview)

frame.pack()

message_var = tk.StringVar()
message_entry = ttk.Entry(root, textvariable=message_var)
message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
message_entry.bind("<Return>", send_message)

send_button = ttk.Button(root, text="Send", command=send_message)
send_button.pack(side=tk.RIGHT)

context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="Read aloud", command=read_aloud)


def show_context_menu(event):
    context_menu.post(event.x_root, event.y_root)


chat_box.bind("<Button-3>", show_context_menu)

root.mainloop()
