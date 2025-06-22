import os
import sys
from Api_react import IASuiteApi

def main():
    api = IASuiteApi()
      # Imprimir mensaje informativo
    print("\nServidor de IALab Suite iniciado!")

    # Iniciar el servidor
    api.socketio.run(api.app, host='0.0.0.0', port=8081, allow_unsafe_werkzeug=True)

if __name__ == "__main__":
    main()
