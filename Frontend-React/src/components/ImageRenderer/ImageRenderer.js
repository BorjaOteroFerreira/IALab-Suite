import React from 'react';
import './ImageRenderer.css';
import { useLanguage } from '../../context/LanguageContext';

function ImageRenderer({ src, alt, href }) {
  const { getStrings } = useLanguage();
  const strings = getStrings('misc');
  const altText = alt || strings.imageAlt;
  return (
    <span className="image-renderer">
      <a
        href={href || src}
        target="_blank"
        rel="noopener noreferrer"
        className="image-renderer-link"
        title={altText}
      >
        <img
          src={src}
          alt={altText}
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
