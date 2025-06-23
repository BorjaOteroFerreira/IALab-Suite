const fs = require('fs-extra');
const path = require('path');

// Función para copiar fuentes al directorio build
function copyFontsToPublic() {
  console.log('Copiando fuentes al directorio build...');
  
  // Definir múltiples directorios de origen y destino
  const fontPaths = [
    {
      sourceDir: path.join(__dirname, 'public', 'fonts'),
      targetDir: path.join(__dirname, 'build', 'fonts')
    },
    {
      sourceDir: path.join(__dirname, 'public', 'fonts'),
      targetDir: path.join(__dirname, 'build', 'static', 'fonts')
    },
    {
      sourceDir: path.join(__dirname, 'src', 'styles', 'fonts'), // actualizado a styles/fonts
      targetDir: path.join(__dirname, 'build', 'static', 'media', 'fonts')
    }
  ];

  // Procesar cada par de directorios
  fontPaths.forEach(({ sourceDir, targetDir }) => {
    // Verificar si existe el directorio de origen
    if (!fs.existsSync(sourceDir)) {
      console.log(`El directorio ${sourceDir} no existe, continuando...`);
      return;
    }
    
    // Crear directorio de destino si no existe
    fs.ensureDirSync(targetDir);
    
    // Copiar archivos
    try {
      fs.copySync(sourceDir, targetDir);
      console.log('Fuentes copiadas correctamente a', targetDir);
    } catch (err) {
      console.error(`Error al copiar fuentes a ${targetDir}:`, err);
    }
  });

  // Imprimir mensaje informativo
  console.log('Proceso de copia de fuentes completado');
}

// Ejecutar la función
copyFontsToPublic();
