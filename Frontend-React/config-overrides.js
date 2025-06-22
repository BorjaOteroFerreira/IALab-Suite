module.exports = function override(config, env) {
  // Añadir soporte para archivos de fuentes
  config.module.rules.push({
    test: /\.(woff|woff2|eot|ttf|otf)$/,
    use: [
      {
        loader: 'file-loader',
        options: {
          name: '[name].[ext]',
          outputPath: 'static/fonts/',
          publicPath: '/static/fonts/'
        }
      }
    ]
  });
  
  // Verificar NODE_ENV y aplicar configuraciones específicas
  if (env === 'production') {
    console.log('Configurando para producción...');
  } else {
    console.log('Configurando para desarrollo...');
  }
  
  return config;
};
