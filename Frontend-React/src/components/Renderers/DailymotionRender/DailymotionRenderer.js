import React from 'react';
import './DailymotionRender.css';

// Extrae el ID de video de una URL de Dailymotion
const extractDailymotionVideoId = (url) => {
  // Ejemplo: https://www.dailymotion.com/video/x8c6ejy
  const pattern = /dailymotion\.com\/video\/([\w]+)/;
  const match = url.match(pattern);
  return match ? match[1] : null;
};

// Componente para renderizar el iframe de Dailymotion
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

// Renderizador de enlaces para Dailymotion
export const DailymotionLinkRenderer = ({ href, children }) => {
  const videoId = extractDailymotionVideoId(href);
  if (videoId) {
    // Si el texto es igual al href o es la misma URL de Dailymotion
    if (!children || (typeof children === 'string' && children.trim() === href.trim())) {
      return <DailymotionEmbed videoId={videoId} />;
    }
    // Si el texto es una URL de Dailymotion y su videoId es igual
    if (
      typeof children === 'string' &&
      extractDailymotionVideoId(children.trim()) === videoId
    ) {
      return <DailymotionEmbed videoId={videoId} />;
    }
    // Si el texto es diferente, muestra el embed y el enlace con el texto
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
