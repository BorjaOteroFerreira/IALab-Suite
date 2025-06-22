// Polyfill global para React/Socket.io
window.global = window;

// Polyfill para Font Loading API
if (!document.fonts) {
  console.warn('La Font Loading API no está disponible en este navegador. Usando fallback para fuentes.');
  
  // Función básica para verificar si la fuente está cargada
  document.fonts = {
    ready: Promise.resolve(),
    check: () => true,
    load: () => Promise.resolve([]),
  };
}
