import tkinter as tk
from tkinter import ttk, scrolledtext
from threading import Thread
import queue
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name
from Assistant import Assistant 


class LlamaGUI:
    def __init__(self, master, assistant):
        self.master = master
        self.assistant = assistant
        self.message_queue = queue.Queue()
        self.is_processing = False
        self.stream_thread = None
        master.title("Assistant Chat")

        self.create_widgets()
        self.update_chat_display()

    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self.master, bg="#343a40", padx=10, pady=10)
        header_frame.pack(side=tk.TOP, fill=tk.X)

        clear_context_button = tk.Button(header_frame, text="Reset chat", bg="#555555", fg="black", command=self.clear_context)
        clear_context_button.pack(side=tk.RIGHT)

        # Container principal
        main_container = tk.Frame(self.master)
        main_container.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Footer
        footer_frame = tk.Frame(main_container, bg="#333333", padx=10, pady=10)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.stop_button = tk.Button(footer_frame, text="Stop", bg="#FF5555", fg="black", command=self.stop_stream)
        self.stop_button.pack(side=tk.LEFT)

        self.user_input_entry = tk.Entry(footer_frame, bg="#2C2C2C", fg="white", bd=1, insertbackground="white")
        self.user_input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.user_input_entry.bind("<Return>", self.send_user_input)

        send_button = tk.Button(footer_frame, text="Send", bg="#007ACC", fg="black", command=self.send_user_input)
        send_button.pack(side=tk.RIGHT)

        # Chat Container
        chat_container = tk.Frame(main_container, bg="#333333")
        chat_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(chat_container, wrap=tk.WORD, width=100, height=25, bg="#333333", fg="white")
        self.chat_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def send_user_input(self, event=None):
        user_input = self.user_input_entry.get()  
        if user_input.lower() == 'exit':
            self.master.destroy()
        else:
            self.assistant.add_user_input(user_input)
            self.is_processing = True
            self.add_message_to_display(f"\n\n User:\n\n {user_input}")
            self.add_message_to_display("\n\n Assistant:\n\n ")
            self.stop_button["state"] = "normal"
            self.stream_thread = Thread(target=self.infer_thread, daemon=False)
            self.stream_thread.start()

    def stop_stream(self):
        self.is_processing = False
        assistant.stop_response()
        self.master.after(100, self.update_chat_display)

    def clear_context(self):
        self.assistant.clear_context()
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.user_input_entry.delete(0, tk.END)


    def infer_thread(self):
        if self.is_processing:
            self.assistant.get_assistant_response_stream(self.message_queue)
            self.master.after(0, self.update_chat_display)

    def update_chat_display(self):
        while not self.message_queue.empty():
            message = self.message_queue.get()
            content = message["content"]
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, content)
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.user_input_entry.delete(0, tk.END)

        self.master.after(100, self.update_chat_display)

    def get_context_color(self, fraction):
        return "#007ACC"

    def add_message_to_display(self, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, message)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.user_input_entry.delete(0, tk.END)

if __name__ == "__main__":
    model_path = "models/llama/llama-2-7b-chat.Q8_0.gguf"
    chat_format = "llama-2"
    assistant = Assistant(default_model_path=model_path, default_chat_format=chat_format)

    root = tk.Tk()
    root.geometry("700x600")  # Ajusta el tamaño según tus necesidades
    llama_gui = LlamaGUI(root, assistant)

    root.mainloop()
