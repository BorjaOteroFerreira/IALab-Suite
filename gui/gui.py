from llama2 import LlamaAssistant
import tkinter as tk
from tkinter import ttk, scrolledtext
from threading import Thread
import queue

class LlamaGUI:
    def __init__(self, master, llama_assistant):
        self.master = master
        self.llama_assistant = llama_assistant
        self.message_queue = queue.Queue()
        self.is_processing = False

        master.title("Llama Assistant Chat")

        self.progress_bar = ttk.Progressbar(master, orient="vertical", length=200, mode="determinate")
        self.progress_bar.pack(side="left", padx=5, pady=75)

        self.chat_display = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=100, height=40)
        self.chat_display.pack(padx=10, pady=10)

        self.user_input_entry = tk.Entry(master, width=75)
        self.user_input_entry.pack(padx=10, pady=5)
        self.user_input_entry.bind("<Return>", self.send_user_input)

        self.stop_button = tk.Button(master, text="Detener Stream", command=self.stop_stream)
        self.stop_button.pack(pady=5)

        self.clear_button = tk.Button(master, text="Limpiar Contexto", command=self.clear_context)
        self.clear_button.pack(pady=5)
        self.update_chat_display()


    def send_user_input(self, event=None):
        user_input = self.user_input_entry.get()
        if user_input.lower() == 'exit':
            self.master.destroy()
        else:
            self.llama_assistant.add_user_input(user_input)
            self.is_processing = True
            self.add_message_to_display(f"\n\nUsuario:\n\n{user_input}\n\nAsistente:\n\n")
            self.stop_button["state"] = "normal"  # Activar el botón de detener
            Thread(target=self.infer_thread, daemon=True).start()


    def stop_stream(self):
            self.is_processing = False
            self.stop_button["state"] = "disabled"  # Disable the button instead of hiding it

    
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
        self.llama_assistant.get_assistant_response(self.message_queue)
        # Actualizar la interfaz gráfica en el hilo principal
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

            # Actualizar la barra de carga
            context_fraction = self.llama_assistant.get_context_fraction()
            self.progress_bar["value"] = context_fraction * 100

       


        self.master.after(100, self.update_chat_display)

    def add_message_to_display(self, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, message)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.user_input_entry.delete(0, tk.END)

    def infer_thread(self):
            llama_assistant.get_assistant_response(self.message_queue)
            # Actualizar la interfaz gráfica en el hilo principal
            self.master.after(0, self.update_chat_display)

# Bloque principal
if __name__ == "__main__":
    model_path = "models/TheBloke/NexusRaven-V2-13B-GGUF/nexusraven-v2-13b.Q4_K_S.gguf"
    chat_format="llama-2"
    llama_assistant = LlamaAssistant(model_path=model_path,chat_format=chat_format)

    root = tk.Tk()
    llama_gui = LlamaGUI(root, llama_assistant)

    root.mainloop()