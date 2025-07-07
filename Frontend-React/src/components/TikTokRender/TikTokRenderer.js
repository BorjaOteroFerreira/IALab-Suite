import React from 'react';
import './TikTokRender.css';

// Función para extraer ID de video de TikTok desde diferentes formatos de URL
const extractTikTokVideoId = (url) => {
  // Ejemplo de URL: https://www.tiktok.com/@usuario/video/1234567890123456789
  const pattern = /tiktok\.com\/@[\w.-]+\/video\/(\d+)/;
  const match = url.match(pattern);
  return match ? match[1] : null;
};

// Limpia enlaces markdown redundantes de TikTok
export const cleanTikTokMarkdown = md => md.replace(
  /\[([^\]]+)\]\((https?:\/\/(www\.)?tiktok\.com\/@[\w.-]+\/video\/\d+)\)/gi,
  (match, text, url) => {
    // Si el texto es igual al enlace o el texto es una URL de TikTok al mismo video, elimina el texto redundante
    const textId = extractTikTokVideoId(text.trim());
    const urlId = extractTikTokVideoId(url.trim());
    if (text.trim() === url.trim() || (textId && urlId && textId === urlId)) return url;
    return match;
  }
);

// Componente para renderizar iframe de TikTok
export const TikTokEmbed = ({ videoId }) => {
  return (
    <div className="tiktok-embed-container">
      <iframe
        className="tiktok-embed-iframe"
        src={`https://www.tiktok.com/embed/v2/${videoId}`}
        title="TikTok video player"
        allow="autoplay; encrypted-media"
        allowFullScreen
      />
    </div>
  );
};

// Componente personalizado para enlaces que detecta TikTok - SOLO EMBED
export const LinkRenderer = ({ href, children }) => {
  const videoId = extractTikTokVideoId(href);
  // Si el enlace es de TikTok
  if (videoId) {
    // Si children es igual al href (texto y enlace son idénticos)
    if (!children || (typeof children === 'string' && children.trim() === href.trim())) {
      return <TikTokEmbed videoId={videoId} />;
    }
    // Si children es una URL de TikTok y su videoId es igual al del href (aunque tengan diferente longitud por parámetros, etc)
    if (
      typeof children === 'string' &&
      extractTikTokVideoId(children.trim()) === videoId
    ) {
      return <TikTokEmbed videoId={videoId} />;
    }
    // Si el texto es diferente y no es una URL de TikTok igual, muestra el embed y el enlace con el texto
    return (
      <>
        <TikTokEmbed videoId={videoId} />
        <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
      </>
    );
  }
  // Si no es un enlace de TikTok, comportamiento normal
  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children || href}
    </a>
  );
};
