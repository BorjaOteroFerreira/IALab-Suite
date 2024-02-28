//@author: Borja Otero Ferreira
class Chat {
    constructor() {
        const textarea = document.getElementById('user-input');
        this.socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
        this.socket.on('connect', () => this.onConnect());
        this.conversationHistory = [{'role': 'system', 'content': 'Eres un asistente en español'}];
        this.socket.on('assistant_response', (response) => this.assistantResponse(response));
        this.currentResponse = '';
        this.systemMessage = 'Eres un asistente en español. Debes responder siemrpe en español'
        this.n_responses = 0;
        this.popupCount = 0;
        this.fullResponse = '';
        this.totalTokens = 0;
        this.totalTokensResponse =0;
        this.conversationStarted = false;
        this.chatId = ' ';
        this.adjustTextareaHeight();
        textarea.addEventListener('input', () => this.adjustTextareaHeight());  
        textarea.addEventListener('keydown', (e) => {
                                                        if (e.which === 13 && !e.shiftKey) {
                                                            e.preventDefault();
                                                            this.sendMessage();
                                                            }
                                                    });
    }
/** METHODS */
    onConnect() {
        console.log('Connected! ✅');
        $('#stop-button').hide();
    }

    assistantResponse(response) {
        this.onAssistantResponse(response);

    }

    onAssistantResponse(response) {
      
        const responseData = response.content["choices"][0];
        const { id, model, created, object } = response.content;
        const { index, delta, finish_reason } = responseData;
        const responseId = id;
        const responseModel = model;
        const responseCreated = created;
        const responseObject = object;
        const choiceIndex = index;
        const choiceDelta = delta && Object.keys(delta).length !== 0 ? delta.content : ''; // Verificar si delta no está vacío
        this.fullResponse += choiceDelta; // Agregar a fullResponse
        const choiceFinishReason = finish_reason != null ? finish_reason : 'None';
        const totalUserTokens = response.total_user_tokens;  // Obtener el número total de tokens del usuario
        const totalAssistantTokens = response.total_assistant_tokens; 
        this.totalTokensResponse = totalUserTokens + totalAssistantTokens

        console.log("ID de la respuesta:", responseId);
        console.log("Modelo utilizado:", responseModel);
        console.log("Creación:", responseCreated);
        console.log("Objeto:", responseObject);
        console.log("Índice de la elección:", choiceIndex);
        console.log("Contenido de la elección:", choiceDelta);
        console.log("Razón de finalización:", choiceFinishReason);
        console.log("Tokens del usuario : ", totalUserTokens);
        console.log("Tokens Respuesta: ", totalAssistantTokens);

        $('#stop-button').show();
        $('#send-button').prop('disabled', true);
        $('#send-button').hide();
        this.handleAssistantResponse(choiceDelta);
        this.scrollToBottom();
        /*console.log('Tokens received 🧠');**/
        
    }
    guardarHistorial(chatId, content) {
        $.ajax({
            type: 'POST',
            url: '/actualizar_historial', // Endpoint para actualizar el historial
            data: JSON.stringify({ nombre_chat: chatId, historial: content }), // Convertir a JSON
            contentType: 'application/json', // Asegura que el servidor entienda que es JSON
            success: function (data) {
                
            },
            error: function (error) {
                console.error('Error al guardar el historial:', error); // Imprimir el mensaje de error en la consola
            }
        });
    }

    cargarHistorial(nombre_chat) {
        const self = this;
        $.ajax({
            type: 'GET',
            url: `/recuperar_historial?nombre_chat=${nombre_chat}`,
            contentType: 'application/json',
            success: function (data) {
                // Verifica si se recuperaron datos válidos
                if (data && Array.isArray(data)) {
                    self.conversationHistory = data; // Asigna los datos recuperados a conversationHistory
                    console.log('Historial cargado exitosamente:', self.conversationHistory);
                } else {
                    console.error('Error: No se pudieron recuperar datos válidos del historial.');
                }
            },
            error: function (error) {
                self.showPopup('Error cargando historial','error')
                console.error('Error al cargar el historial:', error); // Imprime el mensaje de error en la consola
            }
        });
    }

    handleAssistantResponse(response) {
        response = response.replace(/<0x0A>/g, '\n');
    
        if (!this.conversationStarted) {
            this.currentResponse = response;
            this.conversationStarted = true;
        } else {
            this.currentResponse += response;
        }
        
        const converter = new showdown.Converter();
        this.response = converter.makeHtml(this.currentResponse);
    
        const tableRegex = /(?:\|.*(?:\|).*)+\|/gs;
        let htmlResponse = this.response.replace(tableRegex, (table) => {
            const rows = table.trim().split('\n').map(row => row.trim().split('|').filter(cell => cell.trim() !== ''));
        
            // Filtrar las filas que contienen guiones
            const filteredRows = rows.filter(row => !row.some(cell => cell.includes('---')));
        
            let htmlTable = '<table>';
            for (let i = 0; i < filteredRows.length; i++) {
                htmlTable += '<tr>';
                for (let j = 0; j < filteredRows[i].length; j++) {
                    htmlTable += (i === 0) ? `<th>${filteredRows[i][j]}</th>` : `<td>${filteredRows[i][j]}</td>`;
                }
                htmlTable += '</tr>';
            }
            htmlTable += '</table>';
            return htmlTable;
        });
    
        var divAssistant = $('#chat-assistant-' + this.n_responses);
        divAssistant.html(htmlResponse);
    
        document.querySelectorAll('pre').forEach(function(pre) {
            pre.classList.add('line-numbers');
        });
    
        divAssistant.find('pre code').each(function(i, block) {
            Prism.highlightElement(block);
        });
    }

