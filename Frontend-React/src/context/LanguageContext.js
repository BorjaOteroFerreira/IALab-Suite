import React, { createContext, useContext, useState, useMemo } from 'react';

// Mapeo de banderas y nombres
const LANG_META = {
  es: { name: 'Español', flag: '🇪🇸' },
  en: { name: 'English', flag: '🇬🇧' },
  it: { name: 'Italiano', flag: '🇮🇹' },
  fr: { name: 'Français', flag: '🇫🇷' },
  pt: { name: 'Português', flag: '🇵🇹' },
  de: { name: 'Deutsch', flag: '🇩🇪' }
};

// Detecta los idiomas por los archivos en src/strings/*/*.js usando require.context
const req = require.context('../strings', true, /([a-zA-Z\-]{2,5})\/.*\.js$/);
const langSet = new Set();
req.keys().forEach((key) => {
  const match = key.match(/\.\/([a-zA-Z\-]{2,5})\/(.+)\.js$/);
  if (!match) return;
  langSet.add(match[1].toLowerCase());
});
const availableLangs = Array.from(langSet);
const availableLangObjects = availableLangs.map(code => ({
  code,
  name: LANG_META[code]?.name || code,
  flag: LANG_META[code]?.flag || '🌐'
}));

// Construir el objeto de strings: { [lang]: { [namespace]: strings } }
const strings = {};
req.keys().forEach((key) => {
  const match = key.match(/\.\/([a-zA-Z\-]{2,5})\/(.+)\.js$/);
  if (!match) return;
  const lang = match[1].toLowerCase();
  const ns = match[2].replace(/^\w+_/, '');
  if (!strings[lang]) strings[lang] = {};
  strings[lang][ns] = req(key).default;
});

const LanguageContext = createContext({
  lang: 'es',
  setLang: () => {},
  getStrings: (ns = 'general') => strings['es']['general'],
  availableLangs: ['es'],
  availableLangObjects: []
});

export const LanguageProvider = ({ children }) => {
  const [lang, setLang] = useState('es');

  // Memoiza para evitar recalcular en cada render
  const value = useMemo(() => ({
    lang,
    setLang,
    availableLangs,
    availableLangObjects,
    getStrings: (ns = 'general') => {
      // Fallback robusto: idioma > español > objeto vacío
      return (strings[lang] && strings[lang][ns]) || (strings['es'] && strings['es'][ns]) || {};
    }
  }), [lang]);

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);
