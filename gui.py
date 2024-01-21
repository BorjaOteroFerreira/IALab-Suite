import tkinter as tk
from tkinter import scrolledtext
from threading import Thread
import queue
from llama2 import LlamaAssistant

class LlamaGUI:
    def __init__(self, master, llama_assistant):
        self.master = master
        self.llama_assistant = llama_assistant
        self.message_queue = queue.Queue()
            
        self.is_processing = False

        master.title("Llama Assistant Chat")

        self.chat_display = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=100, height=40)
        self.chat_display.pack(padx=10, pady=10)

        self.user_input_entry = tk.Entry(master, width=75)
        self.user_input_entry.pack(padx=10, pady=5)
        self.user_input_entry.bind("<Return>", self.send_user_input)

        self.send_button = tk.Button(master, text="Enviar", command=self.send_user_input)
        self.send_button.pack(pady=10)

        self.update_chat_display()
        self.send_button["state"] = "normal"  # Estado normal al inicio

    def send_user_input(self, event=None):
        user_input = self.user_input_entry.get()
        if user_input.lower() == 'exit':
            self.master.destroy()
        else:
            llama_assistant.add_user_input(user_input)
            self.is_processing = True
            self.send_button["state"] = "disabled"
            # Añadir el mensaje del usuario a la conversación 
            self.add_message_to_display(f"\n\nUsuario: {user_input}\n\nAsistente: \n")
            # Iniciar un hilo separado para manejar la inferencia
            Thread(target=self.infer_thread, daemon=True).start()

    def update_chat_display(self):
        while not self.message_queue.empty():
            message = self.message_queue.get()
            content = message["content"]
            # Añadir el mensaje a la conversación con un salto de línea previo
            self.add_message_to_display(f"{content}")
        # Desbloquear la interfaz gráfica después de mostrar la respuesta
        if not self.is_processing:
            self.send_button["state"] = "normal"

        self.master.after(100, self.update_chat_display)

    def add_message_to_display(self, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, message)
        self.chat_display.see(tk.END)  # Desplazar la barra de desplazamiento hasta el final
        self.chat_display.config(state=tk.DISABLED)
        self.user_input_entry.delete(0, tk.END)

    def infer_thread(self):
            llama_assistant.get_assistant_response(self.message_queue)
            # Actualizar la interfaz gráfica en el hilo principal
            self.master.after(0, self.update_chat_display)

# Bloque principal
if __name__ == "__main__":
    model_path = "./models/llama2_7b_chat_uncensored.Q8_0.gguf"
    llama_assistant = LlamaAssistant(model_path=model_path)

    root = tk.Tk()
    llama_gui = LlamaGUI(root, llama_assistant)

    root.mainloop()