import React from 'react';
import AssistantMessageContent from './AssistantMessageContent';
import UserMessageContent from './UserMessageContent';

function capitalizeFirstWord(text) {
  if (!text || typeof text !== 'string') return text;
  return text.replace(/^(\s*)(\w)(.*)/, (m, space, first, rest) => space + first.toUpperCase() + rest);
}

function MessageItem({ message, idx, ttsOpen, toggleTTS, ttsEnabled, renderMarkdown, showDivider }) {
  return (
    <>
      <div className={`message ${message.role}`}>
        <div className="message-content">
          {message.role === 'user' ? (
            <UserMessageContent content={capitalizeFirstWord(message.content)} />
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
      {showDivider && message.role === 'assistant' && <hr className="message-divider" />}
    </>
  );
}

export default MessageItem;
