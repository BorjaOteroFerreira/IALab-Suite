import React from 'react';
import Joyride from 'react-joyride';

const tourSteps = [
  {
    target: '.header',
    content: 'Aquí puedes ver y controlar las herramientas, tokens y preferencias del chat.',
    placement: 'bottom',
  },
  {
    target: '.main-flex-content',
    content: 'Este es el área principal donde aparecen los mensajes y puedes navegar entre chats.',
    placement: 'top',
  },
  {
    target: '.input-area-wrapper',
    content: 'Escribe tus preguntas o comandos aquí y presiona Enter para enviar.',
    placement: 'top',
  },
  {
    target: '.floating-downloader-btn-global',
    content: 'Descarga modelos GGUF desde aquí.',
    placement: 'top', // Cambiado a 'top' para que el popup no tape el botón
  },
  {
    target: '.floating-language-selector-global',
    content: 'Cambia el idioma de la interfaz fácilmente.',
    placement: 'top', // Cambiado a 'top' para que el popup no tape el botón
  },
  {
    target: '.dev-console',
    content: 'Abre la consola de desarrollo para ver logs y mensajes técnicos.',
    placement: 'top', // Cambiado a 'top' para que el popup no tape el botón
  },
];

export default function AppTour({ run, onClose }) {
  return (
    <Joyride
      steps={tourSteps}
      run={run}
      continuous
      showSkipButton
      showProgress
      locale={{ back: 'Atrás', close: 'Cerrar', last: 'Finalizar', next: 'Siguiente', skip: 'Saltar' }}
      styles={{ options: { zIndex: 3002 } }}
      callback={(data) => {
        if (data.status === 'finished' || data.status === 'skipped') {
          onClose && onClose();
        }
      }}
    />
  );
}
