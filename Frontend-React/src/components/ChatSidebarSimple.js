import React from 'react';
import './ChatSidebar.css';

function ChatSidebar({ visible }) {
  if (!visible) return null;
  
  return (
    <div className="chat-sidebar">
      <div className="sidebar-header">
        <h3>Historial de Chat</h3>
      </div>
      
      <div className="chat-list">
        <div className="chat-item">
          <span>Chat 1</span>
        </div>
        <div className="chat-item">
          <span>Chat 2</span>
        </div>
        <div className="chat-item">
          <span>Chat 3</span>
        </div>
      </div>
    </div>
  );
}

export default ChatSidebar;
