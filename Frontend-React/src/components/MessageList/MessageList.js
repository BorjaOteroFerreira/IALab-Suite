import React, { useEffect, useRef, useState } from 'react';
import { LinkRenderer } from '../YoutubeRender/YouTubeRenderer';
import ImageRenderer from '../ImageRenderer/ImageRenderer';
import './MessageList.css';

// Utilidades de detección de enlaces
const isYoutubeLink = href => /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\//.test(href);
const isImageLink = href => /\.(jpg|jpeg|png|gif|webp|bmp|svg)([?#].*)?$/i.test(href);
const isImageLabel = text => /^\s*\[(imagen|image)\b.*\]/i.test(text.trim());

// Limpia enlaces markdown redundantes de YouTube
const cleanYoutubeMarkdown = md => md.replace(
  /\[([^\]]+)\]\((https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/[\w\-?&=;%#@/.]+)\)/gi,
  (match, text, url) => (text.trim() === url.trim() ? url : match)
);

// Procesa markdown con enlaces especiales
const splitMarkdownWithLinks = markdownInput => {
  let markdown = cleanYoutubeMarkdown(markdownInput || '');
  const patterns = {
    customImage: /^[\s\t]*([\-*+•‣◦●▪‧·])[\s\t]+(\[imagen[^\]]*\])\s*\[([^\]]+)\](?:\s*([^\n]*))?$/i,
    markdownImage: /^[\s\t]*([\-*+•‣◦●▪‧·])[\s\t]+(\[imagen[^\]]*\])\(([^)]+)\)(?:\s*([^\n]*))?$/i,
    singleMarkdownImage: /^\s*(\[imagen[^\]]*\])\(([^)]+)\)(?:\s*([^\n]*))?$/i,
    singleCustomImage: /^\s*(\[imagen[^\]]*\])\s*\[([^\]]+)\](?:\s*([^\n]*))?$/i,
    standardImage: /^\s*([\-*+]\s*)?!\[([^\]]*)\]\(([^)]+)\)\s*(.*)$/i,
    youtube: /(https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/[\w\-?&=;%#@/\.]+)/gi
  };

  const lines = markdown.split(/\r?\n/);
  const result = [];
  let buffer = [];
  let imageBlock = [];

  const flushBuffer = () => {
    if (buffer.length) {
      const text = buffer.join('\n');
      if (text.trim()) {
        // Procesar YouTube links en el texto acumulado
        processTextWithYoutube(text, result);
      }
      buffer = [];
    }
  };

  const flushImageBlock = () => {
    if (!imageBlock.length) return;
    const allImgs = imageBlock.every(l => patterns.customImage.test(l) || patterns.markdownImage.test(l));
    if (allImgs) {
      imageBlock.forEach(l => {
        const m = patterns.customImage.exec(l) || patterns.markdownImage.exec(l);
        if (m) {
          result.push({ type: 'image', value: m[3], text: m[2] });
          if (m[4]?.trim()) {
            processTextWithYoutube(m[4].trim(), result);
          }
        }
      });
    } else {
      processTextWithYoutube(imageBlock.join('\n'), result);
    }
    imageBlock = [];
  };

  const processTextWithYoutube = (text, resultArray) => {
    if (!text.trim()) return;
    
    const matches = [...text.matchAll(patterns.youtube)];
    if (!matches.length) {
      resultArray.push({ type: 'text', value: text });
      return;
    }

    let lastIndex = 0;
    matches.forEach(match => {
      // Agregar texto antes del enlace de YouTube
      if (match.index > lastIndex) {
        const beforeText = text.slice(lastIndex, match.index);
        if (beforeText.trim()) {
          resultArray.push({ type: 'text', value: beforeText });
        }
      }
      
      // Agregar el enlace de YouTube
      resultArray.push({ type: 'youtube', value: match[0], text: match[0] });
      lastIndex = match.index + match[0].length;
    });

    // Agregar texto después del último enlace de YouTube
    if (lastIndex < text.length) {
      const afterText = text.slice(lastIndex);
      if (afterText.trim()) {
        resultArray.push({ type: 'text', value: afterText });
      }
    }
  };

  const processLine = line => {
    let m = patterns.standardImage.exec(line);
    if (m && isImageLink(m[3])) {
      result.push({ type: 'image', value: m[3], text: m[2] });
      if (m[4]?.trim()) {
        processTextWithYoutube(m[4].trim(), result);
      }
      return true;
    }
    m = patterns.singleMarkdownImage.exec(line);
    if (m && isImageLabel(m[1]) && isImageLink(m[2])) {
      result.push({ type: 'image', value: m[2], text: m[1] });
      if (m[3]?.trim()) {
        processTextWithYoutube(m[3].trim(), result);
      }
      return true;
    }
    m = patterns.singleCustomImage.exec(line);
    if (m && isImageLabel(m[1])) {
      result.push({ type: 'image', value: m[2], text: m[1] });
      if (m[3]?.trim()) {
        processTextWithYoutube(m[3].trim(), result);
      }
      return true;
    }
    
    // Ya no procesamos YouTube aquí línea por línea
    return false;
  };

  for (let i = 0; i < lines.length; i++) {
    const raw = cleanYoutubeMarkdown(lines[i]);
    if (patterns.customImage.test(raw) || patterns.markdownImage.test(raw)) {
      flushBuffer();
      imageBlock.push(raw);
      const nxt = lines[i+1] || '';
      if (!patterns.customImage.test(nxt) && !patterns.markdownImage.test(nxt)) flushImageBlock();
    } else {
      flushImageBlock();
      if (!processLine(raw)) {
        buffer.push(raw);
      } else {
        flushBuffer();
      }
    }
  }

  flushBuffer();
  flushImageBlock();
  return result.filter(x => x.value != null);
};

