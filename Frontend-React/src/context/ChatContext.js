import React, { createContext, useState, useEffect, useCallback, useRef, useMemo } from 'react';
import io from 'socket.io-client';
import axios from 'axios';

export const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const [messages, setMessages] = useState([]);
  const [currentResponse, setCurrentResponse] = useState('');
  const [chatList, setChatList] = useState([]);
  const [isLoading, setIsLoading] = useState(false);  const [socket, setSocket] = useState(null);
  const [modelConfig, setModelConfig] = useState({
    modelPath: '',
    format: 'chatml',
    temperature: 0.8,
    context: 8192,
    systemMessage: 'Eres un asistente en español. Debes responder siempre en español',
    gpuLayers: -1
  });
  const [tools, setTools] = useState(false);
  const [rag, setRag] = useState(false);
  const [currentAgent, setCurrentAgent] = useState(null); // Estado para el agente actual
  const [tokensCount, setTokensCount] = useState(0);
  const [modelList, setModelList] = useState([]);
  const [formatList, setFormatList] = useState([]);  const [chatId, setChatId] = useState('');
  const [currentMessageId, setCurrentMessageId] = useState(null);
  
  // Estados para manejo de errores y carga
  const [error, setError] = useState(null);
  const [loadingType, setLoadingType] = useState('default'); // Tipos: default, modelLoad, thinking, saving
  const [loadingMessage, setLoadingMessage] = useState('');
  const socketRef = useRef(null);
  const conversationHistory = useRef([{ role: 'system', content: modelConfig.systemMessage }]);
  const messagesLengthRef = useRef(0);
  const finalizationProcessedRef = useRef(false); // Flag para evitar procesamiento múltiple
  const currentResponseRef = useRef(''); // Referencia para el currentResponse actual
  
  // Actualizar la referencia cuando cambian los mensajes
  messagesLengthRef.current = messages.length;  // Función para añadir un mensaje al chat
  const addMessageToChat = useCallback((role, content, messageId = null) => {
    const newId = messageId || `${role}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    console.log('➕ DEBUG: addMessageToChat llamado, role:', role, 'id:', newId, 'content length:', content.length);
    const newMessage = {
      role,
      content,
      id: newId,
      timestamp: Date.now()
    };
    setMessages(prev => {
      // Si el mensaje ya existe por id, no lo agregues de nuevo
      if (prev.some(m => m.id === newId)) {
        console.log('⚠️ DEBUG: Mensaje duplicado detectado, ignorando:', newId);
        return prev;
      }
      console.log('✅ DEBUG: Añadiendo mensaje al historial:', newId);
      // Asegura que los mensajes se acumulen correctamente
      return [...prev, newMessage];
    });
    if (role === 'assistant') {
      const textContent = typeof content === 'object' && content.text ? content.text : content;
      conversationHistory.current.push({ role, content: textContent });
    } else if (role === 'user') {
      conversationHistory.current.push({ role, content });
    }
    return newMessage.id;
  }, []);
  // Inicializar Socket.io
  useEffect(() => {
    const listenerID = Math.random().toString(36).substr(2, 9);
    console.log('🔌 DEBUG: Creando nuevo socket con listener ID:', listenerID);
    
    // Usar port 8081 explícitamente para asegurar la conexión correcta
    const newSocket = io.connect(`http://${window.location.hostname}:8081/test`, {
      transports: ['websocket', 'polling'], // Priorizar websockets
      reconnection: true,
      reconnectionAttempts: 5
    });
      newSocket.on('connect', () => {
      console.log('✅ Conectado al servidor Socket.io en puerto 8081, namespace /test');
    });    newSocket.on('disconnect', () => {
      console.log('❌ Desconectado del servidor Socket.io');
    });    newSocket.on('assistant_response', (response) => {
      console.log('🎯 DEBUG: assistant_response listener ejecutado, finished:', response.finished, 'content length:', response.content?.length || 0);
      if (response.content !== undefined) {
        if (response.error) {
          addMessageToChat('system', response.content);
          setIsLoading(false);
          return;
        }
        
        // Si se reciben tokens del usuario (al inicio del stream)
        if (response.user_tokens) {
          console.log('📊 DEBUG: Recibidos tokens del usuario:', response.user_tokens);
          setTokensCount(prev => {
            const newCount = prev + response.user_tokens;
            console.log('📊 DEBUG: Tokens anteriores:', prev, 'Tokens usuario:', response.user_tokens, 'Total:', newCount);
            return newCount;
          });
        }
        
        // Si se reciben tokens del assistant (en tiempo real)
        if (response.assistant_token_count) {
          console.log('📊 DEBUG: Recibido token del assistant, count:', response.assistant_token_count);
          setTokensCount(prev => prev + response.assistant_token_count);
        }

        // Para contenido no vacío, agregar al stream actual
        if (response.content && response.content.length > 0) {
          console.log('📝 DEBUG: Agregando contenido al stream, length:', response.content.length);
          setCurrentResponse(prev => {
            const newResponse = prev + response.content;
            currentResponseRef.current = newResponse; // Mantener ref sincronizada
            console.log('📝 DEBUG: Nuevo currentResponse length:', newResponse.length);
            return newResponse;
          });
        }// Si la respuesta está marcada como finalizada
        if (response.finished === true) {
          console.log('🏁 Señal de finalización recibida');
          
          // Evitar procesamiento múltiple usando ref
          if (finalizationProcessedRef.current) {
            console.log('⚠️ DEBUG: Finalización ya procesada, ignorando');
            return;
          }
          
          finalizationProcessedRef.current = true;          // Obtener el valor actual de currentResponse usando la referencia
          const currentResponseValue = currentResponseRef.current;
          console.log('🏁 Procesando finalización, currentResponse desde ref:', currentResponseValue.length);
          console.log('🏁 Primeros 100 chars:', currentResponseValue.substring(0, 100));
          
          if (currentResponseValue.length > 0) {
            console.log('📝 Añadiendo mensaje de assistant al historial');
            addMessageToChat('assistant', currentResponseValue);
          } else {
            console.log('⚠️ WARNING: currentResponse está vacío, no se añade mensaje');
          }
            // Limpiar el estado y ref
          setCurrentResponse('');
          currentResponseRef.current = '';
          setIsLoading(false);
            // Resetear el flag después de un pequeño delay
          setTimeout(() => {
            finalizationProcessedRef.current = false;
          }, 100);
        }
      }
    });    newSocket.on('output_console', (response) => {
      console.log('Output de consola:', response);
      // TODO: implementar un área de consola visible en la UI 
    });

    // Listener para respuesta detenida
    newSocket.on('response_stopped', (response) => {
      console.log('Respuesta detenida por el usuario:', response);
      setCurrentResponse('');
      currentResponseRef.current = '';
      setIsLoading(false);
      addMessageToChat('system', '⏹️ Respuesta detenida por el usuario');
      
      // Resetear el flag de finalización
      finalizationProcessedRef.current = false;
    });

    // Listeners para agentes
    newSocket.on('agent_changed', (data) => {
      console.log('🤖 Agent changed:', data);
      setCurrentAgent(data.agent_name);
    });

    newSocket.on('agents_registry', (data) => {
      console.log('🤖 Agents registry received:', data);
      setCurrentAgent(data.current_agent);
    });

    setSocket(newSocket);
    socketRef.current = newSocket;

    // Limpiar socket al desmontar
    return () => {
      newSocket.disconnect();
    };
  }, [addMessageToChat]);

  // Función para mostrar errores
  const showError = useCallback((errorObj, autoHideMs = 0) => {
    setError({
      message: errorObj?.message || errorObj?.toString() || 'Error desconocido',
      timeout: autoHideMs
    });
  }, []);

  // Función para ocultar error
  const hideError = useCallback(() => {
    setError(null);
  }, []);
  // Función para cargar la lista de chats
  const fetchChatList = useCallback(async () => {
    try {      console.log('🔄 fetchChatList: Iniciando solicitud...');
      console.log('🔄 fetchChatList: User Agent:', navigator.userAgent);
      console.log('🔄 fetchChatList: Es Safari iOS:', /iPad|iPhone|iPod/.test(navigator.userAgent));
      
      // Fix específico para Safari iOS - evitar cache
      const isSafariIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
      const config = {
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      };
      
      if (isSafariIOS) {
        config.params = { _t: Date.now() }; // Timestamp para evitar cache
      }
      
      const response = await axios.get('/recuperar_historial', config);
      
      console.log('✅ fetchChatList: Respuesta recibida');
      console.log('✅ fetchChatList: Status:', response.status);
      console.log('✅ fetchChatList: Headers:', response.headers);
      console.log('✅ fetchChatList: Data raw:', response.data);
      console.log('✅ fetchChatList: Tipo de data:', typeof response.data);
      console.log('✅ fetchChatList: Es array:', Array.isArray(response.data));
      
      if (Array.isArray(response.data)) {
        console.log('✅ fetchChatList: Longitud del array:', response.data.length);
        console.log('✅ fetchChatList: Primer elemento:', response.data[0]);
      }
      
      setChatList(response.data);
      console.log('✅ fetchChatList: setChatList ejecutado');
    } catch (error) {
      console.error('❌ fetchChatList: Error al cargar la lista de chats:', error);
      console.error('❌ fetchChatList: Error response:', error.response);
      console.error('❌ fetchChatList: Error status:', error.response?.status);
      showError(error);
    }
  }, [showError]);
  // Cargar datos iniciales solo una vez al montar el componente
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        // Cargar lista de chats
        const chatResponse = await axios.get('/recuperar_historial');
        setChatList(chatResponse.data);
        
        // Cargar modelos y formatos
        const modelsResponse = await axios.get('/api/models-and-formats');
        setModelList(modelsResponse.data.models || []);
        setFormatList(modelsResponse.data.formats || []);
        
        console.log('✅ Datos iniciales cargados correctamente');
      } catch (error) {
        console.error('❌ Error al cargar datos iniciales:', error);
        showError(error);
      }
    };
    
    loadInitialData();
  }, []); // Sin dependencias para ejecutar solo una vez  // Función para enviar mensaje - optimizada con useCallback
  const sendMessage = useCallback(async (message) => {
    // Soporte para string o objeto (texto + imagen)
    let text = '';
    let image_base64 = null;
    if (typeof message === 'string') {
      text = message.trim();
    } else if (typeof message === 'object' && message !== null) {
      text = (message.text || '').trim();
      image_base64 = message.image_base64 || null;
    }
    // Si no hay texto ni imagen, cancelar
    if (!text && !image_base64) {
      console.log('📤 DEBUG: sendMessage CANCELADO (mensaje vacío)');
      return;
    }
    console.log('📤 DEBUG: sendMessage LLAMADO con mensaje:', text.substring(0, 50) + '...' + (image_base64 ? ' [imagen]' : ''));
    // Generar un ID único para este mensaje
    const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setCurrentMessageId(messageId);
    setIsLoading(true);
    setLoadingType('thinking');
    setLoadingMessage('Procesando tu mensaje...');
    hideError();
    // Añadir mensaje del usuario al chat (esto ya actualiza conversationHistory.current)
    addMessageToChat('user', image_base64 ? { text, image_base64 } : text);
    try {
      // Debug: mostrar el historial que se va a enviar
      console.log('📤 Enviando historial al backend:', JSON.stringify(conversationHistory.current, null, 2));
      // Enviar mensaje al servidor con el historial actual
      await axios.post('/user_input', {
        content: conversationHistory.current,
        tools,
        rag
      });
      // La respuesta vendrá a través de Socket.io
      // También guardamos automáticamente el chat después de enviar un mensaje
      if (messages.length > 0 || conversationHistory.current.length > 1) {
        setLoadingType('saving');
        setLoadingMessage('Guardando conversación...');
        await saveChat();
      }
    } catch (error) {
      console.error('Error al enviar mensaje:', error);
      setIsLoading(false);
      showError(error);
    }
  }, [messages.length, tools, rag, hideError, showError, addMessageToChat]);

  // Función para cargar un chat específico
  const loadChat = useCallback(async (chatName) => {
    try {
      const response = await axios.get(`/recuperar_historial?nombre_chat=${chatName}`);
        if (response.data && Array.isArray(response.data)) {
        setMessages(response.data);
        conversationHistory.current = response.data;
        setChatId(chatName);
        setTokensCount(0); // Reiniciar contador de tokens para el chat cargado
      }
    } catch (error) {
      console.error('Error al cargar el chat:', error);
      showError(error);
    }
  }, []);

  // Función para crear un nuevo chat
  const newChat = useCallback(() => {
    setMessages([]);
    conversationHistory.current = [{ role: 'system', content: modelConfig.systemMessage }];
    setChatId('');
    setTokensCount(0); // Reiniciar contador de tokens
  }, [modelConfig.systemMessage]);

  // Función para eliminar un chat
  const deleteChat = useCallback(async (chatName) => {
    try {
      await axios.delete(`/eliminar_historial?nombre_chat=${chatName}`);
      // Actualizar la lista de chats
      fetchChatList();
    } catch (error) {
      console.error('Error al eliminar el chat:', error);
      showError(error);
    }
  }, [fetchChatList]);

  // Función para guardar el chat actual
  const saveChat = useCallback(async () => {
    if (messages.length === 0) return;
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '.');
    const firstUserMessage = messages.find(m => m.role === 'user')?.content || '';
    const chatName = firstUserMessage.substring(0, 30).replace(/[^a-zA-Z0-9]/g, '_');
    const fullChatName = `${timestamp}-${chatName}`;
    
    try {
      await axios.post('/actualizar_historial', {
        nombre_chat: fullChatName,
        historial: conversationHistory.current
      });
      
      setChatId(fullChatName);
      // Actualizar la lista de chats
      fetchChatList();
    } catch (error) {
      console.error('Error al guardar el chat:', error);      showError(error);
    }
  }, [messages, fetchChatList]);

  // Función para limpiar el chat (newChat en el JS original)
  const clearChat = useCallback(() => {
    setMessages([]);
    setCurrentResponse('');
    currentResponseRef.current = ''; // Limpiar también la ref
    setTokensCount(0);
    setChatId('');
    conversationHistory.current = [{ role: 'system', content: modelConfig.systemMessage }];
    setIsLoading(false);
    console.log('Chat limpiado 🗑️');
  }, [modelConfig.systemMessage]);
  // Función para cargar modelos y formatos disponibles
  const fetchModelsAndFormats = useCallback(async () => {
    try {
      console.log('ChatContext: Cargando modelos y formatos...');
      const response = await axios.get('/api/models-and-formats');
      
      const models = response.data.models || [];
      const formats = response.data.formats || [];
      
      console.log(`ChatContext: ${models.length} modelos y ${formats.length} formatos cargados`);
      
      setModelList(models);
      setFormatList(formats);
      
      return {
        models,
        formats
      };
    } catch (error) {
      console.error('ChatContext: Error al cargar modelos y formatos:', error);
      showError(error);
      return {
        models: [],
        formats: []
      };
    }
  }, [showError]);
  // Función para aplicar configuración del modelo
  const applyConfig = useCallback(async (config) => {
    try {
      console.log('🔄 ApplyConfig iniciado con:', config);
      
      setLoadingType('modelLoad');
      setLoadingMessage('Cargando modelo...');
      setIsLoading(true);

      const formData = new FormData();
      formData.append('model_path', config.modelPath);
      formData.append('format', config.format);
      formData.append('temperature', config.temperature.toString());
      formData.append('gpu_layers', config.gpuLayers.toString());
      formData.append('context', config.context.toString());
      formData.append('system_message', config.systemMessage);

      console.log('📤 Enviando FormData a /load_model:');
      console.log('- model_path:', config.modelPath);
      console.log('- format:', config.format);
      console.log('- temperature:', config.temperature.toString());
      console.log('- gpu_layers:', config.gpuLayers.toString());
      console.log('- context:', config.context.toString());
      console.log('- system_message:', config.systemMessage);

      const response = await axios.post('/load_model', formData);
      
      console.log('📥 Respuesta del servidor:', response.data);
      
      setModelConfig(config);
      clearChat();
      addMessageToChat('system', `Modelo ${config.modelPath.split('/').pop()} cargado correctamente`);
      
      console.log('✅ Modelo cargado exitosamente');
    } catch (error) {
      console.error('❌ Error en applyConfig:', error);
      console.error('Error details:', error.response?.data);
      console.error('Error status:', error.response?.status);
      showError(error);
      throw error; // Re-lanzar el error para que el sidebar pueda manejarlo
    } finally {
      setIsLoading(false);
      setLoadingType('default');
      setLoadingMessage('');
    }
  }, [clearChat, addMessageToChat, showError]);

  // Función para descargar modelo
  const unloadModel = useCallback(async () => {
    try {
      const response = await axios.post('/unload_model');
      addMessageToChat('system', 'Modelo descargado 🫗');
      console.log('Modelo descargado:', response.data);
    } catch (error) {
      console.error('Error al descargar el modelo:', error);
      showError(error);
    }
  }, [addMessageToChat, showError]);

  // Función para detener respuesta
  const stopResponse = useCallback(async () => {
    try {
      const response = await axios.post('/stop_response');
      setCurrentResponse('');
      setIsLoading(false);
      addMessageToChat('system', 'Respuesta detenida ⏹️');
      console.log('Respuesta detenida:', response.data);
    } catch (error) {
      console.error('Error al detener la respuesta:', error);      showError(error);
    }
  }, [addMessageToChat, showError]);  // Crear objeto de contexto memoizado para evitar re-renderizaciones innecesarias
  const contextValue = useMemo(() => ({
    messages,
    currentResponse,
    chatList,
    isLoading,
    tools,
    rag,
    currentAgent, // Agregar el agente actual para que los componentes puedan mostrarlo
    tokensCount,
    modelConfig,
    chatId,
    modelList,
    formatList,
    error,
    loadingType,    
    loadingMessage,
    currentMessageId,
    socket,
    setTools,
    setRag,
    setModelConfig,
    sendMessage,
    loadChat,
    clearChat,    deleteChat,
    saveChat,
    applyConfig,
    loadModel: applyConfig,
    unloadModel,
    stopResponse,
    fetchChatList,
    fetchModelsAndFormats,
    showError,
    hideError
  }), [
    messages, 
    currentResponse, 
    chatList, 
    isLoading, 
    tools, 
    rag, 
    currentAgent, // Agregar dependencia del agente actual
    tokensCount, 
    modelConfig, 
    chatId, 
    modelList, 
    formatList,    error, 
    loadingType, 
    loadingMessage,
    currentMessageId,
    setTools, 
    setRag,
    sendMessage, 
    loadChat, 
    clearChat,
    deleteChat,
    saveChat,
    applyConfig,
    unloadModel,
    stopResponse,
    fetchChatList,
    fetchModelsAndFormats,
    showError,
    hideError
  ]);
  return (
    <ChatContext.Provider value={contextValue}>
      {children}
    </ChatContext.Provider>
  );
};
