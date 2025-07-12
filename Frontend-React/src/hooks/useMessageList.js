import { useState, useEffect, useRef } from 'react';
import useTTS from './useTTS';
import { useLanguage } from '../context/LanguageContext';
import { LinkRenderer as YouTubeLinkRenderer } from '../components/Renderers/YoutubeRender/YouTubeRenderer';
import { LinkRenderer as TikTokLinkRenderer, cleanTikTokMarkdown } from '../components/Renderers/TikTokRender/TikTokRenderer';
import ImageRenderer from '../components/Renderers/ImageRenderer/ImageRenderer';
import GoogleMapsRenderer from '../components/Renderers/GoogleMapsRenderer/GoogleMapsRenderer';

const isYoutubeLink = href => /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\//.test(href);
const isTikTokLink = href => /^(https?:\/\/)?(www\.)?tiktok\.com\//.test(href);
const isImageLink = href => /\.(jpg|jpeg|png|gif|webp|bmp|svg)([?#].*)?$/i.test(href);
const isGoogleMapsLink = href => /https?:\/\/(www\.)?maps\.google\.com\/maps\?q=[^\s)]+/i.test(href);

const cleanYoutubeMarkdown = md => md.replace(
  /\[([^\]]+)\]\((https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/[\w\-?&=;%#@/.]+)\)/gi,
  (match, text, url) => (text.trim() === url.trim() ? url : match)
);

const splitMarkdownWithLinks = markdownInput => {
  let markdown = cleanYoutubeMarkdown(markdownInput || '');
  markdown = cleanTikTokMarkdown(markdown);
  const patterns = {
    standardImage: /!\[([^\]]*)\]\(([^)]+)\)/gi,
    youtube: /(https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/[\w\-?&=;%#@/.]+)(\s*\(\s*\))?/gi,
    tiktok: /(https?:\/\/(?:www\.)?tiktok\.com\/[\w\-?&=;%#@/.]+)(\s*\(\s*\))?/gi,
    googlemaps: /(https?:\/\/(?:www\.)?maps\.google\.com\/maps\?q=[^\s)]+)/gi
  };
  const processTextWithYoutubeAndImages = (text, resultArray) => {
    if (!text.trim()) return;
    const imageMatches = [...text.matchAll(patterns.standardImage)];
    const youtubeMatches = [...text.matchAll(patterns.youtube)];
    const tiktokMatches = [...text.matchAll(patterns.tiktok)];
    const googleMapsMatches = [...text.matchAll(patterns.googlemaps)];
    const allMatches = [
      ...youtubeMatches.map(m => ({ ...m, type: 'youtube', url: m[1], fullMatch: m[0] })),
      ...tiktokMatches.map(m => ({ ...m, type: 'tiktok', url: m[1], fullMatch: m[0] })),
      ...imageMatches.map(m => ({ ...m, type: 'image', url: m[2], altText: m[1] }))
    ].sort((a, b) => a.index - b.index);
    if (!allMatches.length) {
      resultArray.push({ type: 'text', value: text });
      return;
    }
    let lastIndex = 0;
    allMatches.forEach((match, idx) => {
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
        const youtubeUrl = match.url || match[0];
        const youtubeText = match.text || youtubeUrl;
        resultArray.push({ type: 'youtube', value: youtubeUrl, text: youtubeText });
        const nextMatch = allMatches[idx + 1];
        const textAfterYoutube = nextMatch ?
          text.slice(match.index + match[0].length, nextMatch.index) :
          text.slice(match.index + match[0].length);
        if (textAfterYoutube.trim() && !textAfterYoutube.startsWith('\n')) {
          resultArray.push({ type: 'text', value: '\n\n' });
        }
      } else if (match.type === 'tiktok') {
        const tiktokUrl = match.url || match[0];
        const tiktokText = match.text || tiktokUrl;
        resultArray.push({ type: 'tiktok', value: tiktokUrl, text: tiktokText });
      } else if (match.type === 'googlemaps') {
        const googleMapsUrl = match.url || match[0];
        const googleMapsText = match.text || googleMapsUrl;
        resultArray.push({ type: 'googlemaps', value: googleMapsUrl, text: googleMapsText });
      }
      lastIndex = match.index + match[0].length;
    });
    if (lastIndex < text.length) {
      const after = text.slice(lastIndex);
      if (after.trim()) resultArray.push({ type: 'text', value: after });
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
          if (part.type === 'link') {
            if (isYoutubeLink(part.value)) return <YouTubeLinkRenderer key={i} href={part.value}>{part.text}</YouTubeLinkRenderer>;
            if (isTikTokLink(part.value)) return <TikTokLinkRenderer key={i} href={part.value}>{part.text}</TikTokLinkRenderer>;
            return <a key={i} href={part.value} target="_blank" rel="noopener noreferrer">{part.text}</a>;
          }
          if (part.type === 'text') {
            const v = part.value;
            if (!v.trim() && v !== '\n') return null;
            let cleanedValue = v.replace(/^\s*[\*\-\+]\s*$/, '').trim();
            cleanedValue = cleanedValue.replace(/^:\s*/gm, '');
            if (!cleanedValue) return null;
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
