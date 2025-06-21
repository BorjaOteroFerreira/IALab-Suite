import React from 'react';
import './ChatSidebar.css';

function ChatSidebar({ newChat, loadHistory, deleteHistory, chatList, isOpen }) {
  return (
    <div id="chat-sidebar" className={isOpen ? 'open' : ''}>
      <div id="header-chat-menu">
        <h5>Conversaciones</h5>
        <button className="btn btn-primary" id="new-chat-button" onClick={newChat}>
          Nueva conversación 🧠
        </button>
      </div>
      
      <div id="conversations-list">
        {chatList && chatList.length > 0 ? (
          chatList.map((chatName) => (
            <div className='chat-history-item' key={chatName} id={chatName}>
              <button 
                className="delete-history-btn" 
                onClick={() => deleteHistory(chatName)}>❌</button>
              <button 
                className="load-history-btn"  
                onClick={() => loadHistory(chatName)}>
                {chatName}
              </button>
            </div>
          ))
        ) : (
          <div className="empty-list-message">No hay conversaciones guardadas</div>
        )}
      </div>
    </div>
  );
}

export default ChatSidebar;
