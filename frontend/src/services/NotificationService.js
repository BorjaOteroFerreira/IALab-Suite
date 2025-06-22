class NotificationService {
  static showNotification(message, type = 'info') {
    // Buscar o crear el contenedor de notificaciones
    let container = document.getElementById('notification-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'notification-container';
      document.body.appendChild(container);
    }

    // Crear la notificación
    const popup = document.createElement('div');
    popup.className = 'popup-notification';
    if (type === 'error') {
      popup.classList.add('error');
    }
    popup.textContent = message;
    container.appendChild(popup);

    // Mostrar con animación
    setTimeout(() => {
      popup.classList.add('show');
      
      // Ocultar después de un tiempo
      setTimeout(() => {
        popup.classList.remove('show');
        setTimeout(() => {
          if (container.contains(popup)) {
            container.removeChild(popup);
          }
        }, 300); // Tiempo para la animación de salida
      }, 3000); // Tiempo que se muestra la notificación
    }, 100);
  }
}

export default NotificationService;
