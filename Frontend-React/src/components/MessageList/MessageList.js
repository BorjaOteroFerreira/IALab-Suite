import React, { useEffect, useRef } from 'react';
import { LinkRenderer } from '../YoutubeRender/YouTubeRenderer';
import ImageRenderer from '../ImageRenderer/ImageRenderer';
import './MessageList.css';

function isYoutubeLink(href) {
  return /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\//.test(href);
}
function isImageLink(href) {
  // Detecta extensiones de imagen en cualquier parte de la URL (path o parámetros)
  return /\.(jpg|jpeg|png|gif|webp|bmp|svg)([?#].*)?$/i.test(href) || /\.(jpg|jpeg|png|gif|webp|bmp|svg)([?#].*)?/i.test(href);
}
function isImageLabel(text) {
  return /^\s*\[(imagen|image)\b.*\]/i.test(text.trim());
}

// Limpia [url_youtube](url_youtube) y lo deja solo como url si es de YouTube y texto === url
function cleanYoutubeMarkdown(md) {
  // Busca patrones [url](url) donde url es de YouTube y texto === url
  return md.replace(/\[([^\]]+)\]\((https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/[\w\-?&=;%#@/\.]+)\)/gi, (match, text, url) => {
    if (text.trim() === url.trim()) {
      return url; // Solo deja la url una vez
    }
    return match;
  });
}

// Solo renderiza como miniatura los enlaces markdown de imagen cuyo texto empiece por "imagen"
function splitMarkdownWithLinks(markdown) {
  // --- LIMPIEZA DE ENLACES YOUTUBE MARKDOWN ---
  markdown = cleanYoutubeMarkdown(markdown);
  // Detecta bullets de lista válidos seguidos de [imagen, permitiendo espacios antes y después del bullet
  const bulletImagePattern = /^[\s\t]*([\-*+•‣◦●▪‣‧·])[\s\t]+(?=\[imagen[^\]]*\])/i;
  // Patrón para - [Imagen X] [url] descripción (bullet + espacio(s) + [imagen ...])
  const customImagePattern = /^[\s\t]*([\-*+•‣◦●▪‣‧·])[\s\t]+(\[imagen[^\]]*\])\s*\[([^\]]+)\](?:\s*([^\n]*))?$/i;
  // Patrón para - [imagen ...](url) descripción (bullet + espacio(s) + [imagen ...])
  const markdownImagePattern = /^[\s\t]*([\-*+•‣◦●▪‣‧·])[\s\t]+(\[imagen[^\]]*\])\(([^)]+)\)(?:\s*([^\n]*))?$/i;
  // Patrón para [imagen ...](url) descripción (sin bullet)
  const singleMarkdownImagePattern = /^\s*(\[imagen[^\]]*\])\(([^)]+)\)(?:\s*([^\n]*))?$/i;
  // Patrón para [imagen ...][url] descripción (sin bullet)
  const singleCustomImagePattern = /^\s*(\[imagen[^\]]*\])\s*\[([^\]]+)\](?:\s*([^\n]*))?$/i;
  // Patrón para [imagen ...] [url](url) (sin bullet)
  const labelLinkImagePattern = /^\s*(\[imagen[^\]]*\])\s*\[([^\]]+)\]\(([^)]+)\)(?:\s*([^\n]*))?$/i;

  const lines = markdown.split(/\r?\n/);
  let result = [];
  let buffer = [];
  let imageBlock = [];

  function isListLine(line) {
    return /^[\s\t]*([\-*+•‣◦●▪‣‧·])[\s\t]+/.test(line);
  }

  function flushBuffer() {
    if (buffer.length > 0) {
      for (let i = 0; i < buffer.length; i++) {
        let l = buffer[i];
        // Detectar imagen markdown estándar ![alt](url) ANTES que cualquier otro patrón
        let m = /^\s*([\-*+]\s*)?!\[([^\]]*)\]\(([^)]+)\)\s*(.*)$/i.exec(l);
        if (m && isImageLink(m[3])) {
          result.push({ type: 'image', value: m[3], text: m[2] });
          if (m[4] && m[4].trim()) result.push({ type: 'text', value: ' ' + m[4].trim() });
          continue;
        }
        // Detectar cualquier enlace de YouTube en la línea (plano o markdown)
        const youtubeRegex = /(https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/[\w\-?&=;%#@/\.]+)/ig;
        let match;
        let lastIndex = 0;
        let foundYoutube = false;
        let youtubeParts = [];
        while ((match = youtubeRegex.exec(l)) !== null) {
          foundYoutube = true;
          if (match.index > lastIndex) {
            const before = l.slice(lastIndex, match.index);
            if (before.replace(/\s+/g, '') !== '') {
              youtubeParts.push({ type: 'text', value: before });
            }
          }
          youtubeParts.push({ type: 'youtube', value: match[0], text: match[0] });
          lastIndex = youtubeRegex.lastIndex;
        }
        if (foundYoutube) {
          const after = l.slice(lastIndex);
          // Solo agregar el texto restante si NO es exactamente un enlace de YouTube
          const afterTrim = after.trim();
          if (
            afterTrim !== '' &&
            !/^https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/[\w\-?&=;%#@/\.]+$/i.test(afterTrim)
          ) {
            youtubeParts.push({ type: 'text', value: after });
          }
          youtubeParts.forEach(part => result.push(part));
          continue;
        }
        m = /^\s*(\[imagen[^\]]*\])\s*\(([^)]+)\)\s*(.*)$/i.exec(l);
        if (m && isImageLabel(m[1]) && isImageLink(m[2])) {
          result.push({ type: 'image', value: m[2], text: m[1] });
          if (m[3] && m[3].trim()) result.push({ type: 'text', value: ' ' + m[3].trim() });
          continue;
        }
        m = labelLinkImagePattern.exec(l);
        if (m && !isImageLink(m[3])) {
          result.push({ type: 'text', value: l });
          continue;
        }
        m = singleCustomImagePattern.exec(l);
        if (m && isImageLabel(m[1])) {
          result.push({ type: 'image', value: m[2], text: m[1] });
          if (m[3] && m[3].trim()) result.push({ type: 'text', value: ' ' + m[3].trim() });
          continue;
        }
        m = singleMarkdownImagePattern.exec(l);
        if (m && isImageLabel(m[1])) {
          result.push({ type: 'image', value: m[2], text: m[1] });
          if (m[3] && m[3].trim()) result.push({ type: 'text', value: ' ' + m[3].trim() });
          continue;
        }
        // Si no es imagen ni patrón especial, agregar como texto normal
        // --- CORRECCIÓN: solo agregar si no es vacío ni solo espacios ---
        if (l.replace(/\s+/g, '') !== '') {
          result.push({ type: 'text', value: l });
          if (i !== buffer.length - 1) {
            result.push({ type: 'text', value: '\n' });
          }
        }
      }
      buffer.length = 0;
    }
  }

  function flushImageBlock() {
    if (imageBlock.length > 0) {
      if (imageBlock.every(l => customImagePattern.test(l) || markdownImagePattern.test(l))) {
        for (let idx = 0; idx < imageBlock.length; idx++) {
          const l = imageBlock[idx];
          let m = customImagePattern.exec(l);
          if (m) {
            let label = m[2].replace(/^\[imagen/i, 'imagen');
            result.push({ type: 'image', value: m[3], text: label });
            if (m[4] && m[4].trim()) result.push({ type: 'text', value: ' ' + m[4].trim() });
            continue;
          }
          m = markdownImagePattern.exec(l);
          if (m) {
            let label = m[2].replace(/^\[imagen/i, 'imagen');
            result.push({ type: 'image', value: m[3], text: label });
            if (m[4] && m[4].trim()) result.push({ type: 'text', value: ' ' + m[4].trim() });
            continue;
          }
        }
      } else {
        result.push({ type: 'text', value: imageBlock.join('\n') });
      }
      imageBlock.length = 0;
    }
  }

  for (let i = 0; i < lines.length; i++) {
    // --- NUEVO: limpiar enlaces markdown de YouTube antes de procesar la línea ---
    const line = cleanYoutubeMarkdown(lines[i]);
    if (customImagePattern.test(line) || markdownImagePattern.test(line)) {
      flushBuffer();
      imageBlock.push(line);
      if (i === lines.length - 1 || (!customImagePattern.test(lines[i + 1]) && !markdownImagePattern.test(lines[i + 1]))) {
        flushImageBlock();
      }
    } else {
      flushImageBlock();
      buffer.push(line);
    }
  }
  // --- CORRECCIÓN: limpiar fragmentos vacíos antes de pasar a showdown ---
  flushBuffer();
  flushImageBlock();
  // Limpieza final: eliminar fragmentos de texto vacíos o solo espacios
  return result.filter(part => {
    if (part.type === 'text') {
      return part.value && part.value.replace(/\s+/g, '') !== '';
    }
    return true;
  });
}

function MessageList({ messages, currentResponse, isLoading, messagesEndRef }) {
  const [showdownConverter, setShowdownConverter] = React.useState(null);
  const [hljs, setHljs] = React.useState(null);
  const htmlRefs = useRef([]);

  useEffect(() => {
    let mounted = true;
    import('showdown').then((mod) => {
      if (mounted) {
        setShowdownConverter(new mod.Converter({
          tables: true,
          simplifiedAutoLink: true,
          openLinksInNewWindow: true,
          strikethrough: true,
          emoji: true,
          tasklists: true,
          ghCodeBlocks: true,
        }));
      }
    });
    import('highlight.js').then((mod) => {
      if (mounted) {
        setHljs(mod.default || mod);
      }
    });
    return () => { mounted = false; };
  }, []);

  // Aplica highlight.js a todos los bloques de código después de renderizar
  useEffect(() => {
    if (hljs && htmlRefs.current) {
      htmlRefs.current.forEach(ref => {
        if (ref) {
          ref.querySelectorAll('pre code').forEach(block => {
            hljs.highlightElement(block);
          });
        }
      });
    }
  }, [messages, currentResponse, hljs]);

  // Renderiza markdown con YouTube, imágenes y enlaces normales como componentes React
  const renderMarkdownSmart = (content, idx) => {
    if (!showdownConverter) return <div className="assistant-message">Cargando...</div>;
    const parts = splitMarkdownWithLinks(content || '');
    return (
      <div className="assistant-message" ref={el => htmlRefs.current[idx] = el}>
        {parts.map((part, i) => {
          if (part.type === 'image') {
            return <ImageRenderer key={i} src={part.value} alt={part.text} href={part.value} />;
          } else if (part.type === 'youtube') {
            return <LinkRenderer key={i} href={part.value}>{part.text || part.value}</LinkRenderer>;
          } else if (part.type === 'link') {
            return <a key={i} href={part.value} target="_blank" rel="noopener noreferrer">{part.text}</a>;
          } else if (part.value.trim() !== '') {
            // Solo limpiar bullets si el fragmento es un bloque de imágenes aplanado
            // Para todos los demás fragmentos, pasar el texto tal cual a showdown
            const html = showdownConverter.makeHtml(part.value);
            if (/^<pre[\s>]/.test(html.trim())) {
              return <div key={i} className="assistant-md-fragment" dangerouslySetInnerHTML={{ __html: html }} />;
            } else {
              return <span key={i} className="assistant-md-fragment" dangerouslySetInnerHTML={{ __html: html }} />;
            }
          } else {
            return null;
          }
        })}
      </div>
    );
  };

  return (
    <div className="messages-container">
      <div className="messages-list">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h2>¡Bienvenido a AI Lab Suite! 🚀</h2>
            <p className="welcome-message-p">Escribe un mensaje para comenzar la conversación.</p>
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
                  renderMarkdownSmart(message.content, idx)
                )}
              </div>
            </div>
          ))
        )}

        {currentResponse && (
          <div className="message assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              {renderMarkdownSmart(currentResponse, messages.length)}
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
