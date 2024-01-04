import tkinter as tk
from tkinter import messagebox, ttk
import openai
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

openai.api_key = config.get("openai", "api_key")


def api_key_and_model_selector():
    root = tk.Tk()
    root.title("OpenAI API Key and Model Selector")
    root.geometry("300x140")

    def api_update():
        config.set("openai", "api_key", api_val.get())
        api_entry.delete(0, tk.END)
        config.set("openai", "model", model_val.get())
        with open("config.ini", "w") as configfile:
            config.write(configfile)
        openai.api_key = config.get("openai", "api_key")

        root.destroy()

    label = ttk.Label(root, text="Please Enter Your Openai API code :")
    label.pack(padx=10, pady=10)

    api_val = tk.StringVar()
    api_entry = ttk.Entry(root, textvariable=api_val)
    api_entry.pack(padx=10, pady=10)

    model_val = tk.StringVar(value="gpt-3.5-turbo")
    model_combo = ttk.Combobox(root, textvariable=model_val)
    model_combo.pack()

    model_combo.config(values=["gpt-3.5-turbo", "gpt-3.5-turbo-0301", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-16k",
                               "gpt-3.5-turbo-16k-0613"])

    submit_button = ttk.Button(root, text="Submit", command=api_update)
    submit_button.pack(padx=10, pady=0)

    root.mainloop()


while openai.api_key == "":
    api_key_and_model_selector()


def send_message(event=None):
    message = message_var.get()
    message_entry.delete(0, tk.END)

    model = config.get("openai", "model")

    if message != "":
        chatbox.insert(tk.END, "You: " + message)
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": message}
                ]
            )
            chatbox.insert(tk.END, "AI: " + response['choices'][0]['message']['content'])
            message_var.set("")
        except openai.error.RateLimitError:
            messagebox.showerror("Error",
                                 "You exceeded your current quota, please check your plan and billing details.")
            api_key_and_model_selector()
        except openai.error.AuthenticationError:
            messagebox.showerror("Error",
                                 f"Incorrect API key provided: {openai.api_key}"
                                 f". You can find your API key at https://platform.openai.com/account/api-keys.")
            api_key_and_model_selector()


    else:
        messagebox.showerror("Error", "Message can't be empty!")


root = tk.Tk()
root.title("Chat Bot")

frame = tk.Frame(root)
scrollbar = ttk.Scrollbar(frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

chatbox = tk.Listbox(frame, height=15, width=50, yscrollcommand=scrollbar.set)
chatbox.pack(side=tk.LEFT, fill=tk.BOTH)
frame.pack()

scrollbar.config(command=chatbox.yview)

message_var = tk.StringVar()
message_entry = ttk.Entry(root, textvariable=message_var)
message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
message_entry.bind("<Return>", send_message)

send_button = ttk.Button(root, text="Send", command=send_message)
send_button.pack(side=tk.RIGHT)

root.mainloop()
