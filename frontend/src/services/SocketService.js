import { io } from 'socket.io-client';

/**
 * Socket Service para la comunicación en tiempo real con el backend
 */
class SocketService {
  constructor() {
    this.socket = null;
    this.callbacks = {
      assistant_response: [],
      output_console: [],
      utilidades: [],
      connect: [],
      disconnect: []
    };
  }

  /**
   * Conecta con el servidor de socket
   */
  connect() {
    const socketUrl = process.env.REACT_APP_SOCKET_URL || window.location.origin;
    
    if (this.socket) {
      console.log('La conexión ya existe, utilizando la existente');
      return this.socket;
    }
    
    console.log('Conectando al socket en:', socketUrl);
    
    // Crear una nueva conexión Socket.IO
    this.socket = io(`${socketUrl}/test`, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    });

    // Configurar listeners para eventos estándar
    this.socket.on('connect', () => {
      console.log('Conectado a socket.io ✅');
      this.triggerCallbacks('connect');
    });

    this.socket.on('disconnect', (reason) => {
      console.log('Desconectado de socket.io:', reason);
      this.triggerCallbacks('disconnect');
    });

    this.socket.on('connect_error', (error) => {
      console.error('Error de conexión socket.io:', error);
    });

    // Configurar listeners para eventos personalizados
    this.socket.on('assistant_response', (data) => {
      this.triggerCallbacks('assistant_response', data);
    });

    this.socket.on('output_console', (data) => {
      this.triggerCallbacks('output_console', data);
    });

    this.socket.on('utilidades', (data) => {
      this.triggerCallbacks('utilidades', data);
    });

    return this.socket;
  }

  /**
   * Desconecta del servidor de socket
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      console.log('Desconectado del socket');
    }
  }

  /**
   * Emite un mensaje al servidor
   */
  emit(event, data) {
    if (!this.socket) {
      this.connect();
    }
    
    console.log('Emitiendo evento:', event, data);
    this.socket.emit(event, data);
  }

  /**
   * Registra un callback para un evento específico
   */
  on(event, callback) {
    if (!this.callbacks[event]) {
      this.callbacks[event] = [];
    }
    
    this.callbacks[event].push(callback);
    
    // Si el socket no está conectado, conectarlo
    if (!this.socket) {
      this.connect();
    }
    
    return () => this.off(event, callback); // Devuelve función para eliminar listener
  }

  /**
   * Elimina un callback para un evento específico
   */
  off(event, callback) {
    if (this.callbacks[event]) {
      this.callbacks[event] = this.callbacks[event].filter(cb => cb !== callback);
    }
  }

  /**
   * Activa todos los callbacks registrados para un evento
   */
  triggerCallbacks(event, data) {
    if (this.callbacks[event]) {
      this.callbacks[event].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error en callback para evento ${event}:`, error);
        }
      });
    }
  }

  /**
   * Verifica si el socket está conectado
   */
  isConnected() {
    return this.socket && this.socket.connected;
  }
}

export default new SocketService();
