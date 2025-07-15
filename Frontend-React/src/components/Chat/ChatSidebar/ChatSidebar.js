import React, { useState, useEffect, useMemo } from 'react';
import { 
  Search, 
  Star, 
  MessageCircle, 
  Trash2, 
  Edit3,
  CheckSquare,
  Square,
  X,
  Clock
} from 'lucide-react';
import { useChatContext } from '../../../hooks/useChatContext';
import { useLanguage } from '../../../context/LanguageContext';
import './ChatSidebar.css';

const ChatSidebar = ({ visible, onLoadChat, onDeleteChat, onClose }) => {
  const { chatList, fetchChatList } = useChatContext();
  const { getStrings } = useLanguage();
  const strings = getStrings('chatSidebar');

  const [searchTerm, setSearchTerm] = useState('');
  const [selectMode, setSelectMode] = useState(false);
  const [selectedChats, setSelectedChats] = useState(new Set());
  const [favoriteChats, setFavoriteChats] = useState(new Set());
  const [hoveredChat, setHoveredChat] = useState(null);
  const [editingChat, setEditingChat] = useState(null);
  const [editingName, setEditingName] = useState('');
  const [allChats, setAllChats] = useState([]);

  // Función para convertir chatList del backend a formato unificado
  const convertBackendChats = (backendChatList) => {
    if (!Array.isArray(backendChatList)) return [];
    
    return backendChatList
      .filter(chatName => chatName && chatName.trim() !== '')
      .map(chatName => {
        // Extraer fecha del nombre si existe
        const match = chatName.match(/^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}\.[0-9]{2}\.[0-9]{2}\.[0-9]{3}Z)-?(.*)$/);
        let displayName = chatName;
        let timestamp = new Date();
        
        if (match) {
          displayName = match[2].trim();
          if (!displayName) {
            const date = new Date(match[1].replace(/\./g, ':').replace('T', ' ').replace('Z', ''));
            displayName = !isNaN(date.getTime()) ? date.toLocaleString() : match[1];
            timestamp = date;
          } else {
            timestamp = new Date(match[1].replace(/\./g, ':').replace('T', ' ').replace('Z', ''));
          }
        }
        
        displayName = displayName.replace(/_/g, ' ');
        
        return {
          id: chatName,
          name: displayName,
          messages: [],
          timestamp: timestamp,
          lastMessage: 'Chat del backend',
          messageCount: 0,
          isFromBackend: true
        };
      });
  };

  // Cargar historial de chats desde localStorage
  const loadLocalStorageChats = () => {
    const histories = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('chat_')) {
        const chatName = key.replace('chat_', '');
        try {
          const chatData = JSON.parse(localStorage.getItem(key));
          const lastMessage = chatData.messages && chatData.messages.length > 0 
            ? chatData.messages[chatData.messages.length - 1].content?.substring(0, 50) + '...' 
            : 'Chat vacío';
          
          histories.push({
            id: chatName,
            name: chatName,
            messages: chatData.messages || [],
            timestamp: new Date(chatData.timestamp || Date.now()),
            lastMessage: lastMessage,
            messageCount: chatData.messages ? chatData.messages.length : 0,
            isFromBackend: false
          });
        } catch (error) {
          console.error('Error parsing chat data:', error);
        }
      }
    }
    return histories;
  };

  // Unificar chats de ambas fuentes
  const unifyChats = () => {
    const localChats = loadLocalStorageChats();
    const backendChats = convertBackendChats(chatList);
    
    // Combinar ambas listas, evitando duplicados por ID
    const chatMap = new Map();
    
    // Primero agregar chats locales
    localChats.forEach(chat => {
      chatMap.set(chat.id, chat);
    });
    
    // Luego agregar chats del backend (solo si no existen localmente)
    backendChats.forEach(chat => {
      if (!chatMap.has(chat.id)) {
        chatMap.set(chat.id, chat);
      }
    });
    
    // Convertir a array y ordenar por timestamp
    const unified = Array.from(chatMap.values());
    unified.sort((a, b) => b.timestamp - a.timestamp);
    
    setAllChats(unified);
  };

  useEffect(() => {
    if (visible) {
      fetchChatList();
    }
  }, [visible, fetchChatList]);

  // Unificar chats cuando cambie la lista del backend o se monte el componente
  useEffect(() => {
    if (visible) {
      unifyChats();
    }
  }, [visible, chatList]);

  // Cargar favoritos desde localStorage
  useEffect(() => {
    const savedFavorites = localStorage.getItem('favoriteChats');
    if (savedFavorites) {
      try {
        setFavoriteChats(new Set(JSON.parse(savedFavorites)));
      } catch (error) {
        console.error('Error loading favorites:', error);
      }
    }
  }, []);

  // Guardar favoritos en localStorage
  useEffect(() => {
    localStorage.setItem('favoriteChats', JSON.stringify([...favoriteChats]));
  }, [favoriteChats]);

  // Filtrar chats basado en término de búsqueda
  const filteredChats = useMemo(() => {
    if (!searchTerm.trim()) return allChats;
    
    return allChats.filter(chat => 
      chat.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      chat.lastMessage.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [allChats, searchTerm]);

  // Separar favoritos y chats regulares
  const favoritesList = useMemo(() => {
    return filteredChats.filter(chat => favoriteChats.has(chat.id));
  }, [filteredChats, favoriteChats]);

  const regularChats = useMemo(() => {
    return filteredChats.filter(chat => !favoriteChats.has(chat.id));
  }, [filteredChats, favoriteChats]);

  // Agrupar chats por fecha
  const groupChatsByDate = (chats) => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

    const groups = {
      today: [],
      yesterday: [],
      thisWeek: [],
      thisMonth: [],
      older: []
    };

    chats.forEach(chat => {
      const chatDate = new Date(chat.timestamp);
      if (chatDate >= today) {
        groups.today.push(chat);
      } else if (chatDate >= yesterday) {
        groups.yesterday.push(chat);
      } else if (chatDate >= weekAgo) {
        groups.thisWeek.push(chat);
      } else if (chatDate >= monthAgo) {
        groups.thisMonth.push(chat);
      } else {
        groups.older.push(chat);
      }
    });

    return groups;
  };

  const groupedChats = useMemo(() => groupChatsByDate(regularChats), [regularChats]);

  const formatTime = (date) => {
    return date.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const toggleFavorite = (chatId) => {
    setFavoriteChats(prev => {
      const newSet = new Set(prev);
      if (newSet.has(chatId)) {
        newSet.delete(chatId);
      } else {
        newSet.add(chatId);
      }
      return newSet;
    });
  };

  const toggleSelectMode = () => {
    setSelectMode(!selectMode);
    setSelectedChats(new Set());
  };

  const toggleSelectChat = (chatId) => {
    setSelectedChats(prev => {
      const newSet = new Set(prev);
      if (newSet.has(chatId)) {
        newSet.delete(chatId);
      } else {
        newSet.add(chatId);
      }
      return newSet;
    });
  };

  const selectAllChats = () => {
    if (selectedChats.size === filteredChats.length) {
      setSelectedChats(new Set());
    } else {
      setSelectedChats(new Set(filteredChats.map(chat => chat.id)));
    }
  };

  const deleteSelectedChats = () => {
    if (selectedChats.size > 0) {
      const confirmed = window.confirm(`¿Eliminar ${selectedChats.size} chat${selectedChats.size > 1 ? 's' : ''}?`);
      if (confirmed) {
        selectedChats.forEach(chatId => {
          onDeleteChat(chatId);
        });
        setSelectedChats(new Set());
        setSelectMode(false);
        // Recargar historial después de eliminar
        setTimeout(() => {
          unifyChats();
        }, 100);
      }
    }
  };

  const startEditing = (chat) => {
    setEditingChat(chat.id);
    setEditingName(chat.name);
  };

  const saveEditedName = (chatId) => {
    if (editingName.trim() && editingName !== chatId) {
      setAllChats(prev => prev.map(chat => 
        chat.id === chatId ? { ...chat, name: editingName.trim() } : chat
      ));
    }
    setEditingChat(null);
    setEditingName('');
  };

  const cancelEditing = () => {
    setEditingChat(null);
    setEditingName('');
  };

  const ChatItem = ({ chat, isFavorite = false }) => {
    const isSelected = selectedChats.has(chat.id);
    const isHovered = hoveredChat === chat.id;
    const isEditing = editingChat === chat.id;

    return (
      <div
        className={`chat-item ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''}`}
        onMouseEnter={() => setHoveredChat(chat.id)}
        onMouseLeave={() => setHoveredChat(null)}
        style={{
          padding: '12px 16px',
          borderRadius: '8px',
          margin: '2px 8px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '12px',
          backgroundColor: isSelected ? '#3b82f6' : (isHovered ? '#f8fafc' : 'transparent'),
          color: isSelected ? 'white' : '#1f2937',
          transition: 'all 0.2s ease',
          position: 'relative',
          border: isSelected ? '1px solid #3b82f6' : '1px solid transparent'
        }}
      >
        {selectMode && (
          <div
            onClick={(e) => {
              e.stopPropagation();
              toggleSelectChat(chat.id);
            }}
            style={{ flexShrink: 0, marginTop: '2px' }}
          >
            {isSelected ? (
              <CheckSquare size={18} color={isSelected ? 'white' : '#3b82f6'} />
            ) : (
              <Square size={18} color="#6b7280" />
            )}
          </div>
        )}

        <div
          style={{
            flex: 1,
            minWidth: 0,
            display: 'flex',
            flexDirection: 'column',
            gap: '4px'
          }}
          onClick={() => !selectMode && !isEditing && onLoadChat(chat.id)}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <MessageCircle size={16} style={{ flexShrink: 0, opacity: 0.7 }} />
            
            {isEditing ? (
              <input
                type="text"
                value={editingName}
                onChange={(e) => setEditingName(e.target.value)}
                onBlur={() => saveEditedName(chat.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') saveEditedName(chat.id);
                  if (e.key === 'Escape') cancelEditing();
                }}
                onClick={(e) => e.stopPropagation()}
                style={{
                  flex: 1,
                  background: 'white',
                  border: '2px solid #3b82f6',
                  borderRadius: '4px',
                  padding: '4px 8px',
                  fontSize: '14px',
                  color: '#1f2937'
                }}
                autoFocus
              />
            ) : (
              <span
                style={{
                  flex: 1,
                  fontWeight: '500',
                  fontSize: '14px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}
              >
                {chat.name}
              </span>
            )}

            {isFavorite && (
              <Star
                size={14}
                fill="#fbbf24"
                color="#fbbf24"
                style={{ flexShrink: 0 }}
              />
            )}

            {/* Indicador de origen */}
            {chat.isFromBackend && (
              <div
                style={{
                  background: '#10b981',
                  color: 'white',
                  fontSize: '10px',
                  padding: '2px 6px',
                  borderRadius: '10px',
                  fontWeight: '500'
                }}
                title="Chat del backend"
              >
                API
              </div>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', opacity: 0.7 }}>
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {chat.lastMessage}
            </span>
            <span style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Clock size={12} />
              {formatTime(chat.timestamp)}
            </span>
          </div>
        </div>

        {!selectMode && isHovered && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleFavorite(chat.id);
              }}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '4px',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: favoriteChats.has(chat.id) ? '#fbbf24' : '#6b7280'
              }}
              title={favoriteChats.has(chat.id) ? 'Quitar de favoritos' : 'Marcar como favorito'}
            >
              <Star size={16} fill={favoriteChats.has(chat.id) ? '#fbbf24' : 'none'} />
            </button>
            
            <button
              onClick={(e) => {
                e.stopPropagation();
                startEditing(chat);
              }}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '4px',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#6b7280'
              }}
              title="Editar nombre"
            >
              <Edit3 size={16} />
            </button>
            
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDeleteChat(chat.id);
                setTimeout(() => unifyChats(), 100);
              }}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '4px',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ef4444'
              }}
              title="Eliminar chat"
            >
              <Trash2 size={16} />
            </button>
          </div>
        )}
      </div>
    );
  };

  const SectionHeader = ({ title, count }) => (
    <div style={{
      padding: '8px 16px 4px',
      fontSize: '12px',
      fontWeight: '600',
      color: '#6b7280',
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px'
    }}>
      <span>{title}</span>
      <span style={{
        background: '#e5e7eb',
        color: '#6b7280',
        padding: '2px 6px',
        borderRadius: '10px',
        fontSize: '10px',
        fontWeight: '500'
      }}>
        {count}
      </span>
    </div>
  );

  // Render principal
  if (!visible) return null;

  return (
    <div className="chat-sidebar">
      {/* Header */}
      <div className="chat-sidebar-header">
        <h2 className="chat-sidebar-title">
          Conversaciones ({allChats.length})
        </h2>
        <button
          onClick={onClose}
          className="close-chat-sidebar-btn"
        >
          <X size={20} />
        </button>
      </div>
      {/* Barra de búsqueda */}
      <div className="chat-sidebar-search">
        <Search size={18} className="chat-sidebar-search-icon" />
        <input
          type="text"
          placeholder="Buscar conversaciones..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="chat-sidebar-search-input"
        />
      </div>
      {/* Controles de selección */}
      <div className="chat-sidebar-controls">
        <button
          onClick={toggleSelectMode}
          className="chat-sidebar-controls-btn"
        >
          {selectMode ? 'Cancelar' : 'Seleccionar'}
        </button>
        {selectMode && (
          <>
            <button
              onClick={selectAllChats}
              className="chat-sidebar-controls-btn"
            >
              {selectedChats.size === filteredChats.length ? 'Deseleccionar' : 'Seleccionar'} todos
            </button>
            {selectedChats.size > 0 && (
              <button
                onClick={deleteSelectedChats}
                className="chat-sidebar-controls-btn"
                style={{ background: '#ef4444', color: 'white' }}
              >
                <Trash2 size={12} />
                Eliminar ({selectedChats.size})
              </button>
            )}
          </>
        )}
      </div>
      {/* Lista de chats */}
      <div className="conversations-list">
        {/* Favoritos */}
        {favoritesList.length > 0 && (
          <div className="chat-group">
            <SectionHeader title="Favoritos" count={favoritesList.length} />
            <div className="chat-group-content">
              {favoritesList.map(chat => (
                <ChatItem key={chat.id} chat={chat} isFavorite={true} />
              ))}
            </div>
          </div>
        )}

        {/* Chats agrupados por fecha */}
        {groupedChats.today.length > 0 && (
          <div className="chat-group">
            <SectionHeader title="Hoy" count={groupedChats.today.length} />
            <div className="chat-group-content">
              {groupedChats.today.map(chat => (
                <ChatItem key={chat.id} chat={chat} />
              ))}
            </div>
          </div>
        )}

        {groupedChats.yesterday.length > 0 && (
          <div className="chat-group">
            <SectionHeader title="Ayer" count={groupedChats.yesterday.length} />
            <div className="chat-group-content">
              {groupedChats.yesterday.map(chat => (
                <ChatItem key={chat.id} chat={chat} />
              ))}
            </div>
          </div>
        )}

        {groupedChats.thisWeek.length > 0 && (
          <div className="chat-group">
            <SectionHeader title="Esta semana" count={groupedChats.thisWeek.length} />
            <div className="chat-group-content">
              {groupedChats.thisWeek.map(chat => (
                <ChatItem key={chat.id} chat={chat} />
              ))}
            </div>
          </div>
        )}

        {groupedChats.thisMonth.length > 0 && (
          <div className="chat-group">
            <SectionHeader title="Este mes" count={groupedChats.thisMonth.length} />
            <div className="chat-group-content">
              {groupedChats.thisMonth.map(chat => (
                <ChatItem key={chat.id} chat={chat} />
              ))}
            </div>
          </div>
        )}

        {groupedChats.older.length > 0 && (
          <div className="chat-group">
            <SectionHeader title="Más antiguos" count={groupedChats.older.length} />
            <div className="chat-group-content">
              {groupedChats.older.map(chat => (
                <ChatItem key={chat.id} chat={chat} />
              ))}
            </div>
          </div>
        )}

        {filteredChats.length === 0 && (
          <div style={{
            padding: '32px 16px',
            textAlign: 'center',
            color: '#6b7280'
          }}>
            <MessageCircle size={48} style={{ opacity: 0.3, margin: '0 auto 16px' }} />
            <p style={{ margin: 0, fontSize: '14px' }}>
              {searchTerm ? 'No se encontraron conversaciones' : 'No hay conversaciones guardadas'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatSidebar;