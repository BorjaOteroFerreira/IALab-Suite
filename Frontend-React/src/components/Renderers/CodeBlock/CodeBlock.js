import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check } from 'lucide-react';

// Color de acento principal del gradiente
const ACCENT_GREEN = '#6366f1';

function CodeBlock({ code, language }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  return (
    <div style={{ position: 'relative', marginBottom: '2em' }}>
      <SyntaxHighlighter
        language={language || 'plaintext'}
        style={vscDarkPlus}
        showLineNumbers
        customStyle={{ borderRadius: '8px', fontSize: '1em', margin: '1em 0', overflowX: 'auto', paddingBottom: '2.5em', background: '#23272f' }}
      >
        {code}
      </SyntaxHighlighter>
      <button
        style={{
          position: 'absolute',
          right: '12px',
          bottom: '12px',
          background: copied 
            ? 'linear-gradient(120deg, #191a1a 0%, #23272f 100%)' 
            : 'transparent',
          border: 'none',
          borderRadius: '6px',
          padding: '6px',
          cursor: 'pointer',
          zIndex: 2,
          transition: 'background 0.2s'
        }}
        title={copied ? '¡Copiado!' : 'Copiar código'}
        onClick={handleCopy}
      >
        {copied ? <Check size={18} color="#fff" /> : <Copy size={18} color="#bbb" />}
      </button>
      {/* Fix: Añadimos un div vacío para asegurar el flujo y evitar problemas de renderizado con tokens posteriores */}
      <div style={{ clear: 'both', height: 0 }}></div>
    </div>
  );
}

export default CodeBlock;
