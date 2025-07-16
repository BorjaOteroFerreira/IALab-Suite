import { useState, useEffect, useRef } from 'react';
import useTTS from './useTTS';
import { useLanguage } from '../context/LanguageContext';
import { LinkRenderer as YouTubeLinkRenderer } from '../components/Renderers/YoutubeRender/YouTubeRenderer';
import { LinkRenderer as TikTokLinkRenderer, cleanTikTokMarkdown } from '../components/Renderers/TikTokRender/TikTokRenderer';
import { LinkRenderer as SpotifyLinkRenderer, cleanSpotifyMarkdown } from '../components/Renderers/SpotifyRender/SpotifyRenderer';
import { LinkRenderer as SoundCloudLinkRenderer, cleanSoundCloudMarkdown } from '../components/Renderers/SoundCloudRender/SoundCloudRenderer';
import { DailymotionLinkRenderer } from '../components/Renderers/DailymotionRender/DailymotionRenderer';
import ImageRenderer from '../components/Renderers/ImageRenderer/ImageRenderer';
import GoogleMapsRenderer from '../components/Renderers/GoogleMapsRenderer/GoogleMapsRenderer';
import CodeBlock from '../components/Renderers/CodeBlock/CodeBlock';

const isYoutubeLink = href => /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\//.test(href);
const isTikTokLink = href => /^(https?:\/\/)?(www\.)?tiktok\.com\//.test(href);
const isSpotifyLink = href => /^(https?:\/\/)?(open\.)?spotify\.com\/(?:[a-zA-Z0-9\-]+\/)?(track|album|playlist|artist)\//.test(href);
const isSoundCloudLink = href => /^(https?:\/\/)?(www\.)?soundcloud\.com\//.test(href);
const isDailymotionLink = href => /^(https?:\/\/)?(www\.)?dailymotion\.com\/(video|playlist)\//.test(href);
const isImageLink = href => /\.(jpg|jpeg|png|gif|webp|bmp|svg)([?#].*)?$/i.test(href);
const isGoogleMapsLink = href => /https?:\/\/(www\.)?maps\.google\.com\/maps\?q=[^\s)]+/i.test(href);

const cleanYoutubeMarkdown = md => md.replace(
  /\[([^\]]+)\]\((https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/[\w\-?&=;%#@/.]+)\)/gi,
  (match, text, url) => (text.trim() === url.trim() ? url : match)
);

// Agregar limpieza de markdown de Spotify
const cleanAllMarkdown = md => {
  let out = cleanYoutubeMarkdown(md);
  out = cleanTikTokMarkdown(out);
  out = cleanSpotifyMarkdown(out);
  out = cleanSoundCloudMarkdown(out);
  return out;
};

// Función para limpiar URLs de caracteres finales no deseados
const cleanUrl = url => {
  if (!url) return '';
  // Remover caracteres de puntuación final que no son parte del URL
  return url.replace(/[)\]}.,:;!?]*$/, '');
};

