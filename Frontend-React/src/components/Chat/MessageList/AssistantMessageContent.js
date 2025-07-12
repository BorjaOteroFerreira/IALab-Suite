import React from 'react';
import TTSPlayer from '../TTSPlayer/TTSPlayer';

function AssistantMessageContent({ content, idx, ttsOpen, toggleTTS, ttsEnabled, renderMarkdown }) {
  return (
    <>
      {renderMarkdown(content, idx)}
      <button
        className="tts-toggle-btn"
        onClick={() => toggleTTS(idx)}
        style={{ marginTop: 8 }}
      >
        {ttsOpen[idx] ? 'Ocultar audio' : 'Escuchar mensaje'}
      </button>
      {ttsOpen[idx] && (
        <TTSPlayer text={content} enabled={ttsEnabled} />
      )}
    </>
  );
}

export default AssistantMessageContent;
