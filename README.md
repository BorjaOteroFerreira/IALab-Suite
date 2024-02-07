<h1> Proyecto de IA basado en LLama-2</h1>

Actualmente en fase de desarollo, pensado para ejecutar en local
para entornos en producción utilizar otro servidor wsgi

Instalar dependencias

        pip install Flask
        pip install flask_socketio
        pip instal CORS
        pip install llama-cpp-python 

# llama-cpp-python

## Instalación

Hay diferentes opciones para instalar el paquete llama-cpp:

- Uso de CPU
- CPU + GPU (utilizando uno de los muchos backends de BLAS)
- GPU Metal (MacOS con chip Apple Silicon)

## Instalación solo CPU

```
%pip install --upgrade --quiet llama-cpp-python
```

## Instalación con OpenBLAS / cuBLAS / CLBlast

llama.cpp admite múltiples backends de BLAS para un procesamiento más rápido. Use la variable de entorno FORCE_CMAKE=1 para forzar el uso de cmake e instalar el paquete pip para el backend BLAS deseado.

Ejemplo de instalación con backend cuBLAS:

```
!CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip install llama-cpp-python
```

**IMPORTANTE:** Si ya ha instalado la versión solo CPU del paquete, debe reinstalarlo desde cero. Considere el siguiente comando:

```
!CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip install --upgrade --force-reinstall llama-cpp-python --no-cache-dir
```

## Instalación con Metal

llama.cpp admite Apple Silicon como ciudadano de primera clase, optimizado a través de ARM NEON, Accelerate y Metal frameworks. Use la variable de entorno FORCE_CMAKE=1 para forzar el uso de cmake e instalar el paquete pip para el soporte de Metal.

Ejemplo de instalación con soporte de Metal:

```
!CMAKE_ARGS="-DLLAMA_METAL=on" FORCE_CMAKE=1 pip install llama-cpp-python
```

**IMPORTANTE:** Si ya ha instalado una versión solo CPU del paquete, debe reinstalarlo desde cero: considere el siguiente comando:

```
!CMAKE_ARGS="-DLLAMA_METAL=on" FORCE_CMAKE=1 pip install --upgrade --force-reinstall llama-cpp-python --no-cache-dir
```

## Instalación con Windows

Es estable instalar la biblioteca llama-cpp-python compilando desde la fuente. Puede seguir la mayoría de las instrucciones en el repositorio mismo, pero hay algunas instrucciones específicas de Windows que podrían ser útiles.

### Requisitos para instalar llama-cpp-python

- git
- python
- cmake
- Visual Studio Community (asegúrese de instalar esto con la configuración siguiente)
  - Desarrollo de escritorio con C++
  - Desarrollo de Python
  - Desarrollo de Linux embebido con C++

Clona el repositorio de git recursivamente para obtener también el submódulo llama.cpp.

```
git clone --recursive -j8 https://github.com/abetlen/llama-cpp-python.git
```

Abre un símbolo del sistema y establece las siguientes variables de entorno.

```
set FORCE_CMAKE=1
set CMAKE_ARGS=-DLLAMA_CUBLAS=OFF
```

Si tienes una GPU NVIDIA, asegúrate de que DLLAMA_CUBLAS esté configurado como ON.

### Compilación e instalación

Ahora puedes navegar al directorio llama-cpp-python e instalar el paquete.

```
python -m pip install -e .
```

**IMPORTANTE:** Si ya has instalado una versión solo CPU del paquete, debes reinstalarlo desde cero: considera el siguiente comando:

```
!python -m pip install -e . --force-reinstall --no-cache-dir
```

# Uso

Descargar <a href="https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q8_0.gguf?download=true">modelo</a> y meterlo en la carpeta models.

Modo de empleo: 

    cd ruta/a/carpeta/del/proyecto
    python3 ./app.py

Se inicia el servidor en el localhost 127.0.0.1:8080


# Contribución

Las contribuciones (BTC) son bienvenidas:
        
bc1qs52ppg3c8qpmskchhxvrrxc2wragh2qy3rl65d







