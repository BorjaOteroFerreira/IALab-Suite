var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
var currentAssistantResponse;
var n_responses = 0;
var response
socket.on('connect', function() {
    console.log('Conectado!');
});

socket.on('assistant_response', function(response) {
    handleAssistantResponse(response.content);
    scrollToBottom();
    console.log('Tokens recibidos')
  
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
}

function clear_chat() {
    $('#chat-list').html('');
    currentAssistantResponse = '';
    $('#key-container').empty();
    console.log('Se ha vaciado el chat!')
}

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
    console.log('Prompt enviado!')
    $('#user-input').val('');
    $('#user-input').focus();
    var message = $('<div class="user-message-container-'+n_responses+' user-message-container"><label>Yo</label><div class="user-message user-message-' + n_responses + '">' + userMessage + '</div></div>');
    var chatList = $('#chat-list');
    chatList.append(message);
    var divAssistant = $('<div class="assistant-message-container-'+n_responses+' assistant-message-container"><label>Asistente<br></label><div id="chat-assistant-'+n_responses+'" class="assistant-message"></div></div>');
    chatList.append(divAssistant);
    var botonCompartir = $('<button id="share" onclick="compartirChat(' + n_responses + ')">Compartir</button>');
    userMessageCointainer = $('.assistant-message-container-' + n_responses);
    userMessageCointainer.append(botonCompartir);
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
    clear_chat()
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
    clear_chat();
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
    console.log('Copiado al portapapeles!')
}
function toggleSidebar() {
    var sidebar = document.getElementById('sidebar');
    sidebar.style.display = (sidebar.style.display === 'none' || sidebar.style.display === '') ? 'block' : 'none';
}


function compartirChat(numeroRespuesta) {
    if (navigator.share) {
        var pregunta = $('.user-message-' + numeroRespuesta).text();
        var respuesta =  $('#chat-assistant-' + numeroRespuesta).html();
        var respuestaCompleta = "Yo: \n"+pregunta+"\n\nAsistente:\n"+respuesta
        respuestaCompleta = respuestaCompleta.replace(/<br>/g, '\n');
        navigator.share({
            title: pregunta,
            text: respuestaCompleta,
            url: 'VidriosDeLaTorre/VidrioAhumado' 
        })
        .then(() => console.log('Chat compartido con éxito'))
        .catch((error) => console.error('Error al compartir el chat:', error));
    } else {
        alert('La función de compartir no está soportada en este navegador.');
    }
}
