import React from 'react';
import Joyride from 'react-joyride';

const steps = [
  {
    target: '.downloader-page',
    content: 'Este es el gestor de descargas. Aquí puedes ver los modelos disponibles para descargar.',
    placement: 'center',
    disableBeacon: true,
  },
  {
    target: '.downloader-page .model-list',
    content: 'Aquí se muestra la lista de modelos GGUF disponibles. Puedes buscar y filtrar modelos.',
    placement: 'center',
    disableBeacon: true,
  },
  {
    target: '.downloader-page .download-btn',
    content: 'Pulsa este botón para descargar el modelo seleccionado.',
    placement: 'center',
    disableBeacon: true,
  },
];

export default function DownloaderTour({ run, onClose }) {
  return (
    <Joyride
      steps={steps}
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
