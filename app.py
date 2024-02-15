'''
@Author: Borja Otero Ferreira
'''
from IASuite import IASuiteApi
from flask_cors import CORS 



if __name__ == '__main__':
    chat_app = IASuiteApi()
    CORS(chat_app.app, origins=["http://127.0.0.1:8080", "http://[::1]:8080"])
    chat_app.socketio.run(chat_app.app, host='0.0.0.0', port=8080, debug=False)

   

