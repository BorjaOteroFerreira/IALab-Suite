import React from 'react';
import { useLanguage } from '../../../context/LanguageContext';
import './MessageList.css';

function ShortcutsLegend({ floating = false }) {
  const { getStrings } = useLanguage();
  const shortcuts = getStrings('shortcuts');
  return (
    <div className={floating ? "shortcuts-legend-floating" : "shortcuts-legend"}>
      <ul className="shortcuts-list">
        <li><kbd>{shortcuts.sendMessageShortcut}</kbd> - {shortcuts.sendMessage}</li>
        <li><kbd>{shortcuts.newLineShortcut}</kbd> - {shortcuts.newLine}</li>
        <li><kbd>{shortcuts.newChatShortcut}</kbd> - {shortcuts.newChat}</li>
        <li><kbd>{shortcuts.showAllShortcut}</kbd> - {shortcuts.showAll}</li>
        <li><kbd>{shortcuts.toggleConfigSidebarShortcut}</kbd> - {shortcuts.toggleConfigSidebar}</li>
        <li><kbd>{shortcuts.toggleChatSidebarShortcut}</kbd> - {shortcuts.toggleChatSidebar}</li>
        <li><kbd>{shortcuts.toggleHeaderShortcut}</kbd> - {shortcuts.toggleHeader}</li>
        <li><kbd>{shortcuts.closeAllShortcut}</kbd> - {shortcuts.closeAll}</li>
        <li><kbd>{shortcuts.devConsoleShortcut}</kbd> - {shortcuts.devConsole}</li>
        <li><kbd>{shortcuts.openToolSelectorShortcut}</kbd> - {shortcuts.openToolSelector}</li>
        <li><kbd>{shortcuts.toggleToolsShortcut}</kbd> - {shortcuts.toggleTools}</li>
      </ul>
    </div>
  );
}

export default ShortcutsLegend;
