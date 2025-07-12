// Solo función de limpieza, sin efecto de reproducción automática
function cleanTextForTTS(text) {
  if (!text) return '';
  // Elimina etiquetas HTML
  let cleaned = text.replace(/<[^>]+>/g, '');
  // Elimina enlaces (http/https)
  cleaned = cleaned.replace(/https?:\/\/\S+/g, '');
  // Elimina markdown de imágenes y enlaces
  cleaned = cleaned.replace(/!\[[^\]]*\]\([^)]*\)/g, ''); // imágenes
  cleaned = cleaned.replace(/\[[^\]]*\]\([^)]*\)/g, ''); // enlaces
  // Elimina encabezados markdown tipo ####
  cleaned = cleaned.replace(/\n?#+\s*/g, '');
  // Elimina emojis
  cleaned = cleaned.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '');
  // Elimina todos los caracteres especiales excepto letras, números y espacios
  cleaned = cleaned.replace(/[^\p{L}\p{N}\s\.]/gu, '');
  // Elimina etiquetas tipo /think ... /think
  cleaned = cleaned.replace(/\/think[\s\S]*?\/think/g, '');
  // Elimina saltos de línea excesivos
  cleaned = cleaned.replace(/\n{2,}/g, '. ');
  // Elimina espacios extra
  cleaned = cleaned.replace(/\s{2,}/g, ' ');
  return cleaned.trim();
}

export default cleanTextForTTS;
