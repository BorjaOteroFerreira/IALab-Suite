import React, { createContext, useContext, useState, useMemo } from 'react';

// Carga dinámica de todos los archivos de strings en src/strings/*/*.js
// Esto requiere Webpack (create-react-app lo soporta)
const req = require.context('../strings', true, /([a-z]{2})\/(.+)\.js$/);

// Construir el objeto de strings: { [lang]: { [namespace]: strings } }
const strings = {};
req.keys().forEach((key) => {
  const match = key.match(/\.\/([a-z]{2})\/(.+)\.js$/);
  if (!match) return;
  const lang = match[1];
  const ns = match[2].replace(/^\w+_/, ''); // elimina prefijo tipo 'en_'
  if (!strings[lang]) strings[lang] = {};
  strings[lang][ns] = req(key).default;
});

const availableLangs = Object.keys(strings);

const LanguageContext = createContext({
  lang: 'en',
  setLang: () => {},
  getStrings: (ns = 'general') => strings['es']['general'],
  availableLangs: ['es']
});

export const LanguageProvider = ({ children }) => {
  const [lang, setLang] = useState('es');

  // Memoiza para evitar recalcular en cada render
  const value = useMemo(() => ({
    lang,
    setLang,
    availableLangs,
    getStrings: (ns = 'general') => {
      // Fallback robusto: idioma > inglés > objeto vacío
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
