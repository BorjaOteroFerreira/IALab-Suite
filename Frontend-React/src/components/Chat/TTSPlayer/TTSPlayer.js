import React, { useState, useRef } from "react";
import { Volume2, VolumeX, SkipBack, SkipForward } from "lucide-react";
import './TTSPlayer.css';
import cleanTextForTTS from '../../../hooks/useTTS';

function splitTextToSentences(text) {
  // Divide el texto en frases usando puntos, signos de exclamación/interrogación
  return text.match(/[^.!?]+[.!?]?/g) || [];
}

export default function TTSPlayer({ text, enabled = true, voiceName = "Microsoft Pablo - Spanish (Spain)" }) {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const sentences = splitTextToSentences(text);
  const utteranceRef = useRef(null);

  const playSentence = idx => {
    if (!sentences[idx]) return;
    window.speechSynthesis.cancel();
    // Limpia el texto antes de reproducir
    const cleaned = cleanTextForTTS(sentences[idx]);
    if (!cleaned) return;
    // Espera a que las voces estén cargadas antes de crear el utterance
    const synth = window.speechSynthesis;
    const speak = () => {
      const voices = synth.getVoices();
      const utter = new window.SpeechSynthesisUtterance(cleaned);
      const preferred = voices.find(v => v.name === voiceName);
      utter.voice = preferred || voices.find(v => v.name.includes("Microsoft") && v.lang.startsWith("es"));
      utter.onend = () => {
        if (idx < sentences.length - 1 && isPlaying) {
          setCurrentIdx(idx + 1);
          playSentence(idx + 1);
        } else {
          setIsPlaying(false);
        }
      };
      utteranceRef.current = utter;
      synth.speak(utter);
    };
    if (synth.getVoices().length === 0) {
      synth.onvoiceschanged = speak;
    } else {
      speak();
    }
  };

  const handlePlay = () => {
    setIsPlaying(true);
    playSentence(currentIdx);
  };

  const handlePause = () => {
    setIsPlaying(false);
    window.speechSynthesis.cancel();
  };

  const handleSkip = dir => {
    let newIdx = currentIdx + dir;
    if (newIdx < 0) newIdx = 0;
    if (newIdx >= sentences.length) newIdx = sentences.length - 1;
    setCurrentIdx(newIdx);
    if (isPlaying) playSentence(newIdx);
  };

  const handleSliderChange = (value) => {
    setCurrentIdx(value);
    if (isPlaying) {
      playSentence(value);
    } else {
      window.speechSynthesis.cancel();
    }
  };

  React.useEffect(() => {
    if (!enabled && isPlaying) handlePause();
  }, [enabled]);

  React.useEffect(() => {
    setCurrentIdx(0);
  }, [text]);

  // Sincroniza la bolita con el audio usando boundary
  React.useEffect(() => {
    let utter = utteranceRef.current;
    if (!utter) return;
    utter.onboundary = (event) => {
      if (isPlaying && event.charIndex === 0) {
        setCurrentIdx(prev => prev + 1);
      }
    };
    utter.onend = () => {
      setIsPlaying(false);
    };
    return () => {
      if (utter) {
        utter.onboundary = null;
        utter.onend = null;
      }
    };
  }, [isPlaying, currentIdx, sentences.length]);

  return (
    <div className="tts-player">
      <button onClick={isPlaying ? handlePause : handlePlay} className="tts-btn">
        {!isPlaying ? <VolumeX size={22}/> : <Volume2 size={22}/>}
      </button>
      <button onClick={() => handleSkip(-1)} className="tts-btn"><SkipBack size={18}/></button>
      <div className="tts-progress">
        <input
          type="range"
          min={0}
          max={sentences.length - 1}
          value={currentIdx}
          onChange={e => handleSliderChange(Number(e.target.value))}
        />
        <span>{currentIdx + 1} de {sentences.length}</span>
      </div>
      <button onClick={() => handleSkip(1)} className="tts-btn"><SkipForward size={18}/></button>
    </div>
  );
}
