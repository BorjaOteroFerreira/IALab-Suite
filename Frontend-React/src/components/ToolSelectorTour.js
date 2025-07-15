import React from 'react';
import Joyride from 'react-joyride';

const steps = [
  {
    target: '.tools-selector-dropdown, .tools-selector-panel',
    content: 'Aquí puedes seleccionar y activar diferentes herramientas y agentes para potenciar tus conversaciones.',
    placement: 'right',
    disableBeacon: true,
  },
  {
    target: '.tools-selector-dropdown .tools-list, .tools-selector-panel .tools-list',
    content: 'Activa o desactiva las herramientas específicas que necesites: calculadora, búsqueda web, generación de imágenes, etc.',
    placement: 'right',
    disableBeacon: true,
  },
];

export default function ToolSelectorTour({ run, onClose }) {
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
