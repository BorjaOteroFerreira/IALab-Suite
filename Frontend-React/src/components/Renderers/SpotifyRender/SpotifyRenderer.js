import React from 'react';
import './SpotifyRender.css';

// Función para extraer tipo y ID de recurso de Spotify desde diferentes formatos de URL
const extractSpotifyResource = (url) => {
  let cleanUrl = url ? url.trim() : '';
  // Elimina puntuación y paréntesis finales comunes
  cleanUrl = cleanUrl.replace(/[)\]\.,!?:;"']+$/g, '');
  const pattern = /spotify\.com\/(?:[a-zA-Z0-9\-]+\/)?(track|album|playlist|artist)\/([a-zA-Z0-9]+)(\?si=[\w-]+)?/;
  const match = cleanUrl.match(pattern);
  if (match) {
    return { type: match[1], id: match[2] };
  }
  return null;
};

// Componente para renderizar iframe de Spotify
export const SpotifyEmbed = ({ type, id }) => {
  if (!type || !id) return null;
  // Altura según tipo
  const height = type === 'track' ? 80 : 352;
  return (
    <div className="spotify-embed-container">
      <iframe
        src={`https://open.spotify.com/embed/${type}/${id}?utm_source=generator&theme=0`}
        width="100%"
        height={height}
        frameBorder="0"
        allowTransparency="true"
        allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
        loading="lazy"
        title={`Spotify ${type}`}
      />
    </div>
  );
};

// Componente personalizado para enlaces que detecta Spotify - SOLO EMBED
export const LinkRenderer = ({ href, children }) => {
  // Usar la función extractSpotifyResource local en lugar de cleanLink
  const resource = extractSpotifyResource(href);
  
  if (resource) {
    // Si children es igual al href (texto y enlace son idénticos)
    if (!children || (typeof children === 'string' && extractSpotifyResource(children) && 
        extractSpotifyResource(children).id === resource.id && 
        extractSpotifyResource(children).type === resource.type)) {
      return <SpotifyEmbed type={resource.type} id={resource.id} />;
    }
    
    // Si el texto es diferente y no es una URL de Spotify igual, muestra el embed y el enlace con el texto
    return (
      <>
        <SpotifyEmbed type={resource.type} id={resource.id} />
        <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
      </>
    );
  }
  
  // Si no es un enlace de Spotify, comportamiento normal
  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children || href}
    </a>
  );
};

// Función para limpiar el markdown de Spotify (usada en useMessageList)
export const cleanSpotifyMarkdown = (md) => {
  return md.replace(
    /\[([^\]]+)\]\((https?:\/\/(open\.)?spotify\.com\/(track|album|playlist|artist)\/[a-zA-Z0-9]+(\?si=[\w-]+)?)\)/gi,
    (match, text, url) => {
      // Si el texto es igual a la URL, solo devolver la URL
      if (text.trim() === url.trim()) {
        return url;
      }
      // Si el texto es diferente, mantener el formato markdown
      return match;
    }
  );
};