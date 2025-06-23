import React from 'react';
import './YoutubeRender.css';

// Función para extraer ID de video de YouTube desde diferentes formatos de URL
const extractYouTubeVideoId = (url) => {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([^&\n?#]+)/,
    /youtube\.com\/watch\?.*v=([^&\n?#]+)$/
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
      overflow: 'hidden',
      maxWidth: '100%',
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
        title="YouTube video player"
        frameBorder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
    </div>
  );
};

// Componente personalizado para enlaces que detecta YouTube
export const LinkRenderer = ({ href, children }) => {
  const videoId = extractYouTubeVideoId(href);
  
  if (videoId) {
    return (
      <div>
        <a href={href} target="_blank" rel="noopener noreferrer" className="youtube-link">
          {children || href}
        </a>
        <YouTubeEmbed videoId={videoId} />
      </div>
    );
  }
  
  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children || href}
    </a>
  );
};
