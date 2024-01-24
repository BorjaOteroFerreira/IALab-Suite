import tkinter as tk
from tkinter import ttk, scrolledtext
from threading import Thread
import queue
from stream.llama2 import LlamaAssistant

class LlamaGUI:
    def __init__(self, master, llama_assistant):
        self.master = master
        self.llama_assistant = llama_assistant
        self.message_queue = queue.Queue()
        self.is_processing = False
        self.stream_thread = None  # Variable para almacenar la referencia al hilo del stream

        master.title("Llama Assistant Chat")

        # Colores similares a Visual Studio Code
        vscode_bg_color = "#1E1E1E"
        vscode_fg_color = "#D4D4D4"
        vscode_button_color = "#007ACC"

        master.config(bg=vscode_bg_color)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TButton", padding=(10, 5, 10, 5), font=('Helvetica', 12), background=vscode_button_color, foreground=vscode_fg_color, borderwidth=0)
        style.configure("TEntry", padding=(5, 5, 5, 5), font=('Helvetica', 12), bg="1E1E1E", foreground="1E1E1E")
        style.configure("TProgressbar", thickness=20, troughrelief="flat", background="#1E1E1E", borderwidth=0, fg="#007ACC")

        self.master.columnconfigure(1, weight=1)  # Columna del chat expandible
        self.master.rowconfigure(1, weight=1)  # Fila del chat expandible

        self.progress_bar = ttk.Progressbar(master, orient="vertical", length=200, mode="determinate", style="TProgressbar")
        self.progress_bar.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.chat_display = scrolledtext.ScrolledText(master, font=('Helvetica', 16,), wrap=tk.WORD, width=100, height=70, bg=vscode_bg_color, fg="#007ACC")
        self.chat_display.grid(row=1, column=1, sticky="ew", padx=20, pady=10)

        self.user_input_entry = ttk.Entry(master, width=75)
        self.user_input_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        self.user_input_entry.bind("<Return>", self.send_user_input)

        self.stop_button = ttk.Button(master, text="Detener Stream", command=self.stop_stream)
        self.stop_button.grid(row=3, column=1, sticky="nsew", padx=10, pady=5)
        self.stop_button["state"] = "disabled"

        self.clear_button = ttk.Button(master, text="Limpiar Contexto", command=self.clear_context)
        self.clear_button.grid(row=4, column=1, sticky="nsew", padx=10, pady=5)

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
        # Limpiar el contenido de la pantalla
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        # Limpiar la entrada de usuario
        self.user_input_entry.delete(0, tk.END)
        # Restablecer la barra de progreso
        self.progress_bar["value"] = 0

    def infer_thread(self):
        if self.is_processing == True:
            self.llama_assistant.get_assistant_response(self.message_queue)
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
            context_fraction = self.llama_assistant.get_context_fraction()
            self.progress_bar["value"] = context_fraction * 100

            # Actualizar el color de la barra de progreso según el contexto
            context_color = self.get_context_color(context_fraction)
            style = ttk.Style()
            style.configure("TProgressbar", troughcolor="#1E1E1E", bordercolor=context_color, background=context_color)

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

# Bloque principal
if __name__ == "__main__":
    model_path = "models/TheBloke/Guanaco-13B-Uncensored-GGUF/guanaco-13b-uncensored.Q5_K_M.gguf"
    chat_format="guanaco"
    llama_assistant = LlamaAssistant(model_path=model_path, chat_format=chat_format)

    root = tk.Tk()
    root.geometry("700x1050")  # Ajusta el tamaño de la ventana según tus necesidades
    llama_gui = LlamaGUI(root, llama_assistant)

    root.mainloop()
