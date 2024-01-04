import base64
import requests
import json
from difflib import get_close_matches
from dotenv import load_dotenv
import os
import tkinter as tk
from tkinter import messagebox, ttk
import pyttsx3
import socket
from vosk import Model, KaldiRecognizer
import pyaudio
from PIL import Image, ImageTk
import threading

# ==================== LoadData ====================

current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "knowledge_base.json")

current_dir = os.path.dirname(os.path.abspath(__file__))
ico_path = os.path.join(current_dir, "chatbot.ico")

current_dir = os.path.dirname(os.path.abspath(__file__))
img_path = os.path.join(current_dir, "microphone.png")

current_dir = os.path.dirname(os.path.abspath(__file__))
mod_path = os.path.join(current_dir, "vosk-model-small-en-us-0.15")

load_dotenv(env_path)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")
FILE_PATH = os.getenv("FILE_PATH")


# ==================== Knowledgebase ====================

def download_knowledgebase():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    file_name = "knowledge_base.json"
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    try:
        content = response.json()["content"]
        decoded_content = base64.b64decode(content).decode("utf-8")
        with open(file_path, "w") as file:
            file.write(decoded_content)
    except OSError:
        messagebox.showerror("Error", "Failed to download data, Please check your internet.")


def is_internet_connected():
    try:

        socket.create_connection(("www.google.com", 80))
        download_knowledgebase()
    except OSError:
        try:
            with open("knowledge_base.json", "r"):
                pass
        except:
            messagebox.showerror("Error", "Please check your internet connection.")


def load_knowledge_base():
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


def save_knowledge_base(data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)


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
        chat_box.itemconfig(tk.END, {"fg": "green"})
    else:
        messagebox.showerror("Error", "Somethings went wrong!")


# ==================== functions ====================
def find_best_match(user_question, questions):
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.8)
    print(matches)
    return matches[0] if matches else None


def get_answer_for_question(question, knowledge_base):
    for q in knowledge_base["questions"]:
        if q["question"] == question:
            return q["answer"]


def send_message(event=None):
    if message_var.get() != "":
        message = message_var.get()
        chat_box.config(foreground="black")
        insert_text_with_newline(chat_box, f"You: {message}", 50)
        if message.lower() == "bye":
            root.after(2500, lambda: root.destroy())
    else:
        messagebox.showerror("Error", "Message can't be empty!")
    message_entry.delete(0, tk.END)
    response(message)


def new_response(m):
    def submit_response(event=None):
        answer = new_answer.get()
        if answer.lower() != "skip":

            try:
                knowledge_base["questions"].append({"question": m.lower(), "answer": answer})
                save_knowledge_base_to_github(knowledge_base, sha)
                download_knowledgebase()
            except:
                messagebox.showerror("Error", "Please check your internet connection.")

        new_response_window.destroy()

    knowledge_base, sha = load_knowledge_base_from_github()
    new_response_window = tk.Toplevel()
    new_response_window.geometry("250x80")
    new_response_window.title("I'm learning ...")
    ttk.Label(new_response_window, text="Type the answer or 'skip' to skip:").pack()
    new_answer = tk.StringVar()
    en = ttk.Entry(new_response_window, textvariable=new_answer)
    en.pack()
    en.bind("<Return>", submit_response)

    ttk.Button(new_response_window, text="Submit", command=submit_response).pack()

    new_response_window.mainloop()


def response(msg):
    knowledge_base = load_knowledge_base()
    best_match = find_best_match(msg.lower(), [q["question"] for q in knowledge_base["questions"]])
    if best_match:
        answer = get_answer_for_question(best_match, knowledge_base)
        insert_text_with_newline(chat_box, f"Bot: {answer}", 50)
        # Set the color of the bot's response to green
        chat_box.itemconfig(tk.END, {'fg': 'green'})
    else:
        chat_box.insert(tk.END, "Bot: I don't know the answer. Can you teach me?")
        chat_box.itemconfig(tk.END, {"fg": "red"})
        try:
            socket.create_connection(("www.google.com", 80))
            new_response(msg)
        except:
            messagebox.showerror("Sorry", "For teaching me you should have internet connection.")


# ==================== main ====================
def read_aloud():
    selected_item = chat_box.get(chat_box.curselection())

    engine = pyttsx3.init()

    voice = engine.getProperty('voices')
    engine.setProperty('voice', voice[1].id)

    engine.setProperty('rate', 150)

    engine.say(selected_item[5:])

    engine.runAndWait()


def show_line(text, index=4):
    if index < len(text):
        chat_box.delete(tk.END)
        chat_box.insert(tk.END, text[:index + 1])
        root.after(100, show_line, text, index + 1)

    chat_box.itemconfig(tk.END, {"fg": "green"})


def insert_text_with_newline(widget, text, max_chars_per_line=50):
    lines = [text[i:i + max_chars_per_line] for i in range(0, len(text), max_chars_per_line)]
    for line in lines:
        if "Bot:" in text:
            chat_box.insert(tk.END, "")
            show_line(line)
        else:
            widget.insert(tk.END, line)
    chat_box.config(foreground="black")


is_internet_connected()
root = tk.Tk()
root.iconbitmap(ico_path)
root.title("Chat Bot")

frame = tk.Frame(root)
scrollbar = ttk.Scrollbar(frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

chat_box = tk.Listbox(frame, height=15, width=80, yscrollcommand=scrollbar.set)
chat_box.pack(side=tk.LEFT, fill=tk.BOTH)

scrollbar.config(command=chat_box.yview)

frame.pack()

message_var = tk.StringVar()
message_entry = ttk.Entry(root, textvariable=message_var)
message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
message_entry.bind("<Return>", send_message)

# ==================== Send Button ====================

send_button = ttk.Button(root, text="Send", command=send_message)
send_button.pack(side=tk.RIGHT)


# ==================== Record Button Functions ====================

def record_audio():
    global text
    cap = pyaudio.PyAudio()
    stream = cap.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
    stream.start_stream()

    # recognized_text = []

    try:
        while True:
            data = stream.read(1024)
            if recognizer.AcceptWaveform(data):
                text = recognizer.Result()[14:-3]
    except KeyboardInterrupt:
        print("Listening stopped.")

    stream.stop_stream()
    stream.close()
    cap.terminate()


def button_released(event):
    global record_thread, text
    print(text)
    message_entry.config(foreground="black")
    message_var.set("")
    record_button.is_pressed = False
    record_thread.join()
    if text != "":
        message_var.set(text)


def button_pressed(event):
    global recognizer, record_thread
    model = Model(mod_path)
    recognizer = KaldiRecognizer(model, 16000)
    message_entry.config(foreground="red")
    message_var.set("I'm listening ...")
    record_button.is_pressed = True
    record_thread = threading.Thread(target=record_audio)
    record_thread.start()


# ==================== Record Button ====================
microphone_image = Image.open(img_path)
# ImageSize
microphone_image = microphone_image.resize((25, 15))
tk_microphone_image = ImageTk.PhotoImage(microphone_image)

record_button = ttk.Button(root, image=tk_microphone_image)
record_button.pack(side=tk.RIGHT)

record_button.bind("<ButtonPress-1>", button_pressed)
record_button.bind("<ButtonRelease-1>", button_released)
record_button.is_pressed = False
record_thread = None

context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="Read aloud", command=read_aloud)


def show_context_menu(event):
    context_menu.post(event.x_root, event.y_root)


chat_box.bind("<Button-3>", show_context_menu)

root.mainloop()
