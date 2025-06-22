import React from 'react';
import ReactMarkdown from 'react-markdown';
import CodeBlock from '../CodeBlock/CodeBlock';
import { LinkRenderer } from '../YoutubeRender/YouTubeRenderer';

function MessageList({ messages, currentResponse, isLoading, messagesEndRef }) {
  const renderMarkdown = (content) => (
    <ReactMarkdown 
      className="assistant-message"
      components={{
        code({node, inline, className, children, ...props}) {
          const match = /language-(\w+)/.exec(className || '');
          const language = match ? match[1] : '';
          
          return !inline ? (
            <CodeBlock language={language}>
              {String(children).replace(/\n$/, '')}
            </CodeBlock>
          ) : (
            <code className="inline-code" {...props}>
              {children}
            </code>
          );
        },
        a: LinkRenderer
      }}
    >
      {content}
    </ReactMarkdown>
  );

  return (
    <div className="messages-container">
      <div className="messages-list">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h2>¡Bienvenido a AI Lab Suite! 🚀</h2>
            <p>Escribe un mensaje para comenzar la conversación.</p>
          </div>
        ) : (
          messages.map((message, idx) => (
            <div key={idx} className={`message ${message.role}`}>
              <div className="message-avatar">
                {message.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className="message-content">
                {message.role === 'user' ? (
                  <div className="user-message">{message.content}</div>
                ) : (
                  renderMarkdown(message.content)
                )}
              </div>
            </div>
          ))
        )}

        {currentResponse && (
          <div className="message assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <ReactMarkdown 
                className="assistant-message streaming"
                components={{
                  code({node, inline, className, children, ...props}) {
                    const match = /language-(\w+)/.exec(className || '');
                    const language = match ? match[1] : '';
                    
                    return !inline ? (
                      <CodeBlock language={language}>
                        {String(children).replace(/\n$/, '')}
                      </CodeBlock>
                    ) : (
                      <code className="inline-code" {...props}>
                        {children}
                      </code>
                    );
                  },
                  a: LinkRenderer
                }}
              >
                {currentResponse}
              </ReactMarkdown>
            </div>
          </div>
        )}
        
        {isLoading && !currentResponse && (
          <div className="message assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}

export default MessageList;
