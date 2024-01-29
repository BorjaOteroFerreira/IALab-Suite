var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
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
    chatList.html('<li class="assistant-message">' + currentAssistantResponse + '</li>');
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


