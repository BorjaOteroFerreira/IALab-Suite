import React from 'react';
import './ImageRenderer.css';

function ImageRenderer({ src, alt, href }) {
  return (
    <span className="image-renderer">
      <a
        href={href || src}
        target="_blank"
        rel="noopener noreferrer"
        className="image-renderer-link"
        title={alt || src}
      >
        <img
          src={src}
          alt={alt || ''}
          className="image-renderer-thumb"
          width={128}
          height={128}
          loading="lazy"
          style={{ objectFit: 'cover', borderRadius: 8, background: '#222' }}
        />
      </a>
    </span>
  );
}

export default ImageRenderer;
