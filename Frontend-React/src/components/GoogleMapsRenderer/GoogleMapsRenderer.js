import React from 'react';

function GoogleMapsRenderer({ url, alt }) {
  if (!url || typeof url !== 'string') return null;
  // Extraer solo la parte base de la URL para el iframe
  // Google Maps permite embeber con /maps?q=lat,long&output=embed
  let embedUrl = url;
  if (url.includes('/maps?q=')) {
    embedUrl = url.replace('/maps?q=', '/maps?q=').replace(/(&amp;|&)output=embed/, '');
    if (!embedUrl.includes('output=embed')) {
      embedUrl += (embedUrl.includes('?') ? '&' : '?') + 'output=embed';
    }
  }
  return (
    <div className="google-maps-embed-container" style={{margin: '10px 0', borderRadius: 8, overflow: 'hidden', background: '#222'}}>
      <iframe
        src={embedUrl}
        title={alt || 'Mapa de Google Maps'}
        width="100%"
        height="300"
        style={{ border: 0, borderRadius: 8, width: '100%', minHeight: 200 }}
        allowFullScreen=""
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
      />
    </div>
  );
}

export default GoogleMapsRenderer;
