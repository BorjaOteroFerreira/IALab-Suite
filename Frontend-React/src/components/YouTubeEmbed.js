import React from 'react';
import './YouTubeEmbed.css';

const YouTubeEmbed = ({ videoIds }) => {
  if (!videoIds || !Array.isArray(videoIds) || videoIds.length === 0) {
    return null;
  }

  return (
    <div className="youtube-embeds">
      <div className="youtube-header">
        <h4>Videos relacionados:</h4>
      </div>
      <div className="youtube-grid">
        {videoIds.map((videoId, index) => (
          <div key={`${videoId}-${index}`} className="youtube-container">
            <iframe
              src={`https://www.youtube.com/embed/${videoId}`}
              title={`Video de YouTube ${index + 1}`}
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              loading="lazy"
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default YouTubeEmbed;
