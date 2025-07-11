import React, { useEffect } from 'react';
import { useChatContext } from '../../hooks/useChatContext';
import { Trash } from 'lucide-react';
import './ChatSidebar.css';
import { useLanguage } from '../../context/LanguageContext';

function ChatSidebar({ visible, onLoadChat, onDeleteChat, onClose }) {
  const { chatList, fetchChatList } = useChatContext();
  const { getStrings } = useLanguage();
  const strings = getStrings('chatSidebar');

  useEffect(() => {
    if (visible) {
      fetchChatList();
    }
  }, [visible, fetchChatList]);

  if (!visible) return null;

  return (
    <div className={`chat-sidebar ${visible ? 'visible' : ''}`}>
      <div className="chat-list">
        {Array.isArray(chatList) && chatList.length > 0 ? (
          chatList.map((chatName, idx) => {
            // Filtrar la fecha y hora del nombre (formato ISO y guion)
            const match = chatName.match(/^(\d{4}-\d{2}-\d{2}T\d{2}\.\d{2}\.\d{2}\.\d{3}Z)-?(.*)$/);
            let displayName = chatName;
            if (match) {
              displayName = match[2].trim();
              // Si no hay nombre, mostrar la fecha/hora formateada
              if (!displayName) {
                const date = new Date(match[1].replace(/\./g, ':').replace('T', ' ').replace('Z', ''));
                if (!isNaN(date.getTime())) {
                  displayName = date.toLocaleString();
                } else {
                  displayName = match[1];
                }
              }
            }
            // Reemplazar guiones bajos por espacios en el displayName
            displayName = displayName.replace(/_/g, ' ');
            return (
              <div key={idx} className="chat-item">
                <button
                  onClick={() => onDeleteChat(chatName)}
                  className="delete-chat-btn"
                  title={strings.deleteTitle}
                >
                  <Trash size={18} />
                </button>
                <button
                  onClick={() => onLoadChat(chatName)}
                  className="chat-name-btn"
                  title={strings.loadTitle.replace('{chatName}', chatName)}
                >
                  {displayName}
                </button>
              </div>
            );
          })
        ) : (
          <div
            style={{
              textAlign: 'center',
              color: 'var(--text-secondary)',
              padding: '2rem',
              fontStyle: 'italic',
            }}
          >
            {strings.empty}
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatSidebar;
