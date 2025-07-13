import React, { useState, useRef, useEffect } from 'react';
import { useLanguage } from '../../../context/LanguageContext';

export default function LanguageSelector() {
  const { lang, setLang, availableLangObjects } = useLanguage();
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Cierra el dropdown al hacer clic fuera
  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  const currentLangData = availableLangObjects.find(l => l.code === lang) || { code: lang, name: lang, flag: '🌐' };

  return (
    <div className="custom-lang-dropdown floating-language-selector compact" ref={dropdownRef}>
      <button
        className="lang-dropdown-btn"
        tabIndex={0}
        onClick={() => setOpen(o => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        {currentLangData.flag}
        <span>{currentLangData.code ? currentLangData.code.toUpperCase() : '??'}</span>
        <span className="chevron">▼</span>
      </button>
      {open && (
        <ul className="lang-dropdown-list" role="listbox">
          {availableLangObjects.map(langObj => (
            <li
              key={langObj.code}
              className={`lang-dropdown-item${langObj.code === lang ? ' selected' : ''}`}
              onClick={() => { setLang(langObj.code); setOpen(false); }}
              role="option"
              aria-selected={langObj.code === lang}
            >
              <span>{langObj.flag}</span> {langObj.code.toUpperCase()} <span style={{marginLeft:4, opacity:0.7}}>{langObj.name}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
