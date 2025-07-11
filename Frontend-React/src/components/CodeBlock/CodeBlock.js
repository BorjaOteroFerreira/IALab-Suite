import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './CodeBlock.css';
import { useLanguage } from '../../context/LanguageContext';

const CodeBlock = ({ language, children }) => {
  const [copied, setCopied] = useState(false);
  const { getStrings } = useLanguage();
  const strings = getStrings('codeblock');

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(children);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Error al copiar:', err);
    }
  };

  // Detectar el lenguaje si no se proporciona
  const detectedLanguage = language || detectLanguage(children);

  return (
    <div className="code-block">
      <div className="code-header">
        <span className="code-language">{detectedLanguage}</span>
        <button 
          onClick={copyToClipboard}
          className={`copy-button ${copied ? 'copied' : ''}`}
          title={copied ? strings.copied : strings.copy}
        >
          {copied ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke="currentColor" strokeWidth="2" fill="none"/>
              <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" stroke="currentColor" strokeWidth="2" fill="none"/>
            </svg>
          )}
        </button>
      </div>
      <SyntaxHighlighter
        language={detectedLanguage}
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          borderRadius: '0 0 8px 8px',
          fontSize: '14px',
          lineHeight: '1.5'
        }}
        showLineNumbers={children.split('\n').length > 10}
        wrapLines={true}
        wrapLongLines={true}
      >
        {children}
      </SyntaxHighlighter>
    </div>
  );
};

// Función para detectar el lenguaje basado en el contenido
const detectLanguage = (code) => {
  const trimmed = code.trim().toLowerCase();
  
  // JavaScript/TypeScript
  if (trimmed.includes('function') || trimmed.includes('const') || trimmed.includes('let') || 
      trimmed.includes('var') || trimmed.includes('=>') || trimmed.includes('console.log')) {
    return 'javascript';
  }
  
  // Python
  if (trimmed.includes('def ') || trimmed.includes('import ') || trimmed.includes('print(') ||
      trimmed.includes('class ') || trimmed.includes('if __name__')) {
    return 'python';
  }
  
  // CSS
  if (trimmed.includes('{') && trimmed.includes(':') && trimmed.includes(';') && 
      (trimmed.includes('color') || trimmed.includes('margin') || trimmed.includes('padding'))) {
    return 'css';
  }
  
  // HTML
  if (trimmed.includes('<') && trimmed.includes('>') && 
      (trimmed.includes('<div') || trimmed.includes('<span') || trimmed.includes('<!DOCTYPE'))) {
    return 'html';
  }
  
  // JSON
  if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || 
      (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
    try {
      JSON.parse(trimmed);
      return 'json';
    } catch (e) {
      // No es JSON válido
    }
  }
  
  // SQL
  if (trimmed.includes('select') || trimmed.includes('insert') || trimmed.includes('update') ||
      trimmed.includes('delete') || trimmed.includes('create table')) {
    return 'sql';
  }
  
  // Bash/Shell
  if (trimmed.startsWith('#!/bin/bash') || trimmed.includes('echo ') || 
      trimmed.includes('cd ') || trimmed.includes('ls ') || trimmed.includes('grep ')) {
    return 'bash';
  }
  
  // React/JSX
  if (trimmed.includes('import React') || trimmed.includes('useState') || 
      trimmed.includes('useEffect') || trimmed.includes('jsx')) {
    return 'jsx';
  }
  
  return 'text';
};

export default CodeBlock;
