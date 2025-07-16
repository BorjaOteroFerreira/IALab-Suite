import React, { useState } from 'react';
import Joyride from 'react-joyride';

const steps = [
  {
    target: '.model-select',
    content: 'Selecciona aquí el modelo que quieres usar en el chat.',
    placement: 'right',
    disableBeacon: true,
  },
  {
    target: '.param-temperature',
    content: 'La temperatura controla la creatividad de las respuestas. Valores altos generan respuestas más variadas.',
    placement: 'right',
    disableBeacon: true,
  },
  {
    target: '.param-context',
    content: 'El contexto define cuántos tokens (palabras) puede tener la conversación. Un valor mayor permite respuestas más largas.',
    placement: 'right',
    disableBeacon: true,
  },
  {
    target: '.param-system-message',
    content: 'El mensaje del sistema define el comportamiento y personalidad del modelo. Puedes personalizarlo aquí.',
    placement: 'right',
    disableBeacon: true,
  },
  {
    target: '.param-gpu-layers',
    content: 'Las capas GPU determinan cuántas capas del modelo se ejecutan en la GPU. -1 significa que se usan todas las capas posibles.',
    placement: 'right',
    disableBeacon: true,
  },
  {
    target: '.apply-btn',
    content: 'Pulsa aquí para aplicar los cambios y usar el modelo con los parámetros seleccionados.',
    placement: 'right',
    disableBeacon: true,
  },
];

export default function ConfigSidebarTour({ onClose }) {
  // Solo mostrar el tour la primera vez que se visita la página
  const [run, setRun] = useState(() => {
    return !localStorage.getItem('configSidebarTourSeen');
  });

  const handleJoyrideCallback = (data) => {
    if (data.status === 'finished' || data.status === 'skipped') {
      localStorage.setItem('configSidebarTourSeen', 'true');
      setRun(false);
      onClose && onClose();
    }
  };

  return (
    <Joyride
      steps={steps}
      run={run}
      continuous
      showSkipButton
      showProgress
      locale={{ back: 'Atrás', close: 'Cerrar', last: 'Finalizar', next: 'Siguiente', skip: 'Saltar' }}
      styles={{ options: { zIndex: 3002 } }}
      callback={handleJoyrideCallback}
    />
  );
}
