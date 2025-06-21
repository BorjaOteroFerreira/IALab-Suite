class ChatService {
  static saveHistory(chatId, content) {
    return fetch('/actualizar_historial', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        nombre_chat: chatId,
        historial: content
      })
    })
    .then(response => response.json())
    .catch(error => console.error('Error saving history:', error));
  }

  static loadHistory(chatId) {
    return fetch(`/recuperar_historial?nombre_chat=${chatId}`)
      .then(response => response.json())
      .catch(error => console.error('Error loading history:', error));
  }

  static deleteHistory(chatId) {
    return fetch(`/eliminar_historial?nombre_chat=${chatId}`, {
      method: 'DELETE'
    })
    .then(response => response.json())
    .catch(error => console.error('Error deleting history:', error));
  }

  static loadModel(modelConfig) {
    const formData = new FormData();
    Object.keys(modelConfig).forEach(key => {
      if (modelConfig[key] !== undefined) {
        formData.append(key, modelConfig[key]);
      }
    });

    return fetch('/load_model', {
      method: 'POST',
      body: formData
    })
    .then(response => response.text())
    .catch(error => console.error('Error loading model:', error));
  }

  static unloadModel() {
    return fetch('/unload_model', {
      method: 'POST'
    })
    .then(response => response.text())
    .catch(error => console.error('Error unloading model:', error));
  }

  static stopResponse() {
    return fetch('/stop_response', {
      method: 'POST'
    })
    .then(response => response.text())
    .catch(error => console.error('Error stopping response:', error));
  }
}

export default ChatService;
