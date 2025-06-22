import './polyfills';
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import './fonts.css';
import './fontLoader';
import App from './App'; // Usando la versión completa con el nuevo diseño

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
