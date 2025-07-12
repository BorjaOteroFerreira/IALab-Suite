import React from 'react';
import TTSPlayer from '../TTSPlayer/TTSPlayer';

function CurrentResponseItem({ currentResponse, ttsOpen, toggleTTS, ttsEnabled, renderMarkdown, messagesLength }) {
  return (
    <div className="message assistant">
      <div className="message-avatar">🤖</div>
      <div className="message-content">
        {renderMarkdown(currentResponse, messagesLength)}
        <button
          className="tts-toggle-btn"
          onClick={() => toggleTTS('current')}
          style={{ marginTop: 8 }}
        >
          {ttsOpen['current'] ? 'Ocultar audio' : 'Escuchar mensaje'}
        </button>
        {ttsOpen['current'] && (
          <TTSPlayer text={currentResponse} enabled={ttsEnabled} />
        )}
      </div>
    </div>
  );
}

export default CurrentResponseItem;
