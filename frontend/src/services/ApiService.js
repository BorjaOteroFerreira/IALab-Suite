/**
 * API Service para la comunicación con el backend de Flask
 */
import NotificationService from './NotificationService';

class ApiService {
  constructor() {
    this.baseUrl = process.env.REACT_APP_API_URL || window.location.origin;
    this.maxRetries = 3;
    this.retryDelay = 1000;
  }

  /**
   * Realiza una petición HTTP con reintentos
   */
  async fetchWithRetry(url, options, retries = this.maxRetries) {
    try {
      console.log(`Petición a ${url}`, options);
      const response = await fetch(url, options);
      
      console.log(`Respuesta de ${url}:`, response);
      
      if (!response.ok) {
        throw new Error(`Error en la petición: ${response.status} ${response.statusText}`);
      }
      
      // Si es una respuesta vacía, devolver un array vacío
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        return data;
      } else {
        return {};
      }
    } catch (error) {
      console.error(`Error en petición a ${url}:`, error);
      
      // Reintentar solo si no es un error 4xx
      if (retries > 0 && !error.message.includes('4')) {
        console.log(`Reintentando en ${this.retryDelay}ms, ${retries} intentos restantes...`);
        
        return new Promise(resolve => {
          setTimeout(() => {
            resolve(this.fetchWithRetry(url, options, retries - 1));
          }, this.retryDelay);
        });
      }
      
      // Si no hay más reintentos o es un error 4xx, usar fallback o lanzar error
      throw error;
    }
  }

  /**
   * Obtiene la lista de modelos disponibles
   */
  async getModelsList() {
    try {
      console.log('Obteniendo lista de modelos...');
      const data = await this.fetchWithRetry(`${this.baseUrl}/models_list`);
      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.error('Error en getModelsList:', error);
      NotificationService.showNotification('Error cargando lista de modelos', 'error');
      return [];
    }
  }

  /**
   * Obtiene la lista de formatos de chat disponibles
   */
  async getFormatList() {
    try {
      console.log('Obteniendo lista de formatos...');
      const data = await this.fetchWithRetry(`${this.baseUrl}/format_list`);
      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.error('Error en getFormatList:', error);
      NotificationService.showNotification('Error cargando lista de formatos', 'error');
      return [];
    }
  }

  /**
   * Obtiene la lista de chats guardados
   */
  async getChatList() {
    try {
      console.log('Obteniendo lista de chats...');
      const data = await this.fetchWithRetry(`${this.baseUrl}/get_chat_list`);
      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.error('Error en getChatList:', error);
      NotificationService.showNotification('Error cargando lista de chats', 'error');
      return [];
    }
  }

  /**
   * Guarda el historial de chat
   */
  async saveChatHistory(history, chatName) {
    try {
      console.log('Guardando historial de chat...');
      await this.fetchWithRetry(`${this.baseUrl}/actualizar_historial`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          nombre_chat: chatName || 'Conversación_' + new Date().toISOString().substring(0, 19).replace(/:/g, '-'),
          historial: history
        })
      });
      
      return true;
    } catch (error) {
      console.error('Error en saveChatHistory:', error);
      NotificationService.showNotification('Error guardando historial de chat', 'error');
      return false;
    }
  }

  /**
   * Carga el historial de chat
   */
  async loadChatHistory(chatName) {
    try {
      console.log('Cargando historial de chat...');
      const data = await this.fetchWithRetry(`${this.baseUrl}/recuperar_historial?nombre_chat=${encodeURIComponent(chatName)}`);
      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.error('Error en loadChatHistory:', error);
      NotificationService.showNotification('Error cargando historial de chat', 'error');
      return [];
    }
  }

  /**
   * Elimina un chat guardado
   */
  async deleteChatHistory(chatName) {
    try {
      console.log('Eliminando historial de chat...');
      await this.fetchWithRetry(`${this.baseUrl}/eliminar_historial`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ chatName })
      });
      
      return true;
    } catch (error) {
      console.error('Error en deleteChatHistory:', error);
      NotificationService.showNotification('Error eliminando historial de chat', 'error');
      return false;
    }
  }

  /**
   * Verifica si el servidor está funcionando
   */
  async healthCheck() {
    try {
      await this.fetchWithRetry(`${this.baseUrl}/health`);
      return true;
    } catch (error) {
      console.error('Error en healthCheck:', error);
      return false;
    }
  }
}

export default new ApiService();
