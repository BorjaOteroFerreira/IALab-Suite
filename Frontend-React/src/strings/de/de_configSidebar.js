// Strings auf Deutsch für ConfigSidebar
const de_configSidebar = {
  title: 'Modellkonfiguration',
  loadingModels: 'Modelle werden geladen...',
  selectModel: 'Modell auswählen',
  selectedModel: 'Ausgewähltes Modell:',
  modelsAvailable: (n) => `${n} Modell${n !== 1 ? 'e' : ''} verfügbar`,
  temperature: 'Temperatur:',
  temperaturePlaceholder: 'Beispiel: 0.8',
  context: 'Maximaler Kontext:',
  contextPlaceholder: 'Beispiel: 8192',
  systemMessage: 'Systemnachricht:',
  systemMessagePlaceholder: 'Sie sind ein Assistent auf Deutsch. Bitte immer auf Deutsch antworten.',
  gpuLayers: 'GPU-Schichten:',
  apply: 'Konfiguration anwenden',
  applying: 'Wird angewendet...',
  unload: 'Entladen',
  selectModelAlert: 'Bitte wählen Sie ein Modell aus',
  errorApply: 'Fehler beim Anwenden der Konfiguration. Siehe Konsole für Details.',
  vision: 'Vision',
  gb: 'GB',
  textareaDefault: 'Sie sind ein ehrlicher und hilfsbereiter Assistent',
};
export default de_configSidebar;
