import './polyfills';
import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles/index.css';
import './styles/fonts.css';
import './styles/github-dark.css';
import './styles/safari-mobile-fix.css';
import './fontLoader';
import App from './App'; 

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
