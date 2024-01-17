<h1> Proyecto de IA basado en LLama-2</h1>

Actualmente en fase de desarollo, pensado para ejecutar en local
para entornos en producción utilizar otro servidor wsgi

Instalar dependencias

        pip install Flask
        pip install flask_socketio
        pip instal CORS
        pip install llama-cpp-python (mac y linux)

  <h2>llama-cpp-python en windows</h2>

  <h3>Instalar Visual Studio con:</h3>
  <ul>
    <li>C++ CMake tools para Windows.</li>
    <li>C++ herramientas principales</li> 
    <li>Windows 10/11 SDK. (segun tu sistema)</li>
    <li>Descarga e instala CUDA Toolkit 12.3 de la <a href="https://developer.nvidia.com/cuda-12-2-0-download-archive?target_os=Windows">web oficial de nvidia.</a></li>
  </ul>
    
  Verifica la instalación con nvcc --version y nvidia-smi.

  Añade CUDA_PATH ( C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.3) a tus variables de entorno.

  copia los ficheros de from: C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2\extras\visual_studio_integration\MSBuildExtensions
  a la carpeta (Para version enterprise) C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Microsoft\VC\v170\BuildCustomizations
  ó
  (para la version Comunity)C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Microsoft\VC\v170\BuildCustomizations<p>


    set CMAKE_ARGS=-DLLAMA_CUBLAS=on
    set FORCE_CMAKE=1
    pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir --verbose


Descargar <a href="https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q8_0.gguf?download=true">modelo</a> y meterlo en la carpeta models.

Modo de empleo: 


    cd ruta/a/carpeta/del/proyecto
    python3 ./app.py


Se inicia el servidor en el localhost 127.0.0.1:5000




