import React, { useEffect, useRef, useState } from 'react';
import { LinkRenderer } from '../YoutubeRender/YouTubeRenderer';
import ImageRenderer from '../ImageRenderer/ImageRenderer';
import GoogleMapsRenderer from '../GoogleMapsRenderer/GoogleMapsRenderer';
import './MessageList.css';

// Utilidades de detección de enlaces e imágenes
const isYoutubeLink = href => /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\//.test(href);
const isImageLink = href => /\.(jpg|jpeg|png|gif|webp|bmp|svg)([?#].*)?$/i.test(href);
const isGoogleMapsLink = href => /https?:\/\/(www\.)?maps\.google\.com\/maps\?q=[^\s)]+/i.test(href);

// Limpia enlaces markdown redundantes de YouTube
const cleanYoutubeMarkdown = md => md.replace(
  /\[([^\]]+)\]\((https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/[\w\-?&=;%#@/.]+)\)/gi,
  (match, text, url) => (text.trim() === url.trim() ? url : match)
);

// Procesa markdown con enlaces especiales
const splitMarkdownWithLinks = markdownInput => {
  // Aplicar limpieza a YouTube
  let markdown = cleanYoutubeMarkdown(markdownInput || '');

  const patterns = {
    // Solo mantenemos el patrón markdown estándar para imágenes
    standardImage: /!\[([^\]]*)\]\(([^)]+)\)/gi,
    youtube: /(https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/[\w\-?&=;%#@/.]+)(\s*\(\s*\))?/gi,
    googlemaps: /(https?:\/\/(?:www\.)?maps\.google\.com\/maps\?q=[^\s)]+)/gi
  };

  const processTextWithYoutubeAndImages = (text, resultArray) => {
    if (!text.trim()) return;
    
    const imageMatches = [...text.matchAll(patterns.standardImage)];
    const youtubeMatches = [...text.matchAll(patterns.youtube)];
    const googleMapsMatches = [...text.matchAll(patterns.googlemaps)];
    
    const allMatches = [
      ...youtubeMatches.map(m => ({ ...m, type: 'youtube', url: m[1], fullMatch: m[0] })),
      ...googleMapsMatches.map(m => ({ ...m, type: 'googlemaps', url: m[1], fullMatch: m[0] })),
      ...imageMatches.map(m => ({ ...m, type: 'image', url: m[2], altText: m[1] }))
    ].sort((a, b) => a.index - b.index);

    if (!allMatches.length) {
      resultArray.push({ type: 'text', value: text });
      return;
    }

    let lastIndex = 0;
    allMatches.forEach((match, idx) => {
      // Agregar texto antes del match
      if (match.index > lastIndex) {
        let before = text.slice(lastIndex, match.index);
        
        // Si el siguiente match es una imagen, limpiar asteriscos del texto anterior
        if (match.type === 'image') {
          // Eliminar asteriscos sueltos que preceden a imágenes
          before = before.replace(/\s*[\*\-\+]\s*$/, '');
        }
        
        if (before.trim()) resultArray.push({ type: 'text', value: before });
      }
      
      if (match.type === 'image') {
        // Verificar si hay texto inmediatamente antes de la imagen (sin salto de línea)
        const textBefore = text.slice(0, match.index);
        const lastChar = textBefore.slice(-1);
        const needsLineBreak = textBefore.trim() && lastChar !== '\n' && !textBefore.endsWith('\n\n');
        
        // Agregar salto de línea si es necesario
        if (needsLineBreak) {
          resultArray.push({ type: 'text', value: '\n\n' });
        }
        // Agregar la imagen
        resultArray.push({ type: 'image', value: match.url, text: match.altText });
      } else if (match.type === 'youtube') {
        // Agregar el enlace de YouTube
        const youtubeUrl = match.url || match[0];
        const youtubeText = match.text || youtubeUrl;
        resultArray.push({ type: 'youtube', value: youtubeUrl, text: youtubeText });

        // Agregar salto de línea después de YouTube si hay texto siguiente
        const nextMatch = allMatches[idx + 1];
        const textAfterYoutube = nextMatch ?
          text.slice(match.index + match[0].length, nextMatch.index) :
          text.slice(match.index + match[0].length);
        
        if (textAfterYoutube.trim() && !textAfterYoutube.startsWith('\n')) {
          // Insertar un salto de línea virtual para evitar problemas de renderizado
          resultArray.push({ type: 'text', value: '\n\n' });
        }
      } else if (match.type === 'googlemaps') {
        // Agregar el enlace de Google Maps
        const googleMapsUrl = match.url || match[0];
        const googleMapsText = match.text || googleMapsUrl;
        resultArray.push({ type: 'googlemaps', value: googleMapsUrl, text: googleMapsText });
      }
      
      lastIndex = match.index + match[0].length;
    });

    // Agregar texto restante después del último match
    if (lastIndex < text.length) {
      const after = text.slice(lastIndex);
      if (after.trim()) resultArray.push({ type: 'text', value: after });
    }
  };

  // Procesar el texto completo
  const result = [];
  processTextWithYoutubeAndImages(markdown, result);
  
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
    const blockRe = /<(h[1-6]|p|ul|ol|li|blockquote|table|pre|code)/i;

    // Agrupar imágenes consecutivas ignorando saltos de línea y espacios
    const grouped = [];
    let imageBuffer = [];
    let skipIndexes = new Set();
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      // Si es imagen, agregar al buffer
      if (part.type === 'image') {
        imageBuffer.push(part);
        // Buscar imágenes siguientes separadas solo por saltos de línea o espacios
        let j = i + 1;
        while (j < parts.length && (
          (parts[j].type === 'text' && (!parts[j].value.trim() || /^\s*\n+\s*$/.test(parts[j].value))) || parts[j].type === 'image')
        ) {
          if (parts[j].type === 'image') {
            imageBuffer.push(parts[j]);
            skipIndexes.add(j);
          }
          j++;
        }
        i = j - 1;
        if (imageBuffer.length === 1) {
          grouped.push(imageBuffer[0]);
        } else if (imageBuffer.length > 1) {
          grouped.push({ type: 'image-row', images: imageBuffer });
        }
        imageBuffer = [];
      } else if (!skipIndexes.has(i)) {
        grouped.push(part);
      }
    }
    if (imageBuffer.length === 1) {
      grouped.push(imageBuffer[0]);
    } else if (imageBuffer.length > 1) {
      grouped.push({ type: 'image-row', images: imageBuffer });
    }

    return (
      <div className="assistant-message" ref={el => htmlRefs.current[idx] = el}>
        {grouped.map((part, i) => {
          if (part.type === 'image-row') {
            return (
              <div key={i} className="image-container-row">
                {part.images.map((img, j) => (
                  <div key={j} className="image-container">
                    <ImageRenderer src={img.value} alt={img.text} href={img.value}/>
                  </div>
                ))}
              </div>
            );
          }
          if (part.type === 'image') {
            // Esto solo ocurrirá si hay una imagen aislada
            return (
              <div key={i} className="image-container">
                <ImageRenderer src={part.value} alt={part.text} href={part.value}/>
              </div>
            );
          }
          if (part.type === 'googlemaps') {
            return <GoogleMapsRenderer key={i} url={part.url} alt={part.text || 'Mapa de Google Maps'} />;
          }
          if (part.type === 'youtube') return <LinkRenderer key={i} href={part.value}>{part.text}</LinkRenderer>;
          if (part.type === 'link') return <a key={i} href={part.value} target="_blank" rel="noopener noreferrer">{part.text}</a>;
          if (part.type === 'text') {
            const v = part.value;
            if (!v.trim() && v !== '\n') return null;
            
            // Filtrar asteriscos sueltos que pueden generar elementos de lista vacíos
            let cleanedValue = v.replace(/^\s*[\*\-\+]\s*$/, '').trim();
            
            // Eliminar dos puntos (:) al inicio de línea, preservando el texto que sigue
            cleanedValue = cleanedValue.replace(/^:\s*/gm, '');
            
            if (!cleanedValue) return null;
            
            const wasListItem = /^\s*[\*\-\+]\s+/.test(v);
            const html = showdown.makeHtml(cleanedValue);
            
            // Evitar renderizar elementos vacíos o solo con asteriscos
            if (html.trim() === '<p></p>' || html.trim() === '' || /^<[^>]*>\s*<\/[^>]*>$/.test(html.trim())) {
              return null;
            }
            
            const isBlockContent = blockRe.test(html.trim()) && !wasListItem;
            const shouldBeBlock = isBlockContent || /^\s*[\*\-\+]\s+/.test(v);
            const Tag = shouldBeBlock ? 'div' : 'span';
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
            <div className="message-avatar">{m.role==='user'? '👤' : '🤖'}</div>
            <div className="message-content">
              {m.role === 'user'
                ? <div className="user-message">{m.content}</div>
                : renderMarkdown(m.content, i)
              }
            </div>
          </div>
        ))}
        {currentResponse && (
          <div className="message assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">{renderMarkdown(currentResponse, messages.length)}</div>
          </div>
        )}
        {isLoading && !currentResponse && (
          <div className="message assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="typing-indicator"><span/><span/><span/></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef}/>
      </div>
    </div>
  );
}

export default MessageList;