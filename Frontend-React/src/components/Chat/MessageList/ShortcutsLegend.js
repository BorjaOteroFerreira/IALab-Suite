import React from 'react';
import { useLanguage } from '../../../context/LanguageContext';
import './MessageList.css';

function ShortcutsLegend({ floating = false }) {
  const { getStrings } = useLanguage();
  const shortcuts = getStrings('shortcuts');
  return (
    <div className={floating ? "shortcuts-legend-floating" : "shortcuts-legend"}>
      <ul className="shortcuts-list">
        <li><kbd>{shortcuts.devConsoleShortcut}</kbd> - {shortcuts.devConsole}</li>
        <li><kbd>{shortcuts.sendMessageShortcut}</kbd> - {shortcuts.sendMessage}</li>
        <li><kbd>{shortcuts.newLineShortcut}</kbd> - {shortcuts.newLine}</li>
        <li><kbd>{shortcuts.focusInputShortcut}</kbd> - {shortcuts.focusInput}</li>
      </ul>
    </div>
  );
}

export default ShortcutsLegend;