function MessageList({ messages, currentResponse, isLoading, messagesEndRef }) {
  const [showdown, setShowdown] = useState(null);
  const [hljs, setHljs] = useState(null);
  const htmlRefs = useRef([]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      const [sd, hl] = await Promise.all([import('showdown'), import('highlight.js')]);
      if (mounted) {
        setShowdown(new sd.Converter({
          tables: true,
          simplifiedAutoLink: true,
          openLinksInNewWindow: true,
          strikethrough: true,
          emoji: true,
          tasklists: true,
          ghCodeBlocks: true,
          noHeaderId: true,
          excludeTrailingPunctuationFromURLs: true,
          parseImgDimensions: true,
          headerLevelStart: 1
        }));
        setHljs(hl.default || hl);
      }
    })();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (hljs) htmlRefs.current.forEach(r => r?.querySelectorAll('pre code').forEach(c => hljs.highlightElement(c)));
  }, [messages, currentResponse, hljs]);

  const renderMarkdown = (text, idx) => {
    if (!showdown) return <div className="assistant-message">Cargando...</div>;
    const parts = splitMarkdownWithLinks(text || '');
    const blockRe = /<(h[1-6]|p|ul|ol|li|blockquote|table|pre)/i;

    return (
      <div className="assistant-message" ref={el => htmlRefs.current[idx] = el}>
        {parts.map((part, i) => {
          if (part.type === 'image') return <ImageRenderer key={i} src={part.value} alt={part.text} href={part.value}/>;
          if (part.type === 'youtube') return <LinkRenderer key={i} href={part.value}>{part.text}</LinkRenderer>;
          if (part.type === 'link') return <a key={i} href={part.value} target="_blank" rel="noopener noreferrer">{part.text}</a>;
          if (part.type === 'text') {
            const v = part.value;
            if (!v.trim() && v !== '\n') return null;
            const html = showdown.makeHtml(v);
            const isList = /^\s*[\*\-\+]\s+/.test(v);
            const Tag = isList || blockRe.test(html.trim()) ? 'div' : 'span';
            return <Tag key={i} className="assistant-md-fragment" dangerouslySetInnerHTML={{ __html: html }} />;
          }
          return null;
        })}
      </div>
    );
  };

  return (
    <div className="messages-container">
      <div className="messages-list">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h2>¡Bienvenido a AI Lab Suite!</h2>
            <p className="welcome-message-p">Escribe un mensaje para comenzar la conversación.</p>
          </div>
        ) : messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            <div className="message-avatar">{m.role==='user'?'👤':'🤖'}</div>
            <div className="message-content">
              {m.role==='user'?<div className="user-message">{m.content}</div>:renderMarkdown(m.content,i)}
            </div>
          </div>
        ))}
        {currentResponse && <div className="message assistant"><div className="message-avatar">🤖</div><div className="message-content">{renderMarkdown(currentResponse,messages.length)}</div></div>}
        {isLoading&&!currentResponse&&<div className="message assistant"><div className="message-avatar">🤖</div><div className="message-content"><div className="typing-indicator"><span/><span/><span/></div></div></div>}
        <div ref={messagesEndRef}/>
      </div>
    </div>
  );
}

export default MessageList;