    clearChat() {
        $('#chat-list').html('');
        this.currentResponse = '';
        this.totalTokens = 0;
        this.chatId=' ';
        var label = document.getElementById('tokens');
        label.textContent = ' ' + this.totalTokens + ' Tokens';
        this.conversationHistory = [{'role':'system', 'content' : this.systemMessage}]
        $('#key-container').empty();
        let str = 'Chat emptied! 🗑️';
        this.showPopup(str);
        console.log(str);
    }

    actualizarTokens(){
        this.totalTokens += this.totalTokensResponse
        this.totalTokensResponse = 0;
        var label = document.getElementById('tokens');
        label.textContent = ' ' + this.totalTokens + ' Tokens';
    }

    sendMessage() {
        if (!this.conversationStarted){
         
            this.conversationStarted= true;
            this.currentResponse = ' ';
            this.n_responses += 1;
            var userMessage = $('#user-input').val(); // Obtener el valor del input
            var userMessageTrimed = userMessage.substring(0, 35); // Usando substring
            var currentDate = new Date(); // Obtener la fecha y hora actual
            var formattedDateTime = currentDate.getFullYear() + '.' + (currentDate.getMonth() + 1) + '.' + currentDate.getDate(); 
            var messageWithDateTime =   formattedDateTime + '-'  + userMessageTrimed; // Agregar la fecha y hora al mensaje
            if (this.chatId ===' '){
                this.chatId = messageWithDateTime;

            }
        
            var sanitizedUserMessage = this.escapeHtml(userMessage);
            this.conversationHistory.push({'role': 'user', 'content': sanitizedUserMessage})
            const self = this;
            $.ajax({
                type: 'POST',
                url: '/user_input',
                data: JSON.stringify({ content: self.conversationHistory }), // Convertir a JSON
                contentType: 'application/json', // Asegura que el servidor entienda que es JSON
                success: function (data) {
                    $('#stop-button').hide();
                    $('#send-button').show();
                    $('#send-button').prop('disabled', false);
                    self.addToConversationHistory(); // Agregar la respuesta completa al historial
                    self.actualizarTokens();
                    self.guardarHistorial(self.chatId , self.conversationHistory);
                    var conversationListDiv = $('#conversations-list');
                    var buttonExists = false;
                    $('.load-history').each(function() {
                        if ($(this).text() === '📪 '+self.chatId) {
                            buttonExists = true;
                            return false; // Salir del bucle each() si se encuentra un botón con el mismo texto
                        }
                    });
                    console.log("Valor de self.chatId:", self.chatId);
                    console.log("Número de botones existentes:", $('.load-history').length);
                    if (!buttonExists) {
                        var conversationListDiv = $('#conversations-list');
                        const newChatHistory = $("<button class='load-history' onclick='chat.loadHistory("+self.chatId+")'>📪 "+self.chatId+"</button>");
                        conversationListDiv.prepend(newChatHistory);
                    }
                    self.showPopup(data);
                    console.log(data);
                    self.conversationStarted = false;
                },
                error: function (error) {
                    self.showPopup(error, 'error');
                    console.error('Error:', error);
                    self.conversationStarted = false;
                }
            });
            console.log('Prompt sent! 🔤');
            $('#user-input').val('');
            $('#user-input').focus();
            var message = $('<div class="user-message-container-' + this.n_responses + 
                            ' user-message-container"><label for="chat-user-' + this.n_responses + 
                            '">User</label><div id="chat-user-' + this.n_responses + 
                            '" class="user-message user-message-' + this.n_responses + '">' + 
                            sanitizedUserMessage + '</div></div>');
            var chatList = $('#chat-list');
            chatList.append(message);
          
            var divAssistant = $('<div class="assistant-message-container-' + this.n_responses + 
                                ' assistant-message-container"><label for="chat-assistant-' + this.n_responses + 
                                '">Assistant<br></label><div id="chat-assistant-' + this.n_responses + 
                                '" class="assistant-message"></div></div>');
            chatList.append(divAssistant);

            var shareButton = $('<button id="share" onclick="chat.shareChat(' + this.n_responses + ')">Share</button>');
            var userMessageCointainer = $('.assistant-message-container-' + this.n_responses);
            userMessageCointainer.append(shareButton);
            this.scrollToBottom();
            
        }
    }

