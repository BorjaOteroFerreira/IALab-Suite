import React from 'react';
import './DailymotionRender.css';

// Extrae el ID de video de una URL de Dailymotion
const extractDailymotionVideoId = (url) => {
  const pattern = /dailymotion\.com\/video\/([\w]+)/;
  const match = url.match(pattern);
  return match ? match[1] : null;
};

// Extrae el ID de playlist de una URL de Dailymotion
const extractDailymotionPlaylistId = (url) => {
  const pattern = /dailymotion\.com\/playlist\/([\w]+)/;
  const match = url.match(pattern);
  return match ? match[1] : null;
};

// Componente para renderizar el iframe de Dailymotion Video
export const DailymotionEmbed = ({ videoId }) => (
  <div className="dailymotion-embed-container">
    <iframe
      className="dailymotion-embed-iframe"
      src={`https://www.dailymotion.com/embed/video/${videoId}`}
      title="Reproductor de Dailymotion"
      allow="autoplay; encrypted-media"
      allowFullScreen
    />
  </div>
);

// Componente para renderizar el iframe de Dailymotion Playlist
export const DailymotionPlaylistEmbed = ({ playlistId }) => (
  <div className="dailymotion-embed-container">
    <iframe
      className="dailymotion-embed-iframe"
      src={`https://www.dailymotion.com/embed/playlist/${playlistId}`}
      title="Playlist de Dailymotion"
      allow="autoplay; encrypted-media"
      allowFullScreen
    />
  </div>
);

// Renderizador de enlaces para Dailymotion
export const DailymotionLinkRenderer = ({ href, children }) => {
  const videoId = extractDailymotionVideoId(href);
  const playlistId = extractDailymotionPlaylistId(href);
  if (playlistId) {
    if (!children || (typeof children === 'string' && children.trim() === href.trim())) {
      return <DailymotionPlaylistEmbed playlistId={playlistId} />;
    }
    if (
      typeof children === 'string' &&
      extractDailymotionPlaylistId(children.trim()) === playlistId
    ) {
      return <DailymotionPlaylistEmbed playlistId={playlistId} />;
    }
    return (
      <>
        <DailymotionPlaylistEmbed playlistId={playlistId} />
        <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
      </>
    );
  }
  if (videoId) {
    if (!children || (typeof children === 'string' && children.trim() === href.trim())) {
      return <DailymotionEmbed videoId={videoId} />;
    }
    if (
      typeof children === 'string' &&
      extractDailymotionVideoId(children.trim()) === videoId
    ) {
      return <DailymotionEmbed videoId={videoId} />;
    }
    return (
      <>
        <DailymotionEmbed videoId={videoId} />
        <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
      </>
    );
  }
  // Si no es un enlace de Dailymotion, comportamiento normal
  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children || href}
    </a>
  );
};
