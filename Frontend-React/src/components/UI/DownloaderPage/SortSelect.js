import React, { useRef, useState } from 'react';
import { ChevronDown } from 'lucide-react';

const options = [
  { value: 'lastModified', labelKey: 'bestMatch' },
  { value: 'downloads', labelKey: 'mostDownloaded' },
  { value: 'likes', labelKey: 'mostPopular' },
  { value: 'createdAt', labelKey: 'mostRecent' },
];

export default function SortSelect({ sortBy, setSortBy, strings }) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef();

  // Cierra el menú si se hace click fuera
  React.useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Accesibilidad: navegación con teclado
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      setOpen(o => !o);
      e.preventDefault();
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  };

  return (
    <div className="custom-select-wrapper" ref={wrapperRef} style={{ position: 'relative', minWidth: 120 }}>
      <button
        className="custom-select-selected"
        style={{ background: 'linear-gradient(135deg, #3A455B, #4A3B6B)', border: '2px solid var(--border-light)', borderRadius: 8, color: 'var(--text-primary)', fontSize: 12, padding: '6px 32px 6px 10px', position: 'relative', cursor: 'pointer', minWidth: 120, width: '100%', textAlign: 'left' }}
        aria-haspopup="listbox"
        aria-expanded={open}
        tabIndex={0}
        onClick={() => setOpen(o => !o)}
        onKeyDown={handleKeyDown}
      >
        {(() => {
          const opt = options.find(o => o.value === sortBy);
          return strings[opt?.labelKey] || strings.bestMatch;
        })()}
        <ChevronDown size={16} style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: 'var(--accent-primary)' }} />
      </button>
      {open && (
        <ul
          className="custom-select-dropdown"
          style={{ position: 'absolute', zIndex: 20, background: 'linear-gradient(135deg, #3A455B, #4A3B6B)', border: '2px solid var(--border-light)', borderRadius: 8, marginTop: 2, minWidth: 120, boxShadow: '0 4px 16px #0002', listStyle: 'none', padding: 0, margin: 0 }}
          role="listbox"
        >
          {options.map(opt => (
            <li
              key={opt.value}
              className="custom-select-option"
              style={{ padding: '7px 12px', cursor: 'pointer', color: 'var(--text-primary)', background: sortBy === opt.value ? 'var(--accent-primary-light)' : 'transparent' }}
              tabIndex={0}
              role="option"
              aria-selected={sortBy === opt.value}
              onClick={() => { setSortBy(opt.value); setOpen(false); }}
              onKeyDown={e => {
                if (e.key === 'Enter' || e.key === ' ') {
                  setSortBy(opt.value); setOpen(false);
                }
              }}
            >
              {strings[opt.labelKey]}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
