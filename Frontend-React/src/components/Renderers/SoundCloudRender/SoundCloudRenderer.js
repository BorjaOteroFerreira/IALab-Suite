import React from 'react';
import { useLanguage } from '../../../context/LanguageContext';
import { useMessageList } from '../../../hooks/useMessageList';

// Función para extraer la URL de track de SoundCloud desde diferentes formatos de enlace
const extractSoundCloudTrackUrl = (url) => {
  // Ejemplo de URL: https://soundcloud.com/usuario/trackname
  const pattern = /https?:\/\/(www\.)?soundcloud\.com\/[\w-]+\/[\w-]+/;
  const match = url.match(pattern);
  return match ? match[0] : null;
};

// Limpia enlaces markdown redundantes de SoundCloud
export const cleanSoundCloudMarkdown = md => md.replace(
  /\[([^\]]+)\]\((https?:\/\/(www\.)?soundcloud\.com\/[\w-]+\/[\w-]+)\)/gi,
  (match, text, url) => {
    // Si el texto es igual al enlace o el texto es una URL de SoundCloud igual, elimina el texto redundante
    const textUrl = extractSoundCloudTrackUrl(text.trim());
    const urlTrack = extractSoundCloudTrackUrl(url.trim());
    if (text.trim() === url.trim() || (textUrl && urlTrack && textUrl === urlTrack)) return url;
    return match;
  }
);

// Componente para renderizar iframe de SoundCloud
export const SoundCloudEmbed = ({ trackUrl }) => {
  const { lang } = useLanguage();
  return (
    <div className="soundcloud-embed-container">
      <iframe
        className="soundcloud-embed-iframe"
        width="100%"
        height="166"
        scrolling="no"
        frameBorder="no"
        allow="autoplay"
        src={`https://w.soundcloud.com/player/?url=${encodeURIComponent(trackUrl)}&color=%23ff5500&auto_play=false&hide_related=false&show_comments=true&show_user=true&show_reposts=false&show_teaser=true`}
        title="Reproductor de SoundCloud"
      />
    </div>
  );
};

// Componente personalizado para enlaces que detecta SoundCloud - SOLO EMBED
export const LinkRenderer = ({ href, children }) => {
  const trackUrl = extractSoundCloudTrackUrl(href);
  // Si el enlace es de SoundCloud
  if (trackUrl) {
    // Si children es igual al href (texto y enlace son idénticos)
    if (!children || (typeof children === 'string' && children.trim() === href.trim())) {
      return <SoundCloudEmbed trackUrl={trackUrl} />;
    }
    // Si children es una URL de SoundCloud y su trackUrl es igual al del href
    if (
      typeof children === 'string' &&
      extractSoundCloudTrackUrl(children.trim()) === trackUrl
    ) {
      return <SoundCloudEmbed trackUrl={trackUrl} />;
    }
    // Si el texto es diferente y no es una URL de SoundCloud igual, muestra el embed y el enlace con el texto tal cual
    return (
      <>
        <SoundCloudEmbed trackUrl={trackUrl} />
        <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
      </>
    );
  }
  // Si no es un enlace de SoundCloud, comportamiento normal
  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children || href}
    </a>
  );
};