    // Método para agregar la respuesta completa al historial de conversación
    addToConversationHistory() {
        // Agregar la respuesta completa al historial de conversación
        this.conversationHistory.push({'role': 'assistant', 'content': this.fullResponse});
        
        // Reiniciar la respuesta completa para futuras conversaciones
        this.fullResponse = '';
    }

    newChat() {
        this.clearChat();
    }

    applyConfig() {
        var selectedModel = $('#model-select').val();
        var selectedFormat = $('#format-select').val();
        var systemMessage = $('#system-message').val();
        var gpuLayers = $('#gpu-layers').val();
        var temperature = $('#temperature').val();
        var n_ctx = $('#context').val();
        const self = this;
        $.ajax({

            type: "POST",
            url: "/load_model",
            data: {
                model_path: selectedModel,
                format: selectedFormat,
                temperature: temperature,
                system_message: systemMessage,
                gpu_layers: gpuLayers,
                context: n_ctx
            },
            success: function (data) {
                self.showPopup('Model loaded successfully');
                self.newChat()
                console.log(data);
            },
            error: function (error) {
                self.showPopup(error, 'error');
                console.error('Error:', error);
            }
        });
        this.clearContext();
    }

    unloadModel() {
        const self = this;
        $.ajax({
            type: "POST",
            url: "/unload_model",
            success: function (data) {
                self.showPopup(data);
                console.log(data);
            },
            error: function (error) {
                self.showPopup(error, 'error');
                console.error('Error:', error);
            }
        });
    }

    stopResponse() {
        const self = this;
        $.ajax({
            type: "POST",
            url: "/stop_response",
            success: (data) => {
                console.log(data);
                self.showPopup(data);
                $('#stop-button').hide();
                $('#send-button').show();
            },
            error: (error) => {
                self.showPopup(error, 'error');
                console.error('Error:', error);
            }
        });
    }
//** UTILS */
    scrollToBottom() {
        var chatContainer = $('#chat-container')[0];
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    copyToClipboard(button) {
        var codeContent = $(button).siblings('code').html();
        codeContent = codeContent.replace(/<br>/g, '\n');
        codeContent = codeContent.replace(/^[^\n]*\n/, '');

        var textarea = document.createElement('textarea');
        textarea.textContent = codeContent;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        let str = 'Copied to clipboard! 📋';
        this.showPopup(str);
        console.log(str);
    }

    toggleSidebar() {
        var sidebar = document.getElementById('sidebar');
        var chatContainer = document.getElementById('main-container');
        
        // Verificar si las media queries están activas
        var mediaQueriesActive = window.matchMedia("(max-width: 1023px)").matches || window.matchMedia("(max-height: 740px)").matches;
    
        // Solo ejecutar el código si las media queries no están activas
        if (!mediaQueriesActive) {
            if (sidebar.style.display === 'none' || sidebar.style.display === '') {
                sidebar.style.display = 'block';
                chatContainer.style.marginRight = '20%'; // Ajustar el margen derecho para dejar espacio al sidebar
            } else {
                sidebar.style.display = 'none';
                chatContainer.style.marginRight = '20px'; // Restaurar el margen derecho a 0
            }
        }
        else{
            sidebar.style.display = (sidebar.style.display === 'none' || sidebar.style.display === '') ? 'block' : 'none';
        }
    }
    escapeHtml(text) {
        var map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function (m) {
            return map[m];
        });
    }

    shareChat(responseNumber) {
        const self = this;
        let str_success = 'Chat shared successfully';
        if (navigator.share) {
            var ask = $('.user-message-' + responseNumber).text();
            var response = $('#chat-assistant-' + responseNumber).html();
            var fullResponse = "User: \n" + ask + "\n\nAssistant:\n" + response;
            fullResponse = fullResponse.replace(/<br>/g, '\n');
            navigator.share({
                title: ask,
                text: fullResponse,
                url: '/'
            })
                .then(() => { console.log(str_success); self.showPopup(str_success); })
                .catch((error) => console.error('Error sharing chat:', error));
        } else {
            self.showPopup('Sharing function not supported in this browser. 😤', 'error');
        }
    }

    showPopup(message, type) {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'popup-container';
            container.style.left = '20px'; 
            container.style.bottom = '20px'; 
            document.body.appendChild(container);
        }

        const popup = document.createElement('div');
        popup.className = 'popup-notification';
        if (type === 'error') {
            popup.classList.add('popup-error');
        }
        popup.textContent = message;
        container.appendChild(popup);

        setTimeout(() => {
            popup.style.opacity = 1;
            setTimeout(() => {
                popup.style.opacity = 0;
                setTimeout(() => {
                    container.removeChild(popup);
                    if (container.childNodes.length === 0) {
                        document.body.removeChild(container);
                    }
                }, 500); //seconds to complete disappearance animation
            }, 5500); //seconds before disappearing
        }, 100); // 0.1 seconds before displaying
    }

    adjustTextareaHeight() {
        const textarea = document.getElementById('user-input');
        const lineHeight = parseFloat(getComputedStyle(textarea).lineHeight);
        const maxLines = 20; 
        const maxHeight = maxLines * lineHeight; 
        textarea.style.height = '0';
        textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`;
    }
}
