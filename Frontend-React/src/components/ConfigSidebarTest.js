import React from 'react';

const ConfigSidebarTest = ({ visible, onClose }) => {
  console.log('🟢 ConfigSidebarTest renderizado');
  
  if (!visible) return null;
  
  return (
    <div className="config-sidebar">
      <h3>Test ConfigSidebar</h3>
      <button onClick={onClose}>Cerrar</button>
    </div>
  );
};

export default ConfigSidebarTest;
