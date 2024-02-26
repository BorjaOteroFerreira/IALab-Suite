from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from flask import request
from IASuite import IASuiteApi
import atexit

class EmbeddedFlaskApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Configurar la aplicación Flask
        self.flask_app = IASuiteApi()
        # Configurar la interfaz de PyQt
        self.init_ui()

    def init_ui(self):
        # Crear un widget contenedor
        container = QWidget(self)
        self.setCentralWidget(container)

        # Crear un diseño vertical para el widget contenedor
        layout = QVBoxLayout(container)

        # Crear un visor web utilizando WebEngineView
        web_view = QWebEngineView(self)
        web_view.load(QUrl("http://127.0.0.1:8080"))  # Ajusta el puerto según tu configuración Flask
        layout.addWidget(web_view)
        

        # Maximizar la ventana para llenar la pantalla
        self.showMaximized()
        web_view.setZoomFactor(0.75)  # Puedes ajustar el valor según sea necesario
     
        style_sheet = """
            QMainWindow {
                background-color: #011627;
                border: none;
                margin: 0;
                padding: 0;
            }
        """
        app.setStyleSheet(style_sheet)

    def run_flask_app(self):
        # Ejecutar la aplicación Flask en un hilo separado
        from threading import Thread
        flask_thread = Thread(target=lambda: self.flask_app.app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False))
        flask_thread.start()

if __name__ == '__main__':
    app = QApplication([])

    # Cambiar el nombre que se muestra en la barra de tareas de Mac
    app.setApplicationDisplayName("IALab_Suite")

    main_window = EmbeddedFlaskApp()
    main_window.run_flask_app()
    main_window.show()
    app.exec_()
