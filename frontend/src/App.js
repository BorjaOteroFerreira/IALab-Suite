import React, { useState, useEffect } from 'react';
import './App.css';
import ChatSidebar from './components/ChatSidebar';
import MainContainer from './components/MainContainer';
import ConfigSidebar from './components/ConfigSidebar';
import HelpModal from './components/HelpModal';
import SocketService from './services/SocketService';
import ApiService from './services/ApiService';
import NotificationService from './services/NotificationService';

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [tools, setTools] = useState(false);
  const [rag, setRag] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [totalTokens, setTotalTokens] = useState(0);
  const [currentResponse, setCurrentResponse] = useState('');
  const [fullResponse, setFullResponse] = useState('');
  const [responseNumber, setResponseNumber] = useState(0);
  const [conversationStarted, setConversationStarted] = useState(false);
  const [chatId, setChatId] = useState(' ');
  const [library, setLibrary] = useState('llama');
  const [chatList, setChatList] = useState([]);
  const [modelsList, setModelsList] = useState([]);
  const [formatList, setFormatList] = useState([]);
  const [showHelpModal, setShowHelpModal] = useState(false);
  const [isConfigSidebarOpen, setIsConfigSidebarOpen] = useState(false);
  const [isChatSidebarOpen, setIsChatSidebarOpen] = useState(true);

  // Cargar listas al iniciar la aplicación
  useEffect(() => {
    loadInitialData();
  }, []);

  // Inicializar Socket.IO
  useEffect(() => {
    // Conectar al socket
    const socket = SocketService.connect();

    // Configurar listeners para eventos
    const connectHandler = () => {
      setIsConnected(true);
      NotificationService.showNotification('Conectado al servidor', 'success');
    };

    const disconnectHandler = () => {
      setIsConnected(false);
      NotificationService.showNotification('Desconectado del servidor', 'error');
    };

    const responseHandler = (response) => {
      handleAssistantResponse(response);
    };

    const consoleHandler = (response) => {
      handleConsoleOutput(response);
    };

    const utilitiesHandler = (response) => {
      loadUtilities(response);
    };

    // Registrar handlers
    SocketService.on('connect', connectHandler);
    SocketService.on('disconnect', disconnectHandler);
    SocketService.on('assistant_response', responseHandler);
    SocketService.on('output_console', consoleHandler);
    SocketService.on('utilidades', utilitiesHandler);

    // Inicializar el historial de conversación con el mensaje del sistema
    setChatHistory([{
      'role': 'system',
      'content': 'Eres un asistente en español. Debes responder siempre en español'
    }]);

    // Limpieza al desmontar el componente
    return () => {
      SocketService.off('connect', connectHandler);
      SocketService.off('disconnect', disconnectHandler);
      SocketService.off('assistant_response', responseHandler);
      SocketService.off('output_console', consoleHandler);
      SocketService.off('utilidades', utilitiesHandler);
      SocketService.disconnect();
    };
  }, []);

  // Cargar datos iniciales (chats, modelos, formatos)
  const loadInitialData = async () => {
    setIsLoading(true);

    try {
      // Cargar chats
      const chats = await ApiService.getChatList();
      setChatList(chats);

      // Cargar modelos
      const models = await ApiService.getModelsList();
      setModelsList(models);

      // Cargar formatos
      const formats = await ApiService.getFormatList();
      setFormatList(formats);
    } catch (error) {
      console.error('Error cargando datos iniciales:', error);
      NotificationService.showNotification('Error cargando datos iniciales', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAssistantResponse = (response) => {
    let delta = '';

    try {
      if (typeof response === 'string') {
        // Intentar parsear como JSON si es una cadena
        const parsedResponse = JSON.parse(response);
        delta = parsedResponse.text || '';
      } else {
        // Si ya es un objeto, extraer directamente
        delta = response.text || '';
      }

      // Actualizar respuesta actual
      setCurrentResponse(prev => prev + delta);

      // Si es el final de la respuesta
      if (response.finish) {
        const fullContent = currentResponse + delta;
        setFullResponse(fullContent);

        // Actualizar historial con la respuesta completa
        setChatHistory(prevHistory => {
          // Crear una copia del historial actual
          const newHistory = [...prevHistory];

          // Verificar si ya existe una respuesta del asistente para esta pregunta
          const lastAssistantIndex = newHistory.findIndex(
            msg => msg.role === 'assistant' && msg.responseNumber === responseNumber
          );

          if (lastAssistantIndex !== -1) {
            // Actualizar respuesta existente
            newHistory[lastAssistantIndex].content = fullContent;
          } else {
            // Agregar nueva respuesta
            newHistory.push({
              role: 'assistant',
              content: fullContent,
              responseNumber: responseNumber
            });
          }

          return newHistory;
        });

        // Actualizar tokens y limpiar respuesta actual
        if (response.tokens) {
          setTotalTokens(response.tokens);
        }

        setCurrentResponse('');
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Error procesando respuesta:', error);
      NotificationService.showNotification('Error procesando respuesta', 'error');
    }
  };

  const handleConsoleOutput = (response) => {
    console.log('Salida consola:', response);
    // Puedes mostrar esto en algún lugar de la UI si lo necesitas
  };

  const loadUtilities = (response) => {
    try {
      const utils = typeof response === 'string' ? JSON.parse(response) : response;

      if (utils.tools !== undefined) {
        setTools(utils.tools);
      }

      if (utils.rag !== undefined) {
        setRag(utils.rag);
      }

      if (utils.tokens !== undefined) {
        setTotalTokens(utils.tokens);
      }

      if (utils.library !== undefined) {
        setLibrary(utils.library);
      }
    } catch (error) {
      console.error('Error cargando utilidades:', error);
    }
  };

  const sendMessage = (message) => {
    if (!message.trim()) return;

    // Actualizar historial con el mensaje del usuario
    const updatedHistory = [...chatHistory, { role: 'user', content: message }];
    setChatHistory(updatedHistory);

    // Incrementar contador de respuestas
    const newResponseNumber = responseNumber + 1;
    setResponseNumber(newResponseNumber);

    // Indicar que la conversación ha comenzado
    if (!conversationStarted) {
      setConversationStarted(true);
    }

    // Indicar que estamos cargando
    setIsLoading(true);

    // Enviar mensaje al backend
    try {
      SocketService.emit('user_input', {
        message,
        history: updatedHistory.filter(msg => msg.role !== 'system'),
        chatId
      });
    } catch (error) {
      console.error('Error enviando mensaje:', error);
      NotificationService.showNotification('Error enviando mensaje', 'error');
      setIsLoading(false);
    }
  };

  const stopResponse = () => {
    try {
      SocketService.emit('stop_generation', {});
      setIsLoading(false);
      NotificationService.showNotification('Generación detenida', 'info');
    } catch (error) {
      console.error('Error deteniendo respuesta:', error);
    }
  };

  const newChat = () => {
    // Restablecer estado
    setChatHistory([{
      'role': 'system',
      'content': 'Eres un asistente en español. Debes responder siempre en español'
    }]);
    setTotalTokens(0);
    setCurrentResponse('');
    setFullResponse('');
    setResponseNumber(0);
    setConversationStarted(false);
    setChatId(' ');

    NotificationService.showNotification('Nueva conversación iniciada', 'info');
  };

  const loadHistory = async (chatName) => {
    try {
      setIsLoading(true);

      const response = await fetch(`/recuperar_historial?nombre_chat=${chatName}`);
      if (!response.ok) {
        throw new Error(`Error cargando historial: ${response.status}`);
      }

      const data = await response.json();

      if (Array.isArray(data) && data.length > 0) {
        // Cargar historial
        setChatHistory(data);
        setChatId(chatName);

        // Actualizar contador de respuestas
        const assistantMessages = data.filter(msg => msg.role === 'assistant');
        setResponseNumber(assistantMessages.length);

        setConversationStarted(true);
        NotificationService.showNotification(`Historial ${chatName} cargado`, 'info');
      } else {
        throw new Error('Historial vacío o inválido');
      }
    } catch (error) {
      console.error('Error cargando historial:', error);
      NotificationService.showNotification('Error cargando historial', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const deleteHistory = async (chatName) => {
    try {
      const response = await fetch('/eliminar_historial', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ chatName })
      });

      if (!response.ok) {
        throw new Error(`Error eliminando historial: ${response.status}`);
      }

      // Actualizar lista de chats
      const updatedList = chatList.filter(name => name !== chatName);
      setChatList(updatedList);

      // Si el chat actual era el eliminado, crear uno nuevo
      if (chatId === chatName) {
        newChat();
      }

      NotificationService.showNotification(`Historial ${chatName} eliminado`, 'info');
    } catch (error) {
      console.error('Error eliminando historial:', error);
      NotificationService.showNotification('Error eliminando historial', 'error');
    }
  };

  const applyConfig = async (config) => {
    try {
      setIsLoading(true);

      // Enviar configuración al backend
      SocketService.emit('config', config);

      // Si hay una configuración de sistema, actualizar el mensaje en el historial
      if (config.system_message) {
        setChatHistory(prevHistory => {
          const newHistory = [...prevHistory];
          // Actualizar mensaje del sistema
          newHistory[0] = {
            role: 'system',
            content: config.system_message
          };
          return newHistory;
        });
      }

      NotificationService.showNotification('Configuración aplicada', 'success');
      // Cerrar sidebar de configuración en móviles
      if (window.innerWidth < 768) {
        setIsConfigSidebarOpen(false);
      }
    } catch (error) {
      console.error('Error aplicando configuración:', error);
      NotificationService.showNotification('Error aplicando configuración', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const unloadModel = async () => {
    try {
      setIsLoading(true);

      // Enviar comando para descargar modelo
      SocketService.emit('unload_model', {});

      NotificationService.showNotification('Modelo descargado', 'info');
    } catch (error) {
      console.error('Error descargando modelo:', error);
      NotificationService.showNotification('Error descargando modelo', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleChatSidebar = () => {
    setIsChatSidebarOpen(!isChatSidebarOpen);
    if (!isChatSidebarOpen && isConfigSidebarOpen) {
      setIsConfigSidebarOpen(false);
    }
  };

  const toggleConfigSidebar = () => {
    setIsConfigSidebarOpen(!isConfigSidebarOpen);
    if (!isConfigSidebarOpen && isChatSidebarOpen) {
      setIsChatSidebarOpen(false);
    }
  };

  const toggleHelpModal = () => {
    setShowHelpModal(!showHelpModal);
  };

  return (
    <div className="app">
      {isLoading && <div className="loading-overlay"><div className="spinner"></div></div>}

      <ChatSidebar 
        newChat={newChat} 
        loadHistory={loadHistory} 
        deleteHistory={deleteHistory} 
        chatList={chatList} 
        isOpen={isChatSidebarOpen}
      />

      <MainContainer 
        chatHistory={chatHistory}
        currentResponse={currentResponse}
        totalTokens={totalTokens}
        tools={tools}
        setTools={setTools}
        rag={rag}
        setRag={setRag}
        sendMessage={sendMessage}
        stopResponse={stopResponse}
        toggleChatSidebar={toggleChatSidebar}
        toggleConfigSidebar={toggleConfigSidebar}
        toggleHelpModal={toggleHelpModal}
        isLoading={isLoading}
        responseNumber={responseNumber}
      />

      <ConfigSidebar 
        applyConfig={applyConfig}
        unloadModel={unloadModel}
        modelsList={modelsList}
        formatList={formatList}
        isOpen={isConfigSidebarOpen}
      />

      {showHelpModal && <HelpModal onClose={toggleHelpModal} />}
    </div>
  );
}

export default App;
