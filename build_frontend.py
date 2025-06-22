"""
Script para construir el frontend de React e integrarlo con el backend de Flask
@Author: Borja Otero Ferreira
"""

import os
import shutil
import subprocess
import sys
import platform
import time
from pathlib import Path

# Colores para la salida
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message):
    """Imprime un mensaje de cabecera."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}==== {message} ===={Colors.ENDC}\n")

def print_success(message):
    """Imprime un mensaje de éxito."""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

def print_warning(message):
    """Imprime un mensaje de advertencia."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")

def print_error(message):
    """Imprime un mensaje de error."""
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")

def run_command(command, cwd=None):
    """Ejecuta un comando y muestra la salida en tiempo real."""
    try:
        process = subprocess.Popen(
            command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            universal_newlines=True,
            cwd=cwd
        )
        
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        return process.returncode == 0
    except Exception as e:
        print_error(f"Error ejecutando comando '{command}': {str(e)}")
        return False

def check_dependencies():
    """Comprueba que todas las dependencias necesarias estén instaladas."""
    print_header("Comprobando dependencias")
    
    # Verificar Node.js y npm
    nodejs_ok = run_command("node --version")
    if not nodejs_ok:
        print_error("Node.js no está instalado o no está en el PATH.")
        print("Por favor, instale Node.js desde https://nodejs.org/")
        return False
    
    npm_ok = run_command("npm --version")
    if not npm_ok:
        print_error("npm no está instalado o no está en el PATH.")
        return False
    
    print_success("Todas las dependencias están instaladas correctamente.")
    return True

def install_frontend_dependencies():
    """Instala las dependencias del frontend."""
    print_header("Instalando dependencias del frontend")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.is_dir():
        print_error(f"No se encontró el directorio '{frontend_dir}'.")
        return False
    
    return run_command("npm install", cwd=frontend_dir)

def build_frontend():
    """Construye el frontend de React."""
    print_header("Construyendo el frontend")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.is_dir():
        print_error(f"No se encontró el directorio '{frontend_dir}'.")
        return False
    
    # Construir con npm
    build_ok = run_command("npm run build", cwd=frontend_dir)
    if not build_ok:
        return False
    
    print_success("Frontend construido correctamente.")
    return True

def integrate_with_flask():
    """Integra el frontend construido con el backend de Flask."""
    print_header("Integrando con Flask")
    
    build_dir = Path("frontend/build")
    static_dir = Path("static")
    templates_dir = Path("templates")
    
    # Verificar que el directorio build existe
    if not build_dir.is_dir():
        print_error(f"No se encontró el directorio '{build_dir}'.")
        return False
    
    try:
        # Crear directorios si no existen
        if not static_dir.is_dir():
            static_dir.mkdir(parents=True)
            print_success(f"Creado directorio '{static_dir}'.")
        
        if not templates_dir.is_dir():
            templates_dir.mkdir(parents=True)
            print_success(f"Creado directorio '{templates_dir}'.")
        
        # Limpiar directorios de destino
        for item in static_dir.glob("*"):
            if item.is_file():
                item.unlink()
            else:
                shutil.rmtree(item)
        
        for item in templates_dir.glob("react.*"):
            item.unlink()
        
        # Copiar archivos estáticos
        for item in build_dir.glob("*"):
            if item.name == "index.html":
                # Mover index.html a templates
                shutil.copy(item, templates_dir / "react.html")
                print_success(f"Copiado '{item}' a '{templates_dir / 'react.html'}'.")
            elif item.is_dir():
                # Copiar directorios completos
                dest_dir = static_dir / item.name
                shutil.copytree(item, dest_dir)
                print_success(f"Copiado directorio '{item}' a '{dest_dir}'.")
            else:
                # Copiar archivos individuales
                shutil.copy(item, static_dir)
                print_success(f"Copiado '{item}' a '{static_dir}'.")
        
        # Modificar las referencias en el HTML
        update_html_references()
        
        print_success("Frontend integrado correctamente con Flask.")
        return True
    except Exception as e:
        print_error(f"Error integrando con Flask: {str(e)}")
        return False

def update_html_references():
    """Actualiza las referencias en el archivo HTML para que funcionen con Flask."""
    try:
        html_file = Path("templates/react.html")
        if not html_file.is_file():
            print_error(f"No se encontró el archivo '{html_file}'.")
            return
        
        content = html_file.read_text(encoding="utf-8")
        
        # Actualizar referencias a archivos estáticos
        content = content.replace('href="/', 'href="/static/')
        content = content.replace('src="/', 'src="/static/')
        content = content.replace('content="/', 'content="/static/')
        
        # Excepciones - no modificar algunas URLs
        content = content.replace('href="/static/static/', 'href="/static/')
        content = content.replace('src="/static/static/', 'src="/static/')
        content = content.replace('href="/static/http', 'href="http')
        content = content.replace('src="/static/http', 'src="http')
        
        # Guardar cambios
        html_file.write_text(content, encoding="utf-8")
        print_success("Actualizadas referencias en el archivo HTML.")
    except Exception as e:
        print_error(f"Error actualizando referencias HTML: {str(e)}")

def main():
    """Función principal."""
    start_time = time.time()
    
    print_header("Construyendo IALab-Suite Frontend")
    
    if not check_dependencies():
        return 1
    
    if not install_frontend_dependencies():
        print_error("Error instalando dependencias del frontend.")
        return 1
    
    if not build_frontend():
        print_error("Error construyendo el frontend.")
        return 1
    
    if not integrate_with_flask():
        print_error("Error integrando el frontend con Flask.")
        return 1
    
    elapsed_time = time.time() - start_time
    print_success(f"¡Construcción completada en {elapsed_time:.2f} segundos!")
    print(f"\n{Colors.BLUE}{Colors.BOLD}Puedes iniciar la aplicación con el comando:{Colors.ENDC}")
    print(f"{Colors.YELLOW}python Api.py{Colors.ENDC}")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_warning("\nProceso interrumpido por el usuario.")
        sys.exit(1)
