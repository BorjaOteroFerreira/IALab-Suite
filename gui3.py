import tkinter as tk
from tkinter import ttk, scrolledtext
from threading import Thread
import queue
from app import LlamaAssistant
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name
import llama_cpp

class LlamaGUI:
    def __init__(self, master, llama_assistant):
        self.master = master
        self.llama_assistant = llama_assistant
        self.message_queue = queue.Queue()
        self.is_processing = False
        self.stream_thread = None
        master.title("Llama Assistant Chat")
        # Colores similares a Visual Studio Code
        vscode_bg_color = "#1E1E1E"
        vscode_fg_color = "#D4D4D4"
        vscode_button_color = "#007ACC"

        master.config(bg=vscode_bg_color)
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TButton", padding=(10, 5, 10, 5), font=('Helvetica', 12), background=vscode_button_color, foreground=vscode_fg_color, borderwidth=0)
        style.configure("TEntry", padding=(5, 5, 5, 5), font=('Helvetica', 12), bg=vscode_bg_color, foreground=vscode_bg_color)
        style.configure("TProgressbar", thickness=20, troughrelief="flat", background=vscode_bg_color, borderwidth=0, fg=vscode_button_color)

        self.master.columnconfigure(1, weight=1)
        self.master.rowconfigure(1, weight=1)

        self.progress_bar = ttk.Progressbar(master, orient="vertical", length=200, mode="determinate", style="TProgressbar")
        self.progress_bar.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.chat_display = scrolledtext.ScrolledText(master,  wrap=tk.WORD, width=100, height=70, bg=vscode_bg_color, fg=vscode_button_color)
        self.chat_display.grid(row=1, column=1, sticky="ew", padx=20, pady=10)

        self.user_input_entry = ttk.Entry(master, width=75)
        self.user_input_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        self.user_input_entry.bind("<Return>", self.send_user_input)

        self.stop_button = ttk.Button(master, text="Detener Stream", command=self.stop_stream)
        self.stop_button.grid(row=3, column=1, sticky="nsew", padx=10, pady=5)
        self.stop_button["state"] = "disabled"

        self.clear_button = ttk.Button(master, text="Limpiar Contexto", command=self.clear_context)
        self.clear_button.grid(row=4, column=1, sticky="nsew", padx=10, pady=5)

        # Configurar Pygments para resaltar el código
        self.code_lexer = get_lexer_by_name("java")
        self.code_formatter = get_formatter_by_name("html")

        self.update_chat_display()

    def send_user_input(self, event=None):
        
        user_input = self.user_input_entry.get()  
        if user_input.lower() == 'exit':
            self.master.destroy()
        else:
            self.llama_assistant.add_user_input(user_input)
            self.is_processing = True
            self.add_message_to_display(f"\n\n Usuario:\b  {user_input}")
            self.stop_button["state"] = "normal"
            self.stream_thread = Thread(target=self.infer_thread, daemon=False)
            self.stream_thread.start()

    def stop_stream(self):
        self.is_processing = False
        self.master.after(100, self.update_chat_display)

    def clear_context(self):
        self.llama_assistant.clear_context()
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.user_input_entry.delete(0, tk.END)
        self.progress_bar["value"] = 0

    def infer_thread(self):
        if self.is_processing == True:
            self.llama_assistant.get_assistant_response_stream(self.message_queue)
            self.master.after(0, self.update_chat_display)

    def update_chat_display(self):
        while not self.message_queue.empty():
            message = self.message_queue.get()
            content = message["content"]
            self.chat_display.config(state=tk.NORMAL)
            # Verificar si el mensaje contiene código y resaltarlo
            if "```" in content:
                code_lines = content.split("```")[1]
                formatted_code = highlight(code_lines, self.code_lexer, self.code_formatter)
                content = content.replace(code_lines, formatted_code)

            context_fraction = self.llama_assistant.get_context_fraction()
            self.progress_bar["value"] = context_fraction * 100
            # Actualizar el color de la barra de progreso según el contexto
            context_color = self.get_context_color(context_fraction)
            style = ttk.Style()
            style.configure("TProgressbar", troughcolor="#1E1E1E", bordercolor=context_color, background=context_color)
            self.chat_display.insert(tk.END, content)
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.user_input_entry.delete(0, tk.END)
        if not self.is_processing:
            self.stop_button["state"] = "disabled"

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
    model_path = "models/TheBloke/llama2_7b_chat_uncensored-GGUF/llama2_7b_chat_uncensored.Q8_0.gguf"
    chat_format = "tb-uncensored"
    llama_assistant = LlamaAssistant(model_path=model_path, chat_format=chat_format)

    root = tk.Tk()
    root.geometry("700x1050")
    llama_gui = LlamaGUI(root, llama_assistant)

    root.mainloop()
