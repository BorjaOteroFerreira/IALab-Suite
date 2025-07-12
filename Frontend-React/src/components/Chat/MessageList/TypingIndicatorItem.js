import React from 'react';

function TypingIndicatorItem() {
  return (
    <div className="message assistant">
      <div className="message-avatar">🤖</div>
      <div className="message-content">
        <div className="typing-indicator"><span/><span/><span/></div>
      </div>
    </div>
  );
}

export default TypingIndicatorItem;
