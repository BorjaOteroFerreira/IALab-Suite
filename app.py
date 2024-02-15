'''
@Author: Borja Otero Ferreira
'''
from IASuite import IASuiteApi
from flask_cors import CORS 



if __name__ == '__main__':
    chat_app = IASuiteApi()
    chat_app.socketio.run(chat_app.app, host='0.0.0.0', port=8080, debug=False)

   

