import React from 'react';
import './YoutubeRender.css';
import { useLanguage } from '../../../context/LanguageContext';

// Función para extraer ID de video de YouTube desde diferentes formatos de URL
const extractYouTubeVideoId = (url) => {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([^&\n?#]+)/,
    /youtube\.com\/watch\?.*v=([^&\n?#]+)$/,
    /youtube\.com\/shorts\/([\w-]+)/ // Soporte para shorts
  ];
  
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) {
      return match[1];
    }
  }
  return null;
};

// Componente para renderizar iframe de YouTube
export const YouTubeEmbed = ({ videoId }) => {
  return (
    <div className="youtube-embed-container" style={{
      position: 'relative',
      paddingBottom: '56.25%' /* 16:9 aspect ratio */,
      height: 0,
      margin: '1em auto',
      overflow: 'hidden',
      maxWidth: '480px',
      background: '#000',
      marginTop: '10px',
      marginBottom: '10px',
      borderRadius: '8px'
    }}>
      <iframe
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          border: 'none',
          borderRadius: '8px'
        }}
        src={`https://www.youtube.com/embed/${videoId}`}
        title="Reproductor de YouTube"
        frameBorder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
    </div>
  );
};

// Componente personalizado para enlaces que detecta YouTube - SOLO EMBED
export const LinkRenderer = ({ href, children }) => {
  const { getStrings } = useLanguage();
  const strings = getStrings('youtubeRenderer');
  
  const videoId = extractYouTubeVideoId(href);
  
  if (videoId) {
    return <YouTubeEmbed videoId={videoId} />;
  }
  
  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children || href}
    </a>
  );
};