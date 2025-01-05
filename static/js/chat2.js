//@author: Borja Otero Ferreira
class Chat {
    constructor() {
        this.tools= false;
        this.rag =  false;
        const checkbox = document.getElementById('checkbox-3');
        const checkboxrag = document.getElementById("checkbox-4");
        const textarea = document.getElementById('user-input');
        this.socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
        this.socket.on('connect', () => this.onConnect());
        this.systemMessage = 'Eres un asistente en español. Debes responder siemrpe en español';
        this.conversationHistory = [{'role': 'system', 'content': this.systemMessage}];
        this.socket.on('assistant_response', (response) => this.assistantResponse(response));
        this.socket.on('output_console', (response) => this.consoleOutputResponse(response));
        this.socket.on('utilidades', (response) => this.cargarUtiles(response));
        this.currentResponse = '';
        this.library ='llama';
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

        // Agregar evento change a los checkbox
        checkbox.addEventListener('change', () => {
            this.tools = checkbox.checked;
        });
        checkboxrag.addEventListener('change', () => {
            this.rag = checkboxrag.checked;
        });
       }                                             
    
/** METHODS */
cargarUtiles(response) {
    // Obtener el div donde se cargarán los resultados
    var divResultados = document.getElementById('resultados'+ this.n_responses);
    // Recorrer la lista de IDs de video recibidos
    response.ids.forEach(function(id) {
        // Crear un elemento iframe para cada ID de video
        var iframe = document.createElement('iframe');
        iframe.width = "64px";
        iframe.height = "32px";
        iframe.src = "https://www.youtube.com/embed/" + id;
        iframe.frameborder = "0";
        iframe.allow = "encrypted-media; picture-in-picture";
        iframe.allowfullscreen = true;
        // Agregar el iframe al div
        divResultados.appendChild(iframe);
    });
}

    onConnect() {
        console.log('Connected! ✅');
        $('#stop-button').hide();
    }

    consoleOutputResponse(response){
        var divConsole = $('#consola');
        var role = response.role;
        var divRespuesta = $('<div id="outputConsole" ><pre class='+role+'>'+response.content+'</pre></div>');
        if (role === 'info')
            divRespuesta = $('<div id="outputConsole" ><pre class='+role+'>ialab-suite@agent:~$ '+response.content+'</pre></div>');
        divConsole.append(divRespuesta);
        this.scrollToBottom(divConsole[0]);
    }

    assistantResponse(response) {
        this.onAssistantResponse(response);
    }

