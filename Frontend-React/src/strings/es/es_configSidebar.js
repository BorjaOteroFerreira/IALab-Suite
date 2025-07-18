// Strings en español para ConfigSidebar
export default {
  title: 'Configuración del modelo',
  loadingModels: 'Cargando modelos...',
  selectModel: 'Selecciona un modelo',
  selectedModel: 'Modelo seleccionado:',
  modelsAvailable: (n) => `${n} modelo${n !== 1 ? 's' : ''} disponible${n !== 1 ? 's' : ''}`,
  temperature: 'Temperatura:',
  temperaturePlaceholder: 'Ejemplo: 0.8',
  context: 'Contexto máximo:',
  contextPlaceholder: 'Ejemplo: 8192',
  systemMessage: 'Mensaje de sistema:',
  systemMessagePlaceholder: 'Eres un asistente en español. Debes responder siempre en español.',
  gpuLayers: 'Capas GPU:',
  apply: 'Aplicar configuración',
  applying: 'Aplicando...',
  unload: 'Desmontar',
  selectModelAlert: 'Por favor selecciona un modelo',
  errorApply: 'Error al aplicar la configuración. Revisa la consola para más detalles.',
  vision: 'visión',
  gb: 'GB',
  textareaDefault: 'Eres un asistente honesto y servicial',
};
