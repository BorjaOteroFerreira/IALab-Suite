import React from 'react';
import TTSPlayer from '../TTSPlayer/TTSPlayer';
import { Volume2 } from 'lucide-react';

function AssistantMessageContent({ content, idx, ttsOpen, toggleTTS, ttsEnabled, renderMarkdown }) {
  return (
    <>
      {renderMarkdown(content, idx)}
      <button
        className="tts-toggle-btn"
        onClick={() => toggleTTS(idx)}
        style={{ marginTop: 8, background: 'transparent', boxShadow: 'none', border: 'none', padding: 0 }}
        title={ttsOpen[idx] ? 'Ocultar audio' : 'Escuchar mensaje'}
      >
        <Volume2 size={22} color="rgba(180,180,180,0.55)" />
      </button>
      {ttsOpen[idx] && (
        <TTSPlayer text={content} enabled={ttsEnabled} />
      )}
    </>
  );
}

export default AssistantMessageContent;
