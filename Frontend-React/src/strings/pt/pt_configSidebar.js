// Strings em português para ConfigSidebar
const pt_configSidebar = {
  title: 'Configuração do modelo',
  loadingModels: 'Carregando modelos...',
  selectModel: 'Selecione um modelo',
  selectedModel: 'Modelo selecionado:',
  modelsAvailable: (n) => `${n} modelo${n !== 1 ? 's' : ''} disponível${n !== 1 ? 's' : ''}`,
  temperature: 'Temperatura:',
  temperaturePlaceholder: 'Exemplo: 0.8',
  context: 'Contexto máximo:',
  contextPlaceholder: 'Exemplo: 8192',
  systemMessage: 'Mensagem do sistema:',
  systemMessagePlaceholder: 'Você é um assistente em português. Sempre responda em português.',
  gpuLayers: 'Camadas GPU:',
  apply: 'Aplicar configuração',
  applying: 'Aplicando...',
  unload: 'Desmontar',
  selectModelAlert: 'Por favor, selecione um modelo',
  errorApply: 'Erro ao aplicar a configuração. Verifique o console para mais detalhes.',
  vision: 'visão',
  gb: 'GB',
  textareaDefault: 'Você é um assistente honesto e prestativo',
};
export default pt_configSidebar;