    onAssistantResponse(response) {
        var delta = '';
        var choiceDelta =''
        if (this.library === 'ollama'){
            const responseData = response;
            delta = responseData.content;
            console.log(response);
            this.fullResponse += delta; // Agregar a fullResponse
            const totalUserTokens = responseData.total_user_tokens;  // Obtener el número total de tokens del usuario
            const totalAssistantTokens = responseData.total_assistant_tokens; 
            this.totalTokensResponse = totalUserTokens + totalAssistantTokens;
            console.log("Contenido de la elección:", delta);
            console.log("Tokens del usuario : ", totalUserTokens);
            console.log("Tokens Respuesta: ", totalAssistantTokens);
        }else{
            const responseData = response.content["choices"][0];
            const { id, model, created, object } = response.content;
            const { index, delta, finish_reason } = responseData;
            const responseId = id;
            const responseModel = model;
            const responseCreated = created;
            const responseObject = object;
            const choiceIndex = index;
            choiceDelta = delta && Object.keys(delta).length !== 0 ? delta.content : ''; // Verificar si delta no está vacío
            this.fullResponse += choiceDelta; // Agregar a fullResponse
            const choiceFinishReason = finish_reason != null ? finish_reason : 'None';
            const totalUserTokens = response.total_user_tokens;  // Obtener el número total de tokens del usuario
            const totalAssistantTokens = response.total_assistant_tokens; 
            this.totalTokensResponse = totalUserTokens + totalAssistantTokens;
            console.log("ID de la respuesta:", responseId);
            console.log("Modelo utilizado:", responseModel);
            console.log("Creación:", responseCreated);
            console.log("Objeto:", responseObject);
            console.log("Índice de la elección:", choiceIndex);
            console.log("Contenido de la elección:", choiceDelta);
            console.log("Razón de finalización:", choiceFinishReason);
            console.log("Tokens del usuario : ", totalUserTokens);
            console.log("Tokens Respuesta: ", totalAssistantTokens);
        }
        $('#stop-button').show();
        $('#send-button').prop('disabled', true);
        $('#send-button').hide();
        var responseModel = this.library === 'ollama' ? delta : choiceDelta;
        this.handleAssistantResponse(responseModel);
        var chatContainer = $('#chat-container')[0];
        this.scrollToBottom(chatContainer);
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

    loadHistory(nombre_chat) {
        nombre_chat = String(nombre_chat);
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
                    self.chatId=nombre_chat;
                } else {
                    console.error('Error: No se pudieron recuperar datos válidos del historial.');
                }
                self.loadMessages();
            },
            error: function (error) {
                self.showPopup('Error cargando historial','error');
                console.error('Error al cargar el historial:', error); // Imprime el mensaje de error en la consola
            }
        });
    }

    loadMessages(){
        $('#chat-list').empty();
        // Suponiendo que this.chatHistory contiene los mensajes
        for (var i = 0; i < this.conversationHistory.length; i++) {
            var messageData = this.conversationHistory[i];
            var sanitizedUserMessage = messageData.role === 'user' ? sanitizeMessage(messageData.content) : messageData.content;
            const converter = new showdown.Converter();
            messageData.content = converter.makeHtml(messageData.content);
            if (messageData.role === 'user') {
                var message = $('<div class="user-message-container-' + i +
                                ' user-message-container"><label for="chat-user-' + i +
                                '">User</label><div id="chat-user-' + i +
                                '" class="user-message user-message-' + i + '">' +
                                sanitizedUserMessage + '</div></div>');
                $('#chat-list').append(message);
            } else if (messageData.role === 'assistant') {
                var divAssistant = $('<div class="assistant-message-container-' + i +
                                    ' assistant-message-container"><label for="chat-assistant-' + i +
                                    '">Assistant<br></label><div id="chat-assistant-' + i +
                                    '" class="assistant-message">' + messageData.content + '</div></div>');
                $('#chat-list').append(divAssistant);
                divAssistant.find('pre code').each(function(i, block) {
                    Prism.highlightElement(block);
                });
            }
    }

        
function sanitizeMessage(message) {
    return $('<div>').text(message).html();
}
    }

    deleteHistory(nombreChat){
        const self = this; 
        $.ajax({
            url: `/eliminar_historial?nombre_chat=${nombreChat}`,
            type: 'DELETE',
            success: function(result) {
                console.log(`Historial ${nombreChat} eliminado exitosamente.`);
                self.removeFromConversationList(nombreChat);

            },
            error: function(xhr, status, error) {
                console.error(`Error al eliminar el historial ${nombreChat}: ${xhr.status}`);
            }
        });
    
    }

    
    removeFromConversationList(chatId) {
        // Eliminar el elemento de la lista de conversaciones
        const conversationListDiv = $('#conversations-list');
        const elementToRemove = $('#' + chatId);
        if (elementToRemove.length) {
            elementToRemove.remove();
        } else {
            // Intentar encontrar el elemento con un selector que coincida con el formato de ID
            const formattedIdSelector = '.load-history[id^="' + chatId + '"]';
            const elementToRemoveFormatted = $(formattedIdSelector);
            if (elementToRemoveFormatted.length) {
                elementToRemoveFormatted.remove();
            } else {
                console.error(`Element with ID ${chatId} not found in conversation list.`);
            }
        }
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
        this.conversationHistory = [{'role':'system', 'content' : this.systemMessage}];
        $('#key-container').empty();
        let str = 'Chat emptied! 🗑️';
        this.showPopup(str);
        console.log(str);
    }

    actualizarTokens(){
        this.totalTokens += this.totalTokensResponse;
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
            var userMessageTrimed = userMessage.substring(0, 35).trim(); // Usando substring
            var currentDate = new Date(); // Obtener la fecha y hora actual
            var formattedDateTime = currentDate.getFullYear() + '.' + (currentDate.getMonth() + 1) + '.' + currentDate.getDate()+'.'+currentDate.getHours()+'.'+currentDate.getMinutes()+'.'+currentDate.getSeconds(); 
            var messageWithDateTime =   formattedDateTime + '-'  + userMessageTrimed; // Agregar la fecha y hora al mensaje
            if (this.chatId ===' '){
                this.chatId = messageWithDateTime.replace(' ','_');

            }
            var url = this.library === 'ollama' ? 'v1/chat/completions' : '/user_input';
            var sanitizedUserMessage = this.escapeHtml(userMessage);
            this.conversationHistory.push({'role': 'user', 'content': sanitizedUserMessage});

            const self = this;
            self.conversationHistory[self.conversationHistory.length -1]['content'];;
            $.ajax({
                type: 'POST',
                url: url,
                data: JSON.stringify({ content: self.conversationHistory, tools: this.tools, rag: this.rag}), // Convertir a JSON
                contentType: 'application/json', // Asegura que el servidor entienda que es JSON
                success: function (data) {
                    $('#stop-button').hide();
                    $('#send-button').show();
                    $('#send-button').prop('disabled', false);
                    self.addToConversationHistory(); // Agregar la respuesta completa al historial
                    self.actualizarTokens();
                   
                    var conversationListDiv = $('#conversations-list');
                    var buttonExists = false;
                    $('.load-history').each(function() {
                        console.log($(this).text())
                        if ($(this).text() === '❌'+self.chatId) {
                            
                            buttonExists = true;
                            return false; // Salir del bucle each() si se encuentra un botón con el mismo texto
                        }
                    });
                    console.log("Valor de self.chatId:", self.chatId);
                    console.log("Número de botones existentes:", $('.load-history').length);
                    var conversationListDiv = $('#conversations-list');
                    var newChatHistory ='';
                    if(!buttonExists) {
                      newChatHistory = $("<div class='load-history' id='"+self.chatId+"'><button  height='1em' width='1em' onclick=chat.deleteHistory('"+self.chatId+"')>❌</button><button class='btnLoadHistory' onclick=chat.loadHistory('"+self.chatId+"')>"+self.chatId+"</button></div>"); // $("<button class='load-history' onclick=chat.loadHistory('"+self.chatId+"')>📪 "+self.chatId+"</button>") 
                      conversationListDiv.prepend(newChatHistory);
                    }
                    self.guardarHistorial(self.chatId , self.conversationHistory);
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
                            ' user-message-container"><div id="chat-user-' + this.n_responses + 
                            '" class="user-message user-message-' + this.n_responses + '">' + 
                            sanitizedUserMessage + '</div></div>');
            var chatList = $('#chat-list');
        
            chatList.append(message);
          
            var divAssistant = $('<div class="assistant-message-container-' + this.n_responses + 
                                ' assistant-message-container"><div id="contenedor_respuesta"><div id="chat-assistant-' + this.n_responses + 
                                '" class="assistant-message"></div><div id="resultados'+ this.n_responses+ '" class="resultados"></div></div></div>');
            chatList.append(divAssistant);

            var shareButton = $('<button id="share" onclick="chat.shareChat(' + this.n_responses + ')">Share</button>');
            var userMessageCointainer = $('.assistant-message-container-' + this.n_responses);
            userMessageCointainer.append(shareButton);
            var chatContainer = $('#chat-container')[0];
            this.scrollToBottom(chatContainer);
            
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
        this.systemMessage = systemMessage;
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
                self.newChat();
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
    scrollToBottom(id) {
        var chatContainer = $('#chat-container')[0];
        id.scrollTop = id.scrollHeight;
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

    toggleSidebar(element) {
        var sidebar = document.getElementById(element);
        // Verificar si las media queries están activas
        var mediaQueriesActive = window.matchMedia("(max-width: 1023px)").matches || window.matchMedia("(max-height: 740px)").matches;
    
        // Solo ejecutar el código si las media queries no están activas
        if (!mediaQueriesActive) {
            if (sidebar.style.display === 'none' || sidebar.style.display === '') {
                sidebar.style.display = 'flex';
                sidebar.style.width = '15%';
            } else {
                sidebar.style.display = 'none';
          
            }
        }
        else{
             if(sidebar.style.display === 'none' || sidebar.style.display === '') {
                sidebar.style.display = 'block';
                sidebar.style.width = '100%';
            } 
            else{
                sidebar.style.display = 'none';
            }
            
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
    