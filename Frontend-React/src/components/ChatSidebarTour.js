import React from 'react';
import Joyride from 'react-joyride';

const steps = [
  {
    target: '.chat-sidebar .sidebar-header',
    content: 'En la parte superior puedes ver el título y acceder al historial de conversaciones guardadas.',
    placement: 'top',
    disableBeacon: true,
  },
  {
    target: '.chat-sidebar .chat-list .chat-item:first-child',
    content: 'Haz clic en la primera conversación de la lista para cargarla y continuar donde la dejaste.',
    placement: 'left',
    disableBeacon: true,
  },
  {
    target: '.chat-sidebar .delete-btn, .chat-sidebar .chat-item .delete-btn',
    content: 'Pulsa el icono de papelera para eliminar una conversación guardada.',
    placement: 'left',
    disableBeacon: true,
  },
];

export default function ChatSidebarTour({ run, onClose }) {
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
