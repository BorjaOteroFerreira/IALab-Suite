import React, { useEffect, useRef } from 'react';
import Prism from 'prismjs';
import showdown from 'showdown';
import './Message.css';

// Cargar componentes adicionales de Prism para resaltado de sintaxis
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-markdown';
import 'prismjs/components/prism-jsx';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-sql';

function Message({ role, content, index, isTyping = false }) {
  const messageRef = useRef(null);
  const converter = new showdown.Converter({
    tables: true,
    tasklists: true,
    strikethrough: true,
    emoji: true,
    underline: true
  });
  
  // Convertir markdown a HTML
  const processContent = () => {
    if (!content) return '';
    
    // Reemplazar saltos de línea especiales
    let processedContent = content.replace(/<0x0A>/g, '\n');
    
    // Asegurarse de que los bloques de código tengan formato adecuado
    processedContent = ensureCodeBlockFormatting(processedContent);
    
    // Convertir markdown a HTML
    let htmlContent = converter.makeHtml(processedContent);
    
    return htmlContent;
  };
  
  // Función para asegurar que los bloques de código están bien formateados
  const ensureCodeBlockFormatting = (text) => {
    // Buscar bloques de código que podrían no estar bien formateados
    const codeBlockRegex = /```([a-zA-Z]*)\s*([\s\S]*?)```/g;
    
    // Reemplazar con formato correcto 
    return text.replace(codeBlockRegex, (match, language, code) => {
      // Eliminar primera y última línea vacía del código si existen
      code = code.trim();
      return `\`\`\`${language}\n${code}\n\`\`\``;
    });
  };
  
  // Aplicar resaltado de sintaxis a los bloques de código
  useEffect(() => {
    if (messageRef.current) {
      // Aplicar resaltado a todos los bloques de código
      messageRef.current.querySelectorAll('pre code').forEach((block) => {
        Prism.highlightElement(block);
      });
      
      // Agregar botones de copia a los bloques de código
      messageRef.current.querySelectorAll('pre').forEach((preElement) => {
        if (!preElement.querySelector('.copy-button')) {
          const button = document.createElement('button');
          button.className = 'copy-button';
          button.textContent = 'Copiar';
          button.onclick = () => copyToClipboard(preElement);
          preElement.appendChild(button);
        }
      });
    }
  }, [content]);
  
  // Función para copiar código al portapapeles
  const copyToClipboard = (preElement) => {
    const codeElement = preElement.querySelector('code');
    if (!codeElement) return;
    
    const text = codeElement.textContent || '';
    
    navigator.clipboard.writeText(text).then(
      () => {
        // Cambiar texto del botón temporalmente para indicar éxito
        const button = preElement.querySelector('.copy-button');
        if (button) {
          const originalText = button.textContent;
          button.textContent = '✓ Copiado';
          button.classList.add('copied');
          
          setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
          }, 2000);
        }
      },
      (err) => {
        console.error('Error al copiar texto:', err);
      }
    );
  };
  
  // Determinar clases de estilo para el mensaje
  const messageClass = role === 'user' ? 'user-message' : 'assistant-message';
  const avatarContent = role === 'user' ? '👤' : '🤖';
  
  return (
    <div className={`message-wrapper ${messageClass} ${isTyping ? 'typing' : ''}`}>
      <div className="message-avatar">
        <div className="avatar-content">
          {avatarContent}
        </div>
      </div>
      
      <div className="message-content">
        <div 
          ref={messageRef} 
          className="message-text"
          dangerouslySetInnerHTML={{ __html: processContent() }}
        />
        
        {isTyping && (
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}
      </div>
    </div>
  );
}

export default Message;
