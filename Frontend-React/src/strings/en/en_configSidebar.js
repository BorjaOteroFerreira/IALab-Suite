// Strings in English for ConfigSidebar
export default {
  title: 'Model Configuration',
  loadingModels: 'Loading models...',
  selectModel: 'Select a model',
  selectedModel: 'Selected model:',
  modelsAvailable: (n) => `${n} model${n !== 1 ? 's' : ''} available`,
  temperature: 'Temperature:',
  temperaturePlaceholder: 'Example: 0.8',
  context: 'Max context:',
  contextPlaceholder: 'Example: 8192',
  systemMessage: 'System message:',
  systemMessagePlaceholder: 'You are an assistant in English. Always reply in English.',
  gpuLayers: 'GPU layers:',
  apply: 'Apply configuration',
  applying: 'Applying...',
  unload: 'Unload',
  selectModelAlert: 'Please select a model',
  errorApply: 'Error applying configuration. Check the console for more details.',
  vision: 'vision',
  gb: 'GB',
  textareaDefault: 'You are an assistant in English. Always reply in English.'
};
