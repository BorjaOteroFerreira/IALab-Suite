var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
var currentAssistantResponse;
n_responses = 0;
socket.on('connect', function() {
    console.log('Connected!');
});

socket.on('assistant_response', function(response) {
    handleAssistantResponse(response.content);
    scrollToBottom();
  
});

function handleAssistantResponse(response) {
    response = response.replace(/<0x0A>/g, '<br>');
    var chatList = $('#chat-list');
    
    if (!conversationStarted) {
        currentAssistantResponse = response;
        conversationStarted = true;
    } else {
        currentAssistantResponse += response;
    }

    // Reemplaza triple comilla con <pre><code>
    currentAssistantResponse = currentAssistantResponse.replace(/```([\s\S]*?)```/g, '<pre><button class="copy-button" onclick=copyToClipboard(this)>Copiar</button><code>$1</code></pre>');
    var div = $('#chat-assistant-' + n_responses);
    div.html(currentAssistantResponse);
    Prism.highlightAll();
    scrollToBottom();
    /** Agregar teclas que caen
    var keysContainer = $('#key-container');
    var responseArray = response.split('');

    // Agregar cada tecla individualmente en orden inverso
    for (var i = 0; i < responseArray.length; i++) {
        var key = $('<div class="key">' + responseArray[i] + '</div>');
        keysContainer.prepend(key);
    }**/
    // Hacer scroll hacia abajo después de agregar un nuevo mensaje
}

socket.on('clear_chat', function () {
    $('#chat-list').html('');
    currentAssistantResponse = '';
    $('#key-container').empty();
});

function sendMessage() {
    currentAssistantResponse=" "
    n_responses+=1
    var userMessage = $('#user-input').val();
    $.ajax({
        type: 'POST',
        url: '/user_input',
        data: { content: userMessage },
        success: function(data) {
            console.log(data);
        },
        error: function(error) {
            console.error('Error:', error);
        }
    });
    $('#user-input').val('');
    $('#user-input').focus();
    var message = $('<div class="user-message-container"><label>Yo</label><div class="user-message">' + userMessage + '</div></div>');
    var chatList = $('#chat-list');
    chatList.append(message);
    var divAssistant = $('<div class="assistant-message-container"><label>Asistente<br></label><div id="chat-assistant-'+n_responses+'" class="assistant-message"></div></div>')
    chatList.append(divAssistant)
    scrollToBottom();
    
}

function startModel() {
    var selectedModel = $('#model-select').val();
    var selectedFormat = $('#format-select').val();
    $.ajax({
        type: "POST",
        url: "/start_model",
        data: { model_path: selectedModel, format: selectedFormat },
        success: function (data) {
            console.log(data);
        },
        error: function (error) {
            console.error('Error:', error);
     }
});
}

function unloadModel() {
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

function clearContext() {
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
}

function scrollToBottom() {
    var chatContainer = $('#chat-container')[0];
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function copyToClipboard(button) {
    var codeContent = $(button).siblings('code').html(); // Obtener el contenido HTML

    // Reemplazar <br> con saltos de línea
    codeContent = codeContent.replace(/<br>/g, '\n');
    //Eliminar la primera linea con la etiqueta de lenguaje
    codeContent = codeContent.replace(/^[^\n]*\n/, '');


    var textarea = document.createElement('textarea');
    textarea.textContent = codeContent; // Usar textContent para evitar interpretar el HTML

    document.body.appendChild(textarea);

    textarea.select();
    document.execCommand('copy');

    document.body.removeChild(textarea);

    alert('Copiado al portapapeles');
}
