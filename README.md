# IA SUITE

### Flask App for Testing LLM Models with Llama.pp Library

This Flask application serves as a platform for testing Language Model (LLM) models using the Llama.pp library. Users can mount and evaluate LLM models in the GGUF format conveniently through the provided template. As an ongoing project, it is continuously being developed with enhancements and code refactoring. 
Stay tuned for updates and additional functionalities!


For production environments use another wsgi server.

## Installation

Install dependencies:

```bash
pip install Flask
```
```bash
pip install flask_socketio
```
```bash
pip install CORS
```

# llama-cpp-python

## Installation

There are different options for installing the llama-cpp package:

- CPU Usage
- CPU + GPU (using one of the many BLAS backends)
- Metal GPU (MacOS with Apple Silicon chip)

### Installation CPU Only

```bash
pip install --upgrade --quiet llama-cpp-python
```

### Installation with OpenBLAS / cuBLAS / CLBlast

llama.cpp supports multiple BLAS backends for faster processing. Use the FORCE_CMAKE=1 environment variable to force the use of cmake and install the pip package for the desired BLAS backend.

Example installation with cuBLAS backend:

```bash
CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip install llama-cpp-python
```

**IMPORTANT:** If you have already installed the CPU-only version of the package, you must reinstall it from scratch. Consider the following command:

```bash
CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip install --upgrade --force-reinstall llama-cpp-python --no-cache-dir
```

### Installation with Metal

llama.cpp supports Apple Silicon as a first-class citizen, optimized through ARM NEON, Accelerate, and Metal frameworks. Use the FORCE_CMAKE=1 environment variable to force the use of cmake and install the pip package for Metal support.

Example installation with Metal support:

```bash
CMAKE_ARGS="-DLLAMA_METAL=on" FORCE_CMAKE=1 pip install llama-cpp-python
```

**IMPORTANT:** If you have already installed a CPU-only version of the package, you must reinstall it from scratch: consider the following command:

```bash
CMAKE_ARGS="-DLLAMA_METAL=on" FORCE_CMAKE=1 pip install --upgrade --force-reinstall llama-cpp-python --no-cache-dir
```

### Installation on Windows

It is stable to install the llama-cpp-python library by compiling from source. You can follow most of the instructions in the repository itself, but there are some Windows-specific instructions that might be helpful.

#### Requirements to install llama-cpp-python

- git
- python
- cmake
- Visual Studio Community / Enterprise (ensure you install this with the following setup)
  - Desktop development with C++
  - Python development
  - Embedded Linux development with C++

- Download and install CUDA Toolkit 12.3 from the [official Nvidia website](https://developer.nvidia.com/cuda-12-2-0-download-archive?target_os=Windows).

  Verify the installation with `nvcc --version` and `nvidia-smi`.

  Add CUDA_PATH (C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.3) to your environment variables.

  Copy the files from: 
  ```
  C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.\extras\visual_studio_integration\MSBuildExtensions
  ```
  To the folder:
  For Enterprise version:
  ```
  C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Microsoft\VC\v170\BuildCustomizations
  ```
  For Community version:
  ```
  C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Microsoft\VC\v170\BuildCustomizations
  ```

Clone the git repository recursively to also get the llama.cpp submodule.

```bash
git clone --recursive -j8 https://github.com/abetlen/llama-cpp-python.git
```

Open a command prompt and set the following environment variables.

```bash
set FORCE_CMAKE=1
set CMAKE_ARGS=-DLLAMA_CUBLAS=OFF
```

If you have an NVIDIA GPU, make sure DLLAMA_CUBLAS is set to ON.

#### Compilation and Installation

Now you can navigate to the llama-cpp-python directory and install the package.

```bash
python3 -m pip install -e .
```

**IMPORTANT:** If you have already installed a CPU-only version of the package, you must reinstall it from scratch: consider the following command:

```bash
python3 -m pip install -e . --force-reinstall --no-cache-dir
```

## Usage

Download the [model](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q8_0.gguf?download=true) and place it in the models folder.

Usage:

```bash
cd path/to/project/folder
python3 ./app.py
```

The server starts on localhost 127.0.0.1:8080.


#### __Tested in Mackbook Pro M3 Pro 11 cpu cores , 14 gpu cores, 18 unify memory with models max 12GB & AMD Ryzen 5600x , Nvidia RTX 3060 gaming OC 12GB, 32GB cpu Memory.__ | __Python version 3.11.7__ | 