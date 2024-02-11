class Chat {
    constructor() {
        this.socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
        this.socket.on('connect', () => this.onConnect());
        this.socket.on('assistant_response', (response) => this.assistantResponse(response));
        
        this.currentAssistantResponse = '';
        this.n_responses = 0;
        this.conversationStarted = false;
        
      

    }
    onConnect() {
        console.log('Conectado! ✅');
        $('#stop-button').hide();
       
    }

    assistantResponse(response){
        this.onAssistantResponse(response);
   

    }

    onAssistantResponse(response) {
        $('#stop-button').show();
        this.handleAssistantResponse(response.content);
        this.scrollToBottom();
        console.log('Tokens recividos 🔤');
    }

  

    handleAssistantResponse(response) {
        response = response.replace(/<0x0A>/g, '<br>');
        var chatList = $('#chat-list');
        if (!this.conversationStarted) {
            this.currentAssistantResponse = response;
            this.conversationStarted = true;
        } else {
            this.currentAssistantResponse += response;
        }
        // Reemplaza triple comilla con <pre><code>
        this.currentAssistantResponse = this.currentAssistantResponse.replace(/```([\s\S]*?)```/g, '<pre><button class="copy-button" onclick="chatApp.copyToClipboard(this)">Copiar</button><code>$1</code></pre>');
        var div = $('#chat-assistant-' + this.n_responses);
        div.html(this.currentAssistantResponse);
        Prism.highlightAll();
        this.scrollToBottom();
    }

    clearChat() {
        $('#chat-list').html('');
        this.currentAssistantResponse = '';
        $('#key-container').empty();
        console.log('Se ha vaciado el chat! 🗑️');
    }

    sendMessage() {
        this.currentAssistantResponse = ' ';
        this.n_responses += 1;
        var userMessage = $('#user-input').val();
        var sanitizedUserMessage = this.escapeHtml(userMessage);

        $.ajax({
            type: 'POST',
            url: '/user_input',
            data: { content: sanitizedUserMessage },
            success: function (data) {
                $('#stop-button').hide();
                console.log(data);
            },
            error: function (error) {
                console.error('Error:', error);
            }
        });
        console.log('Prompt enviado! 🧠');
        $('#user-input').val('');
        $('#user-input').focus();
       
        var message = $('<div class="user-message-container-' + this.n_responses + ' user-message-container"><label>Yo</label><div class="user-message user-message-' + this.n_responses + '">' + sanitizedUserMessage + '</div></div>');
        var chatList = $('#chat-list');
        chatList.append(message);
        
        var divAssistant = $('<div class="assistant-message-container-'+this.n_responses+' assistant-message-container"><label>Asistente<br></label><div id="chat-assistant-'+this.n_responses+'" class="assistant-message"></div></div>');
        chatList.append(divAssistant);

        var botonCompartir = $('<button id="share" onclick="chatApp.shareChat(' + this.n_responses + ')">Compartir</button>');
        var userMessageCointainer = $('.assistant-message-container-' + this.n_responses);
        userMessageCointainer.append(botonCompartir);
        this.scrollToBottom();
    }

    clearContext() {
        $.ajax({
            type: "POST",
            url: "/clear_context", 
            success: function (data) {
                console.log(data);
            },
            error: function (error) {
                console.error('Error:', error);
            }
        });
        this.clearChat();
    }

    applyConfig() {
        var selectedModel = $('#model-select').val();
        var selectedFormat = $('#format-select').val();
        var systemMessage = $('#system-message').val();
        var gpuLayers = $('#gpu-layers').val();
        var n_ctx  = $('#context').val();   
        $.ajax({
            type: "POST",
            url: "/load_model",
            data: { 
                model_path: selectedModel, 
                format: selectedFormat,
                system_message: systemMessage, 
                gpu_layers: gpuLayers,
                context: n_ctx
            },
            success: function (data) {
                console.log(data);
            },
            error: function (error) {
                console.error('Error:', error);
            }
        });
        this.clearContext();
    }

    unloadModel() {
        $.ajax({
            type: "POST",
            url: "/unload_model",
            success: function (data) {
                console.log(data);
            },
            error: function (error) {
                console.error('Error:', error);
            }
        });
    }

    stopResponse() {
        $.ajax({
            type: "POST",
            url: "/stop_response",
            success: (data) => {
                console.log(data);
                $('#stop-button').hide();
            },
            error: (error) => {
                console.error('Error:', error);
            }
        });
      
    }

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
        alert('Copiado al portapapeles');
        console.log('Copiado al portapapeles! 📋');
    }
    toggleSidebar() {
        var sidebar = document.getElementById('sidebar');
        sidebar.style.display = (sidebar.style.display === 'none' || sidebar.style.display === '') ? 'block' : 'none';
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
        if (navigator.share) {
            var ask = $('.user-message-' + responseNumber).text();
            var response =  $('#chat-assistant-' + responseNumber).html();
            var fullResponse = "Yo: \n"+ask+"\n\nAsistente:\n"+response
            fullResponse = fullResponse.replace(/<br>/g, '\n');
            navigator.share({
                title: ask,
                text: fullResponse,
                url: '/' 
            })
            .then(() => console.log('Chat compartido con éxito'))
            .catch((error) => console.error('Error al compartir el chat:', error));
        } else {
            alert('La función de compartir no está soportada en este navegador. 😤');
        }
    }
}




