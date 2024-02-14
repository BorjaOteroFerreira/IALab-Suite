'''
@Author: Borja Otero Ferreira
'''
from IASuite import IASuiteApi
import webbrowser


if __name__ == '__main__':
    chat_app = IASuiteApi()
    chat_app.socketio.run(webbrowser.open('http://127.0.0.1:8080',2,False) and chat_app.app, host='0.0.0.0', port=8080, debug=False)

   

