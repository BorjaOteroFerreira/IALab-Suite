class SendToConsole: 

    @staticmethod
    def send_to_console(message,socket):
        socket.emit('output_console', {'content': message}, namespace='/test')