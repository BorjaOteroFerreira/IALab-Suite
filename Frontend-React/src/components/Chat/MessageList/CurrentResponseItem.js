import React from 'react';
import TTSPlayer from '../TTSPlayer/TTSPlayer';
import { Volume2 } from 'lucide-react';

function CurrentResponseItem({ currentResponse, ttsOpen, toggleTTS, ttsEnabled, renderMarkdown, messagesLength }) {
  return (
    <div className="message assistant">
      <div className="message-avatar">🤖</div>
      <div className="message-content">
        {renderMarkdown(currentResponse, messagesLength)}
        <button
          className="tts-toggle-btn"
          onClick={() => toggleTTS('current')}
          style={{ marginTop: 8, background: 'transparent', boxShadow: 'none', border: 'none', padding: 0 }}
          title={ttsOpen['current'] ? 'Ocultar audio' : 'Escuchar mensaje'}
        >
          <Volume2 size={22} color="rgba(180,180,180,0.55)" />
        </button>
        {ttsOpen['current'] && (
          <TTSPlayer text={currentResponse} enabled={ttsEnabled} />
        )}
      </div>
    </div>
  );
}

export default CurrentResponseItem;
