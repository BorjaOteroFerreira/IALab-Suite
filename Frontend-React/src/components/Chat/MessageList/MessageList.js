import React, { useEffect, useRef } from 'react';
import { useMessageList } from '../../../hooks/useMessageList';
import MessageItem from './MessageItem';
import ShortcutsLegend from './ShortcutsLegend';
import CurrentResponseItem from './CurrentResponseItem';
import TypingIndicatorItem from './TypingIndicatorItem';
import './MessageList.css';

function MessageList({ messages, currentResponse, isLoading, messagesEndRef, ttsEnabled }) {
  const {
    lang,
    general,
    ttsOpen,
    toggleTTS,
    renderMarkdown
  } = useMessageList(messages, currentResponse, messagesEndRef, ttsEnabled);

  // Autoscroll independiente para MessageList
  const prevMessagesCount = useRef(messages.length);
  useEffect(() => {
    if (messagesEndRef?.current && messages.length > prevMessagesCount.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
    prevMessagesCount.current = messages.length;
  }, [messages, messagesEndRef]);

  return (
    <div className="messages-container">
      {messages.length === 0 && (
        <div className="floating-messages">
          <div className="welcome-message">
            <h2>{general.welcome}</h2>
            <p className="welcome-message-p">{general.welcomeSubtitle}</p>
          </div>
          <ShortcutsLegend floating={true} />
        </div>
      )}
      <div className="messages-list">
        {messages.length === 0 ? null : (
          messages.map((m, i) => (
            <MessageItem
              key={i}
              message={m}
              idx={i}
              ttsOpen={ttsOpen}
              toggleTTS={toggleTTS}
              ttsEnabled={ttsEnabled}
              renderMarkdown={renderMarkdown}
            />
          ))
        )}
        {currentResponse && (
          <CurrentResponseItem
            currentResponse={currentResponse}
            ttsOpen={ttsOpen}
            toggleTTS={toggleTTS}
            ttsEnabled={ttsEnabled}
            renderMarkdown={renderMarkdown}
            messagesLength={messages.length}
          />
        )}
        {isLoading && !currentResponse && (
          <TypingIndicatorItem />
        )}
        <div ref={messagesEndRef}/>
      </div>
    </div>
  );
}

export default MessageList;