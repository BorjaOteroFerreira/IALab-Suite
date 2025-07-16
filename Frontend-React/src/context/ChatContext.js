import React, { createContext, useState, useEffect, useCallback, useRef, useMemo } from 'react';
import io from 'socket.io-client';
import axios from 'axios';

export const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const [messages, setMessages] = useState([]);
  const [currentResponse, setCurrentResponse] = useState('');
  const [chatList, setChatList] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [socket, setSocket] = useState(null);
  const [modelConfig, setModelConfig] = useState({
    modelPath: '',
    format: 'chatml',
    temperature: 0.3,
    context: 8192,
    systemMessage: 'Eres un asistente en español. Debes responder siempre en español',
    gpuLayers: -1
  });
  const [tools, setTools] = useState(false);
  const [rag, setRag] = useState(false);
  const [currentAgent, setCurrentAgent] = useState(null);
  const [tokensCount, setTokensCount] = useState(0);
  const [modelList, setModelList] = useState([]);
  const [formatList, setFormatList] = useState([]);
  const [chatId, setChatId] = useState('');
  const [currentMessageId, setCurrentMessageId] = useState(null);
  
  // Estados para manejo de errores y carga
  const [error, setError] = useState(null);
  const [loadingType, setLoadingType] = useState('default');
  const [loadingMessage, setLoadingMessage] = useState('');
  const [savingChat, setSavingChat] = useState(false); // Nuevo estado para indicar guardado
  
  const socketRef = useRef(null);
  const conversationHistory = useRef([{ role: 'system', content: modelConfig.systemMessage }]);
  const messagesLengthRef = useRef(0);
  const finalizationProcessedRef = useRef(false);
  const currentResponseRef = useRef('');
  
  messagesLengthRef.current = messages.length;

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
    try {
      console.log('🔄 fetchChatList: Iniciando solicitud...');
      
      const isSafariIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
      const config = {
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      };
      
      if (isSafariIOS) {
        config.params = { _t: Date.now() };
      }
      
      const response = await axios.get('/recuperar_historial', config);
      console.log('✅ fetchChatList: Respuesta recibida, data:', response.data);
      
      setChatList(response.data);
    } catch (error) {
      console.error('❌ fetchChatList: Error al cargar la lista de chats:', error);
      showError(error);
    }
  }, [showError]);

  // Función para añadir un mensaje al chat
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
      if (prev.some(m => m.id === newId)) {
        console.log('⚠️ DEBUG: Mensaje duplicado detectado, ignorando:', newId);
        return prev;
      }
      console.log('✅ DEBUG: Añadiendo mensaje al historial:', newId);
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

  // Función para guardar el chat actual
  const saveChat = useCallback(async () => {
    if (messages.length === 0 && conversationHistory.current.length <= 1) {
      console.log('💾 DEBUG: No hay mensajes para guardar');
      return;
    }
    
    console.log('💾 DEBUG: Iniciando guardado del chat...');
    console.log('💾 DEBUG: chatId actual:', chatId);
    setSavingChat(true);
    
    try {
      let chatName = chatId;
      let isNewChat = false;
      
      // Si no hay chatId, crear uno nuevo (primera vez solamente)
      if (!chatId) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '.');
        const firstUserMessage = messages.find(m => m.role === 'user')?.content || '';
        const messagePreview = typeof firstUserMessage === 'string' 
          ? firstUserMessage 
          : firstUserMessage?.text || 'chat';
        const cleanName = messagePreview.substring(0, 30).replace(/[^a-zA-Z0-9]/g, '_');
        chatName = `${timestamp}-${cleanName}`;
        isNewChat = true;
        
        console.log('💾 DEBUG: Creando nuevo chat con nombre:', chatName);
        // Establecer el chatId ANTES de hacer la petición para evitar recreación
        setChatId(chatName);
      } else {
        console.log('💾 DEBUG: Actualizando chat existente:', chatName);
      }
      
      console.log('💾 DEBUG: Historial a guardar:', conversationHistory.current);
      
      await axios.post('/actualizar_historial', {
        nombre_chat: chatName,
        historial: conversationHistory.current
      });
      
      console.log('✅ DEBUG: Chat guardado exitosamente');
      
      // Actualizar la lista de chats solo si es un chat nuevo
      if (isNewChat) {
        console.log('💾 DEBUG: Actualizando lista de chats (chat nuevo)');
        await fetchChatList();
      } else {
        console.log('💾 DEBUG: No se actualiza lista (chat existente)');
      }
      
    } catch (error) {
      console.error('❌ Error al guardar el chat:', error);
      showError(error);
    } finally {
      setSavingChat(false);
    }
  }, [messages, conversationHistory.current, chatId, fetchChatList, showError]);

  // Inicializar Socket.io
  useEffect(() => {
    const listenerID = Math.random().toString(36).substr(2, 9);
    console.log('🔌 DEBUG: Creando nuevo socket con listener ID:', listenerID);
    
    const newSocket = io.connect(`http://${window.location.hostname}:8081/test`, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 5
    });

    newSocket.on('connect', () => {
      console.log('✅ Conectado al servidor Socket.io en puerto 8081, namespace /test');
    });

    newSocket.on('disconnect', () => {
      console.log('❌ Desconectado del servidor Socket.io');
    });

    newSocket.on('assistant_response', (response) => {
      console.log('🎯 DEBUG: assistant_response listener ejecutado, finished:', response.finished, 'content length:', response.content?.length || 0);
      
      if (response.content !== undefined) {
        if (response.error) {
          addMessageToChat('system', response.content);
          setIsLoading(false);
          return;
        }
        
        // Tokens del usuario
        if (response.user_tokens) {
          console.log('📊 DEBUG: Recibidos tokens del usuario:', response.user_tokens);
          setTokensCount(prev => {
            const newCount = prev + response.user_tokens;
            console.log('📊 DEBUG: Tokens anteriores:', prev, 'Tokens usuario:', response.user_tokens, 'Total:', newCount);
            return newCount;
          });
        }
        
        // Tokens del assistant
        if (response.assistant_token_count) {
          console.log('📊 DEBUG: Recibido token del assistant, count:', response.assistant_token_count);
          setTokensCount(prev => prev + response.assistant_token_count);
        }

        // Agregar contenido al stream
        if (response.content && response.content.length > 0) {
          console.log('📝 DEBUG: Agregando contenido al stream, length:', response.content.length);
          setCurrentResponse(prev => {
            const newResponse = prev + response.content;
            currentResponseRef.current = newResponse;
            console.log('📝 DEBUG: Nuevo currentResponse length:', newResponse.length);
            return newResponse;
          });
        }

        // ✅ GUARDADO AUTOMÁTICO: Solo cuando se completa la respuesta del asistente
        if (response.finished === true) {
          console.log('🏁 Señal de finalización recibida - Iniciando guardado automático');
          
          if (finalizationProcessedRef.current) {
            console.log('⚠️ DEBUG: Finalización ya procesada, ignorando');
            return;
          }
          
          finalizationProcessedRef.current = true;
          
          const currentResponseValue = currentResponseRef.current;
          console.log('🏁 Procesando finalización, currentResponse desde ref:', currentResponseValue.length);
          
          if (currentResponseValue.length > 0) {
            console.log('📝 Añadiendo mensaje de assistant al historial');
            addMessageToChat('assistant', currentResponseValue);
            
            // Guardar historial después de completar respuesta
            setTimeout(async () => {
              try {
                console.log('💾 Iniciando guardado automático tras completar respuesta...');
                await saveChat();
                console.log('✅ Guardado automático completado exitosamente');
              } catch (error) {
                console.error('❌ Error en guardado automático:', error);
              }
            }, 100); // Pequeño delay para asegurar que el mensaje se haya añadido
            
          } else {
            console.log('⚠️ WARNING: currentResponse está vacío, no se añade mensaje');
          }
          
          // Limpiar estado
          setCurrentResponse('');
          currentResponseRef.current = '';
          setIsLoading(false);
          
          // Resetear flag
          setTimeout(() => {
            finalizationProcessedRef.current = false;
          }, 100);
        }
      }
    });

    newSocket.on('output_console', (response) => {
      console.log('Output de consola:', response);
    });

    newSocket.on('response_stopped', (response) => {
      console.log('Respuesta detenida por el usuario:', response);
      setCurrentResponse('');
      currentResponseRef.current = '';
      setIsLoading(false);
      addMessageToChat('system', '⏹️ Respuesta detenida por el usuario');
      finalizationProcessedRef.current = false;
    });

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

    return () => {
      newSocket.disconnect();
    };
  }, [addMessageToChat, saveChat]); // Ahora saveChat está definido antes de usarse

  // Cargar datos iniciales
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const chatResponse = await axios.get('/recuperar_historial');
        setChatList(chatResponse.data);
        
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
  }, [showError]);

  // Función para enviar mensaje - SIN guardado automático aquí
  const sendMessage = useCallback(async (message) => {
    let text = '';
    let image_base64 = null;
    
    if (typeof message === 'string') {
      text = message.trim();
    } else if (typeof message === 'object' && message !== null) {
      text = (message.text || '').trim();
      image_base64 = message.image_base64 || null;
    }
    
    if (!text && !image_base64) {
      console.log('📤 DEBUG: sendMessage CANCELADO (mensaje vacío)');
      return;
    }
    
    console.log('📤 DEBUG: sendMessage LLAMADO con mensaje:', text.substring(0, 50) + '...' + (image_base64 ? ' [imagen]' : ''));
    
    const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setCurrentMessageId(messageId);
    setIsLoading(true);
    setLoadingType('thinking');
    setLoadingMessage('Procesando tu mensaje...');
    hideError();
    
    // Añadir mensaje del usuario
    addMessageToChat('user', image_base64 ? { text, image_base64 } : text);
    
    try {
      console.log('📤 Enviando historial al backend:', JSON.stringify(conversationHistory.current, null, 2));
      
      await axios.post('/user_input', {
        content: conversationHistory.current,
        tools,
        rag
      });
      

      
    } catch (error) {
      console.error('Error al enviar mensaje:', error);
      setIsLoading(false);
      showError(error);
    }
  }, [tools, rag, hideError, showError, addMessageToChat]);

  // Función para cargar un chat específico
  const loadChat = useCallback(async (chatName) => {
    try {
      const response = await axios.get(`/recuperar_historial?nombre_chat=${chatName}`);
      
      if (response.data && Array.isArray(response.data)) {
        setMessages(response.data);
        conversationHistory.current = response.data;
        setChatId(chatName);
        setTokensCount(0);
      }
    } catch (error) {
      console.error('Error al cargar el chat:', error);
      showError(error);
    }
  }, [showError]);

  // Función para crear un nuevo chat
  const newChat = useCallback(() => {
    setMessages([]);
    conversationHistory.current = [{ role: 'system', content: modelConfig.systemMessage }];
    setChatId(''); // Importante: resetear el chatId para que se cree uno nuevo
    setTokensCount(0);
  }, [modelConfig.systemMessage]);

  // Función para eliminar un chat
  const deleteChat = useCallback(async (chatName) => {
    try {
      await axios.delete(`/eliminar_historial?nombre_chat=${chatName}`);
      fetchChatList();
    } catch (error) {
      console.error('Error al eliminar el chat:', error);
      showError(error);
    }
  }, [fetchChatList, showError]);

  // Función para limpiar el chat
  const clearChat = useCallback(() => {
    setMessages([]);
    setCurrentResponse('');
    currentResponseRef.current = '';
    setTokensCount(0);
    setChatId(''); //resetear el chatId
    conversationHistory.current = [{ role: 'system', content: modelConfig.systemMessage }];
    setIsLoading(false);
    console.log('Chat limpiado 🗑️');
  }, [modelConfig.systemMessage]);

  // Función para cargar modelos y formatos
  const fetchModelsAndFormats = useCallback(async () => {
    try {
      console.log('ChatContext: Cargando modelos y formatos...');
      const response = await axios.get('/api/models-and-formats');
      
      const models = response.data.models || [];
      const formats = response.data.formats || [];
      
      setModelList(models);
      setFormatList(formats);
      
      return { models, formats };
    } catch (error) {
      console.error('ChatContext: Error al cargar modelos y formatos:', error);
      showError(error);
      return { models: [], formats: [] };
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

      const response = await axios.post('/load_model', formData);
      
      setModelConfig(config);
      clearChat();
      addMessageToChat('system', `Modelo ${config.modelPath.split('/').pop()} cargado correctamente`);
      
      console.log('✅ Modelo cargado exitosamente');
    } catch (error) {
      console.error('❌ Error en applyConfig:', error);
      showError(error);
      throw error;
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
      console.error('Error al detener la respuesta:', error);
      showError(error);
    }
  }, [addMessageToChat, showError]);

  // Contexto memoizado
  const contextValue = useMemo(() => ({
    messages,
    currentResponse,
    chatList,
    isLoading,
    savingChat, 
    tools,
    rag,
    currentAgent,
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
    clearChat,
    deleteChat,
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
    savingChat,
    tools, 
    rag, 
    currentAgent, 
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