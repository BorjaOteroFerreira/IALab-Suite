def get_assistant_response(self, user_input):
  # Obtener la respuesta del modelo Llama2 
output = self.llm.create_chat_completion(messages=self.conversation_history, max_tokens=2048, language="es") 
# Filtrar las respuestas en español 
# Obtener la respuesta del modelo 
Llama2 response = output['choices'][0]['message']['content'] 
# Añadir la respuesta al historial de la conversación 
self.conversation_history.append({"role": "assistant", "content": response})
 # Añadir la respuesta al historial de la conversación return response 
# Devolver la respuesta del modelo Llama2 