const splitMarkdownWithLinks = markdownInput => {
  let markdown = cleanAllMarkdown(markdownInput || '');
  const patterns = {
    standardImage: /!\[([^\]]*)\]\(([^)]+)\)/gi,
    // Primero procesar enlaces markdown estándar
    markdownLink: /\[([^\]]+)\]\(([^)]+)\)/gi,
    // Luego URLs directos con regex mejoradas
    youtube: /(https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/[\w\-?&=;%#@/.]+)(?=\s|$|\)|,|\.|\!|\?|;|:|"|')/gi,
    tiktok: /(https?:\/\/(?:www\.)?tiktok\.com\/[\w\-?&=;%#@/.]+)(?=\s|$|\)|,|\.|\!|\?|;|:|"|')/gi,
    spotify: /(https?:\/\/(open\.)?spotify\.com\/(?:[a-zA-Z0-9\-]+\/)?(track|album|playlist|artist)\/[a-zA-Z0-9]+(\?si=[\w-]+)?)(?=\s|$|\)|,|\.|\!|\?|;|:|"|')/gi,
    soundcloud: /(https?:\/\/(www\.)?soundcloud\.com\/[\w\-]+\/[\w\-]+)(?=\s|$|\)|,|\.|\!|\?|;|:|"|')/gi,
    dailymotion: /(https?:\/\/(www\.)?dailymotion\.com\/video\/[\w]+)(?=\s|$|\)|,|\.|!|\?|;|:|"|')/gi,
    dailymotionPlaylist: /(https?:\/\/(www\.)?dailymotion\.com\/playlist\/[\w]+)(?=\s|$|\)|,|\.|!|\?|;|:|"|')/gi,
    googlemaps: /(https?:\/\/(?:www\.)?maps\.google\.com\/maps\?q=[^\s)]+)(?=\s|$|\)|,|\.|\!|\?|;|:|"|')/gi
  };
  
  const processTextWithYoutubeAndImages = (text, resultArray) => {
    if (!text.trim()) return;
    const imageMatches = [...text.matchAll(patterns.standardImage)];
    const markdownLinkMatches = [...text.matchAll(patterns.markdownLink)];
    const youtubeMatches = [...text.matchAll(patterns.youtube)];
    const tiktokMatches = [...text.matchAll(patterns.tiktok)];
    const spotifyMatches = [...text.matchAll(patterns.spotify)];
    const soundcloudMatches = [...text.matchAll(patterns.soundcloud)];
    const dailymotionMatches = [...text.matchAll(patterns.dailymotion)];
    const dailymotionPlaylistMatches = [...text.matchAll(patterns.dailymotionPlaylist)];
    const googleMapsMatches = [...text.matchAll(patterns.googlemaps)];
    
    const allMatches = [
      ...markdownLinkMatches.map(m => {
        const url = m[2];
        const linkText = m[1];
        let linkType = 'link';
        
        // Determinar el tipo de enlace basado en la URL
        if (isYoutubeLink(url)) linkType = 'youtube';
        else if (isTikTokLink(url)) linkType = 'tiktok';
        else if (isSpotifyLink(url)) linkType = 'spotify';
        else if (isSoundCloudLink(url)) linkType = 'soundcloud';
        else if (isDailymotionLink(url)) linkType = 'dailymotion';
        else if (isGoogleMapsLink(url)) linkType = 'googlemaps';
        
        return {
          ...m,
          type: linkType,
          url: cleanUrl(url),
          text: linkText,
          matchLength: m[0].length
        };
      }),
      ...youtubeMatches.map(m => ({ 
        ...m, 
        type: 'youtube', 
        url: cleanUrl(m[1]),
        fullMatch: m[0],
        matchLength: m[1].length
      })),
      ...tiktokMatches.map(m => ({ 
        ...m, 
        type: 'tiktok', 
        url: cleanUrl(m[1]),
        fullMatch: m[0],
        matchLength: m[1].length
      })),
      ...spotifyMatches.map(m => ({ 
        ...m, 
        type: 'spotify', 
        url: cleanUrl(m[1]),
        fullMatch: m[0],
        matchLength: m[1].length
      })),
      ...soundcloudMatches.map(m => ({ 
        ...m, 
        type: 'soundcloud', 
        url: cleanUrl(m[1]),
        fullMatch: m[0],
        matchLength: m[1].length
      })),
      ...dailymotionMatches.map(m => ({ 
        ...m, 
        type: 'dailymotion', 
        url: cleanUrl(m[1]),
        fullMatch: m[0],
        matchLength: m[1].length
      })),
      ...dailymotionPlaylistMatches.map(m => ({ 
        ...m, 
        type: 'dailymotion', 
        url: cleanUrl(m[1]),
        fullMatch: m[0],
        matchLength: m[1].length
      })),
      ...googleMapsMatches.map(m => ({ 
        ...m, 
        type: 'googlemaps', 
        url: cleanUrl(m[1]),
        fullMatch: m[0],
        matchLength: m[1].length
      })),
      ...imageMatches.map(m => ({ 
        ...m, 
        type: 'image', 
        url: m[2], 
        altText: m[1],
        matchLength: m[0].length
      }))
    ].sort((a, b) => a.index - b.index);
    
    // Filtrar matches que se solapan (dar prioridad a los enlaces markdown)
    const filteredMatches = [];
    for (let i = 0; i < allMatches.length; i++) {
      const current = allMatches[i];
      const isOverlapping = filteredMatches.some(existing => {
        const currentEnd = current.index + current.matchLength;
        const existingEnd = existing.index + existing.matchLength;
        return (current.index < existingEnd && currentEnd > existing.index);
      });
      
      if (!isOverlapping) {
        filteredMatches.push(current);
      }
    }
    
    if (!filteredMatches.length) {
      resultArray.push({ type: 'text', value: text });
      return;
    }
    
    let lastIndex = 0;
    filteredMatches.forEach((match, idx) => {
      if (match.index > lastIndex) {
        let before = text.slice(lastIndex, match.index);
        if (match.type === 'image') {
          before = before.replace(/\s*[\*\-\+]\s*$/, '');
        }
        if (before.trim()) resultArray.push({ type: 'text', value: before });
      }
      
      if (match.type === 'image') {
        const textBefore = text.slice(0, match.index);
        const lastChar = textBefore.slice(-1);
        const needsLineBreak = textBefore.trim() && lastChar !== '\n' && !textBefore.endsWith('\n\n');
        if (needsLineBreak) {
          resultArray.push({ type: 'text', value: '\n\n' });
        }
        resultArray.push({ type: 'image', value: match.url, text: match.altText });
      } else if (match.type === 'youtube') {
        const youtubeUrl = match.url;
        const youtubeText = match.text || youtubeUrl;
        resultArray.push({ type: 'youtube', value: youtubeUrl, text: youtubeText });
        const nextMatch = filteredMatches[idx + 1];
        const textAfterYoutube = nextMatch ?
          text.slice(match.index + match.matchLength, nextMatch.index) :
          text.slice(match.index + match.matchLength);
        if (textAfterYoutube.trim() && !textAfterYoutube.startsWith('\n')) {
          resultArray.push({ type: 'text', value: '\n\n' });
        }
      } else if (match.type === 'tiktok') {
        const tiktokUrl = match.url;
        const tiktokText = match.text || tiktokUrl;
        resultArray.push({ type: 'tiktok', value: tiktokUrl, text: tiktokText });
      } else if (match.type === 'spotify') {
        const spotifyUrl = match.url;
        const spotifyText = match.text || spotifyUrl;
        resultArray.push({ type: 'spotify', value: spotifyUrl, text: spotifyText });
      } else if (match.type === 'soundcloud') {
        const soundcloudUrl = match.url;
        const soundcloudText = match.text || soundcloudUrl;
        resultArray.push({ type: 'soundcloud', value: soundcloudUrl, text: soundcloudText });
      } else if (match.type === 'dailymotion') {
        const dailymotionUrl = match.url;
        const dailymotionText = match.text || dailymotionUrl;
        resultArray.push({ type: 'dailymotion', value: dailymotionUrl, text: dailymotionText });
      } else if (match.type === 'googlemaps') {
        const googleMapsUrl = match.url;
        const googleMapsText = match.text || googleMapsUrl;
        resultArray.push({ type: 'googlemaps', value: googleMapsUrl, text: googleMapsText });
      } else if (match.type === 'link') {
        // Enlaces markdown genéricos que no son de plataformas específicas
        resultArray.push({ type: 'link', value: match.url, text: match.text });
      }
      
      lastIndex = match.index + match.matchLength;
    });
    
    if (lastIndex < text.length) {
      const after = text.slice(lastIndex);
      // Limpiar caracteres residuales al inicio del texto que queda
      const cleanedAfter = after.replace(/^[\s\)\]}.,:;!?]*/, '');
      if (cleanedAfter.trim()) resultArray.push({ type: 'text', value: cleanedAfter });
    }
  };
  
  const result = [];
  processTextWithYoutubeAndImages(markdown, result);
  return result.filter(x => x.value != null);
};

