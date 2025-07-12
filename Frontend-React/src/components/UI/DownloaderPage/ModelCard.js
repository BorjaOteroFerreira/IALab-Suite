import React, { useRef } from 'react';
import PropTypes from 'prop-types';
import { ChevronRight } from 'lucide-react';

const ModelCard = React.memo(({
  model,
  isSelected,
  isFocused,
  onClick,
  onKeyDown,
  tabIndex,
  readmePreview,
  badges,
  strings = {}, // strings opcional para internacionalización
  ...props
}) => {
  const cardRef = useRef();
  const { size, quant, type, updatedAt, downloads } = badges || {};
  const tags = model.tags || [];
  const hasVision = tags.some(t => t.toLowerCase().includes('vision') || t.toLowerCase().includes('mmproj'));
  const hasTools = tags.some(t => t.toLowerCase().includes('tools'));
  const hasReasoning = tags.some(t => t.toLowerCase().includes('reasoning'));
  const repo = model.id.split('/')[0];
  return (
    <div
      ref={cardRef}
      className={`model-card model-card-modern${isSelected ? ' selected' : ''}${isFocused ? ' focused' : ''}`}
      tabIndex={tabIndex}
      onClick={onClick}
      onKeyDown={onKeyDown}
      aria-selected={isSelected}
      role="option"
      style={{
        boxShadow: 'none',
        border: 'none',
        borderBottom: '1px solid var(--border-card)',
        borderRadius: 0,
        margin: 0,
        padding: 'var(--card-padding)',
        minHeight: 54,
        alignItems: 'center',
        display: 'flex',
        transition: 'background 0.18s',
        overflow: 'hidden',
        cursor: 'pointer',
        outline: isFocused ? '2px solid var(--accent-primary)' : 'none',
      }}
      {...props}
    >
      <div className="model-card-info" style={{ minWidth: 0, flex: 1 }}>
        <div className="model-card-name" style={{ fontWeight: 700, fontSize: '1.08rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {model.id.split('/')[1] || model.id}
          {hasVision && <span className="model-meta-vision" style={{ marginLeft: 4 }}>{strings.vision || 'visión'}</span>}
          {hasTools && <span className="model-meta-tools" style={{ marginLeft: 4 }}>{strings.tools || 'tools'}</span>}
          {hasReasoning && <span className="model-meta-reasoning" style={{ marginLeft: 4 }}>{strings.reasoning || 'reasoning'}</span>}
        </div>
        <div className="model-card-meta" style={{ display: 'flex', gap: 7, marginTop: 2, fontSize: 13, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {size && <span className="model-meta-size">{size}</span>}
          {quant && <span className="model-meta-quantization">{quant}</span>}
          {type && <span className="model-meta-type">{type}</span>}
          {downloads && <span className="model-meta-downloads">⬇️ {downloads}</span>}
          {updatedAt && <span className="model-meta-updated">🕒 {updatedAt}</span>}
        </div>
        <div className="model-card-repo" style={{ color: 'var(--accent-secondary)', fontSize: 12, marginTop: 2, fontWeight: 500, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {repo}
        </div>
        {readmePreview && (
          <div className="model-card-readme-preview" style={{ color: 'var(--text-secondary)', fontSize: 12, marginTop: 6, maxHeight: 36, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'pre-line' }}>
            {readmePreview}
          </div>
        )}
      </div>
      <ChevronRight size={18} style={{ opacity: 0.5, marginLeft: 8 }} />
      {isSelected && <div className="selected-indicator">✓</div>}
    </div>
  );
});

ModelCard.propTypes = {
  model: PropTypes.shape({
    id: PropTypes.string.isRequired,
    tags: PropTypes.array,
    readmePreview: PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.element
    ]),
  }).isRequired,
  isSelected: PropTypes.bool,
  isFocused: PropTypes.bool,
  onClick: PropTypes.func,
  onKeyDown: PropTypes.func,
  tabIndex: PropTypes.number,
  readmePreview: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.element
  ]),
  badges: PropTypes.shape({
    size: PropTypes.string,
    quant: PropTypes.string,
    type: PropTypes.string,
    updatedAt: PropTypes.string,
    downloads: PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.number
    ]),
    vision: PropTypes.bool
  }),
  strings: PropTypes.object
};

export default ModelCard;
