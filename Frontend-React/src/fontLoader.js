// Este archivo requiere las fuentes directamente para que webpack las incluya
import helveticaNeueLightFont from './styles/fonts/HelveticaNeueLight.otf';
import helveticaNeueUltraLightFont from './styles/fonts/HelveticaNeueUltraLight.otf';

export const fonts = {
  HelveticaNeueLight: helveticaNeueLightFont,
  HelveticaNeueUltraLight: helveticaNeueUltraLightFont
};

export const loadFonts = () => {
  const fontStyles = document.createElement('style');
  fontStyles.textContent = `
    @font-face {
      font-family: 'HelveticaNeueLight';
      src: url('${fonts.HelveticaNeueLight}') format('opentype');
      font-weight: normal;
      font-style: normal;
      font-display: swap;
    }
    
    @font-face {
      font-family: 'HelveticaNeueUltraLight';
      src: url('${fonts.HelveticaNeueUltraLight}') format('opentype');
      font-weight: normal;
      font-style: normal;
      font-display: swap;
    }
  `;
  
  document.head.appendChild(fontStyles);
  console.log('Fuentes cargadas dinámicamente');
};

loadFonts();