export function useMessageList(messages, currentResponse, messagesEndRef, ttsEnabled) {
  const [showdown, setShowdown] = useState(null);
  const [hljs, setHljs] = useState(null);
  const htmlRefs = useRef([]);
  const { lang, getStrings } = useLanguage();
  const general = getStrings('general');
  const [ttsOpen, setTTSOpen] = useState({});

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

  const lastAssistantMessage = messages.length > 0
    ? [...messages].reverse().find(m => m.role === 'assistant' && m.content)
    : null;

  useTTS(lastAssistantMessage?.content, ttsEnabled);

  const toggleTTS = idx => {
    setTTSOpen(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const renderMarkdown = (text, idx) => {
    if (!showdown) return <div className="assistant-message">{lang === 'es' ? 'Cargando...' : 'Loading...'}</div>;
    const parts = splitMarkdownWithLinks(text || '');
    const blockRe = /<(h[1-6]|p|ul|ol|li|blockquote|table|pre|code)/i;
    // Agrupar imágenes consecutivas ignorando saltos de línea y espacios
    const grouped = [];
    let imageBuffer = [];
    let skipIndexes = new Set();
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (part.type === 'image') {
        imageBuffer.push(part);
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
    // Detectar bloques de código en el markdown
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    let rawText = text || '';
    let codeBlocks = [];
    let match;
    while ((match = codeBlockRegex.exec(rawText)) !== null) {
      codeBlocks.push({
        language: match[1] || 'plaintext',
        code: match[2]
      });
    }
    let codeBlockIdx = 0;
    return (
      <div className="assistant-message">
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
            return (
              <div key={i} className="image-container">
                <ImageRenderer src={part.value} alt={part.text} href={part.value}/>
              </div>
            );
          }
          if (part.type === 'googlemaps') {
            return <GoogleMapsRenderer key={i} url={part.url} alt={part.text || 'Mapa de Google Maps'} />;
          }
          if (part.type === 'youtube') return <YouTubeLinkRenderer key={i} href={part.value}>{part.text}</YouTubeLinkRenderer>;
          if (part.type === 'tiktok') return <TikTokLinkRenderer key={i} href={part.value}>{part.text}</TikTokLinkRenderer>;
          if (part.type === 'spotify') return <SpotifyLinkRenderer key={i} href={part.value}>{part.text}</SpotifyLinkRenderer>;
          if (part.type === 'soundcloud') return <SoundCloudLinkRenderer key={i} href={part.value}>{part.text}</SoundCloudLinkRenderer>;
          if (part.type === 'dailymotion') return <DailymotionLinkRenderer key={i} href={part.value}>{part.text}</DailymotionLinkRenderer>;
          if (part.type === 'link') {
            if (isYoutubeLink(part.value)) return <YouTubeLinkRenderer key={i} href={part.value}>{part.text}</YouTubeLinkRenderer>;
            if (isTikTokLink(part.value)) return <TikTokLinkRenderer key={i} href={part.value}>{part.text}</TikTokLinkRenderer>;
            if (isSpotifyLink(part.value)) return <SpotifyLinkRenderer key={i} href={part.value}>{part.text}</SpotifyLinkRenderer>;
            if (isSoundCloudLink(part.value)) return <SoundCloudLinkRenderer key={i} href={part.value}>{part.text}</SoundCloudLinkRenderer>;
            if (isDailymotionLink(part.value)) return <DailymotionLinkRenderer key={i} href={part.value}>{part.text}</DailymotionLinkRenderer>;
            return <a key={i} href={part.value} target="_blank" rel="noopener noreferrer">{part.text}</a>;
          }
          if (part.type === 'text') {
            // Renderizar bloques de código con Prism y números de línea
            const v = part.value;
            if (!v.trim() && v !== '\n') return null;
            let cleanedValue = v.replace(/^\s*[\*\-\+]\s*$/, '').trim();
            cleanedValue = cleanedValue.replace(/^:\s*/gm, '');
            if (!cleanedValue) return null;
            // Buscar si el texto contiene un bloque de código
            const codeBlockRegexLocal = /```(\w+)?\n([\s\S]*?)```/g;
            const codeMatches = [];
            let codeMatch;
            let lastIndex = 0;
            while ((codeMatch = codeBlockRegexLocal.exec(cleanedValue)) !== null) {
              // Renderizar texto antes del bloque de código
              if (codeMatch.index > lastIndex) {
                const beforeCode = cleanedValue.slice(lastIndex, codeMatch.index);
                if (beforeCode.trim()) {
                  const html = showdown.makeHtml(beforeCode);
                  if (html.trim() !== '<p></p>' && html.trim() !== '') {
                    codeMatches.push(<div key={i + '-pre-' + lastIndex} className="assistant-md-fragment" dangerouslySetInnerHTML={{ __html: html }} />);
                  }
                }
              }
              codeMatches.push(<CodeBlock key={i + '-code-' + codeMatch.index} code={codeMatch[2]} language={codeMatch[1] || 'plaintext'} />);
              lastIndex = codeBlockRegexLocal.lastIndex;
            }
            // Renderizar texto después del último bloque de código
            if (lastIndex < cleanedValue.length) {
              const afterCode = cleanedValue.slice(lastIndex);
              if (afterCode.trim()) {
                const html = showdown.makeHtml(afterCode);
                if (html.trim() !== '<p></p>' && html.trim() !== '') {
                  codeMatches.push(<div key={i + '-post-' + lastIndex} className="assistant-md-fragment" dangerouslySetInnerHTML={{ __html: html }} />);
                }
              }
            }
            if (codeMatches.length > 0) return codeMatches;
            // Si no hay bloques de código, renderizar como antes
            const wasListItem = /^\s*[\*\-\+]\s+/.test(v);
            const html = showdown.makeHtml(cleanedValue);
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

  return {
    lang,
    general,
    ttsOpen,
    toggleTTS,
    renderMarkdown
  };
}

export const cleanLink = link => {
  let l = link.trim();
  if (l.endsWith('.')) l = l.slice(0, -1);
  if (l.endsWith(')')) l = l.slice(0, -1);
  if (l.startsWith('[') && l.endsWith(']')) l = l.slice(1, -1);
  return l;
};