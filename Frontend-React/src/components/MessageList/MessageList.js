import React, { useEffect, useRef, useState } from 'react';
import { LinkRenderer } from '../YoutubeRender/YouTubeRenderer';
import ImageRenderer from '../ImageRenderer/ImageRenderer';
import './MessageList.css';

// Utilidades de detección de enlaces e imágenes
const isYoutubeLink = href => /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\//.test(href);
const isImageLink = href => /\.(jpg|jpeg|png|gif|webp|bmp|svg)([?#].*)?$/i.test(href);
const isImageLabel = text => /^\s*\[(imagen|image)\b.*\]/i.test(text.trim());

// Detecta URLs de imágenes más ampliamente, incluso con parámetros complejos
const isImageUrl = url => {
  // Extensiones de imagen comunes
  if (/\.(jpg|jpeg|png|gif|webp|bmp|svg)([?#].*)?$/i.test(url)) return true;
  
  // URLs específicas de servicios de imágenes
  if (/cdninstagram\.com.*\.(jpg|jpeg|png|gif|webp)/i.test(url)) return true;
  if (/staticflickr\.com.*\.(jpg|jpeg|png|gif|webp)/i.test(url)) return true;
  if (/images\.unsplash\.com/i.test(url)) return true;
  if (/imgur\.com\/.*\.(jpg|jpeg|png|gif|webp)/i.test(url)) return true;
  
  return false;
};

// Limpia enlaces markdown redundantes de YouTube
const cleanYoutubeMarkdown = md => md.replace(
  /\[([^\]]+)\]\((https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/[\w\-?&=;%#@/.]+)\)/gi,
  (match, text, url) => (text.trim() === url.trim() ? url : match)
);

// Limpia enlaces markdown redundantes de imágenes
const cleanImageMarkdown = md => md.replace(
  /\[([^\]]+)\]\((https?:\/\/(?:[\w\-./]+)\.(?:jpg|jpeg|png|gif|webp|bmp|svg)(?:[?#][^)]+)?)\)/gi,
  (match, text, url) => (text.trim() === url.trim() ? url : match)
);

// Limpia indicadores de lista markdown
const cleanListIndicators = text => text.replace(/^\s*[\-*+•‣◦●▪‧·]\s+/, '');

// Procesa markdown con enlaces especiales
const splitMarkdownWithLinks = markdownInput => {
  // Aplicar limpieza primero a YouTube, luego a imágenes
  let markdown = cleanYoutubeMarkdown(markdownInput || '');
  markdown = cleanImageMarkdown(markdown);

  const patterns = {
    customImage: /^[\s\t]*([\-*+•‣◦●▪‧·])[\s\t]+(\[imagen[^\]]*\])\s*\[([^\]]+)\](?:\s*([^\n]*))?$/i,
    markdownImage: /^[\s\t]*([\-*+•‣◦●▪‧·])[\s\t]+(\[imagen[^\]]*\])\(([^)]+)\)(?:\s*([^\n]*))?$/i,
    singleMarkdownImage: /^\s*(\[imagen[^\]]*\])\(([^)]+)\)(?:\s*([^\n]*))?$/i,
    singleCustomImage: /^\s*(\[imagen[^\]]*\])\s*\[([^\]]+)\](?:\s*([^\n]*))?$/i,
    standardImage: /^\s*([\-*+]\s*)?!\[([^\]]*)\]\(([^)]+)\)\s*(.*)$/i,
    imageWithColon: /^[\s\t]*([\-*+•‣◦●▪‧·])[\s\t]+(\[imagen[^\]]*:\s*([^\]]+)\])(?:\s*([^\n]*))?$/i,
    singleImageWithColon: /^\s*(\[imagen[^\]]*:\s*([^\]]+)\])(?:\s*([^\n]*))?$/i,
    imageLink: /\[([^\]]*(?:imagen|image)[^\]]*)\]\((https?:\/\/[^\)]+\.(?:jpg|jpeg|png|gif|webp|bmp|svg)(?:\?[^\)]*)?)\)/gi,
    imageLinkColon: /\[imagen[^\]]*:\s*(https?:\/\/[^\]]+\.(?:jpg|jpeg|png|gif|webp|bmp|svg)(?:\?[^\)]*)?)\]/gi,
    //youtubeMarkdown: /\[([^\]]*)\]\((https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/[\w\-?&=;%#@/.]+)\)/gi,
    youtube: /(https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/[\w\-?&=;%#@/.]+)(\s*\(\s*\))?/gi,
    // Patrón mejorado para URLs de imágenes directas
    directImageUrl: /(https?:\/\/[^\s\)]+(?:\.(?:jpg|jpeg|png|gif|webp|bmp|svg)(?:[?#][^\s\)]*)?|cdninstagram\.com[^\s\)]*\.(?:jpg|jpeg|png|gif|webp)|staticflickr\.com[^\s\)]*\.(?:jpg|jpeg|png|gif|webp)|images\.unsplash\.com[^\s\)]*|imgur\.com\/[^\s\)]*\.(?:jpg|jpeg|png|gif|webp)))/gi
  };

  const lines = markdown.split(/\r?\n/);
  const result = [];
  let buffer = [];
  let imageBlock = [];

  const flushBuffer = () => {
    if (!buffer.length) return;
    const text = buffer.join('\n');
    if (text.trim()) processTextWithYoutubeAndImages(text, result);
    buffer = [];
  };

  const flushImageBlock = () => {
    if (!imageBlock.length) return;
    const allImgs = imageBlock.every(l => patterns.customImage.test(l) || patterns.markdownImage.test(l) || patterns.imageWithColon.test(l));
    if (allImgs) {
      imageBlock.forEach(l => {
        const m = patterns.customImage.exec(l) || patterns.markdownImage.exec(l) || patterns.imageWithColon.exec(l);
        if (m) {
          // Agregar texto previo primero para respetar orden
          if (m[4]?.trim()) {
            const cleanText = cleanListIndicators(m[4].trim());
            if (cleanText) processTextWithYoutubeAndImages(cleanText, result);
          }
          const url = patterns.imageWithColon.test(l) ? m[3] : (m[2] || m[2]);
          const text = patterns.imageWithColon.test(l) ? m[2] : m[2];
          result.push({ type: 'image', value: url, text });
        }
      });
    } else {
      processTextWithYoutubeAndImages(imageBlock.join('\n'), result);
    }
    imageBlock = [];
  };

  const processTextWithYoutubeAndImages = (text, resultArray) => {
    if (!text.trim()) return;
    
    // Mejorar la detección de imágenes - priorizar patrones específicos
    const imageMatches = [...text.matchAll(patterns.imageLink)];
    const imageColonMatches = [...text.matchAll(patterns.imageLinkColon)];
    //const youtubeMarkdownMatches = [...text.matchAll(patterns.youtubeMarkdown)];
    const youtubeMatches = [...text.matchAll(patterns.youtube)];
    const directImageMatches = [...text.matchAll(patterns.directImageUrl)];
    
    // Crear un conjunto de rangos ocupados por patrones específicos
    const occupiedRanges = new Set();
    const specificMatches = [
      ...imageMatches,
      ...imageColonMatches,
      //...youtubeMarkdownMatches,
      ...youtubeMatches.filter(m => !isImageUrl(m[1]))
    ];
    
    // Marcar rangos ocupados por patrones específicos
    specificMatches.forEach(match => {
      for (let i = match.index; i < match.index + match[0].length; i++) {
        occupiedRanges.add(i);
      }
    });
    
    // Filtrar URLs directas de imágenes que no conflicten con patrones específicos
    const filteredDirectImageMatches = directImageMatches.filter(match => {
      if (!isImageUrl(match[1])) return false;
      
      // Verificar si esta URL directa está dentro de un patrón específico
      for (let i = match.index; i < match.index + match[0].length; i++) {
        if (occupiedRanges.has(i)) return false;
      }
      return true;
    });
    
    const allMatches = [
      //...youtubeMarkdownMatches.map(m => ({ ...m, type: 'youtube', url: m[2], text: m[1] })),
      ...youtubeMatches.filter(m => !isImageUrl(m[1])) // Excluir URLs que son imágenes
        .map(m => ({ ...m, type: 'youtube', url: m[1], fullMatch: m[0] })),
      ...imageMatches.map(m => ({ ...m, type: 'image', url: m[2], altText: m[1] })),
      ...imageColonMatches.map(m => ({ ...m, type: 'image', url: m[1], altText: 'Imagen' })),
      ...filteredDirectImageMatches.map(m => ({ ...m, type: 'image', url: m[1], altText: 'Imagen' }))
    ].sort((a, b) => a.index - b.index);

    if (!allMatches.length) {
      resultArray.push({ type: 'text', value: text });
      return;
    }

    let lastIndex = 0;
    allMatches.forEach((match, idx) => {
      // Verificar si es una imagen con formato markdown que apunta a una URL de imagen plana
      let effectiveStartIndex = match.index;
      let shouldRemoveMarkdown = false;
      
      if (match.type === 'image') {
        // Verificar si es un patrón markdown que apunta directamente a una imagen
        const isDirectImageUrl = isImageUrl(match.url);
        const hasMarkdownFormat = match[0].includes('[') && match[0].includes(']') && match[0].includes('(') && match[0].includes(')');
        const hasExclamation = match.index > 0 && text[match.index - 1] === '!';
        
        // Solo eliminar markdown si es una URL directa de imagen con formato markdown
        if (isDirectImageUrl && (hasMarkdownFormat || hasExclamation)) {
          shouldRemoveMarkdown = true;
          if (hasExclamation) {
            effectiveStartIndex = match.index - 1;
          }
        }
      }
      
      // Agregar texto antes del match
      if (effectiveStartIndex > lastIndex) {
        const before = text.slice(lastIndex, effectiveStartIndex);
        if (before.trim()) resultArray.push({ type: 'text', value: before });
      }
      
      if (match.type === 'image') {
        // Verificar si hay texto inmediatamente antes de la imagen (sin salto de línea)
        const textBefore = text.slice(0, effectiveStartIndex);
        const lastChar = textBefore.slice(-1);
        const needsLineBreak = textBefore.trim() && lastChar !== '\n' && !textBefore.endsWith('\n\n');
        
        // Agregar salto de línea si es necesario
        if (needsLineBreak) {
          resultArray.push({ type: 'text', value: '\n\n' });
        }
        // Agregar la imagen
        resultArray.push({ type: 'image', value: match.url, text: match.altText });
      } else {
        // Agregar el enlace de YouTube
        const youtubeUrl = match.url || match[0];
        const youtubeText = match.text || youtubeUrl;
        resultArray.push({ type: 'youtube', value: youtubeUrl, text: youtubeText });

        // Agregar salto de línea después de YouTube si hay texto siguiente
        const nextMatch = allMatches[idx + 1];
        const textAfterYoutube = nextMatch ?
          text.slice(match.index + match[0].length, nextMatch.index) :
          text.slice(match.index + match[0].length);
        const textBerforeYoutube = text.slice(0, match.index);
        if(textAfterYoutube.endsWith('(\n') ) { textAfterYoutube.replace('(\n', '\n'); }
        if(textBerforeYoutube.endsWith('\n)') ) { textAfterYoutube.replace('\n)', '\n\n'); }
        if (textAfterYoutube.trim() && !textAfterYoutube.startsWith('\n')) {
          // Insertar un salto de línea virtual para evitar problemas de renderizado
          resultArray.push({ type: 'text', value: '\n\n' });
        }
      }
      
      lastIndex = match.index + match[0].length;
    });

    // Agregar texto restante después del último match
    if (lastIndex < text.length) {
      const after = text.slice(lastIndex);
      if (after.trim()) resultArray.push({ type: 'text', value: after });
    }
  };

  const processLine = line => {
    let m = patterns.standardImage.exec(line);
    if (m && isImageLink(m[3])) {
      if (m[4]?.trim()) buffer.push(cleanListIndicators(m[4].trim()));
      return result.push({ type: 'image', value: m[3], text: m[2] });
    }
    m = patterns.singleMarkdownImage.exec(line);
    if (m && isImageLabel(m[1]) && isImageLink(m[2])) {
      if (m[3]?.trim()) buffer.push(cleanListIndicators(m[3].trim()));
      return result.push({ type: 'image', value: m[2], text: m[1] });
    }
    m = patterns.singleCustomImage.exec(line);
    if (m && isImageLabel(m[1])) {
      if (m[3]?.trim()) buffer.push(cleanListIndicators(m[3].trim()));
      return result.push({ type: 'image', value: m[2], text: m[1] });
    }
    m = patterns.singleImageWithColon.exec(line);
    if (m) {
      if (m[3]?.trim()) buffer.push(cleanListIndicators(m[3].trim()));
      return result.push({ type: 'image', value: m[2], text: 'Imagen' });
    }
    return false;
  };

for (let i = 0; i < lines.length; i++) {
    const raw = cleanYoutubeMarkdown(lines[i]);
    if (patterns.customImage.test(raw) || 
        patterns.markdownImage.test(raw) || 
        patterns.imageWithColon.test(raw)) {
      flushBuffer();
      imageBlock.push(raw);
      const nxt = lines[i+1] || '';
      if (!patterns.customImage.test(nxt) && 
          !patterns.markdownImage.test(nxt) && 
          !patterns.imageWithColon.test(nxt)) {
        flushImageBlock();
      }
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
    const blockRe = /<(h[1-6]|p|ul|ol|li|blockquote|table|pre|code)/i;

    return (
      <div className="assistant-message" ref={el => htmlRefs.current[idx] = el}>
        {parts.map((part, i) => {
          if (part.type === 'image') {
            return (
              <div key={i} className="image-container">
                <ImageRenderer src={part.value} alt={part.text} href={part.value}/>
              </div>
            );
          }
          if (part.type === 'youtube') return <LinkRenderer key={i} href={part.value}>{part.text}</LinkRenderer>;
          if (part.type === 'link') return <a key={i} href={part.value} target="_blank" rel="noopener noreferrer">{part.text}</a>;
          if (part.type === 'text') {
            const v = part.value;
            if (!v.trim() && v !== '\n') return null;
            const wasListItem = /^\s*[\*\-\+]\s+/.test(v);
            const html = showdown.makeHtml(v);
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