import React from 'react';
import AssistantMessageContent from './AssistantMessageContent';
import UserMessageContent from './UserMessageContent';

function MessageItem({ message, idx, ttsOpen, toggleTTS, ttsEnabled, renderMarkdown }) {
  return (
    <div className={`message ${message.role}`}>
      <div className="message-content">
        {message.role === 'user' ? (
          <UserMessageContent content={message.content} />
        ) : (
          <AssistantMessageContent
            content={message.content}
            idx={idx}
            ttsOpen={ttsOpen}
            toggleTTS={toggleTTS}
            ttsEnabled={ttsEnabled}
            renderMarkdown={renderMarkdown}
          />
        )}
      </div>
    </div>
  );
}

export default MessageItem;
