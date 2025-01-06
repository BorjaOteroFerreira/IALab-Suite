// Manejador de WebSocket
class ManejadorWebSocket {
    constructor(dominio, puerto, ruta) {
        this.socket = io.connect(`http://${dominio}:${puerto}${ruta}`);
        this.configurarEscuchadores();
    }

    configurarEscuchadores() {
        this.socket.on('connect', () => this.alConectar());
    }

    alConectar() {
        console.log('¡Conectado! ✅');
    }
}

// Gestor de Interfaz de Usuario
class GestorUI {
    constructor() {
        this.configurarEscuchadoresEventos();
    }

    static mostrarNotificacion(mensaje, tipo = 'info') {
        let contenedor = this.obtenerOCrearContenedorNotificaciones();
        const notificacion = this.crearElementoNotificacion(mensaje, tipo);
        contenedor.appendChild(notificacion);
        this.animarNotificacion(notificacion, contenedor);
    }

    static obtenerOCrearContenedorNotificaciones() {
        let contenedor = document.getElementById('notification-container');
        if (!contenedor) {
            contenedor = document.createElement('div');
            contenedor.id = 'notification-container';
            contenedor.className = 'popup-container';
            contenedor.style.left = '20px';
            contenedor.style.bottom = '20px';
            document.body.appendChild(contenedor);
        }
        return contenedor;
    }

    static crearElementoNotificacion(mensaje, tipo) {
        const notificacion = document.createElement('div');
        notificacion.className = 'popup-notification';
        if (tipo === 'error') notificacion.classList.add('popup-error');
        notificacion.textContent = mensaje;
        return notificacion;
    }

    static animarNotificacion(notificacion, contenedor) {
        setTimeout(() => {
            notificacion.style.opacity = 1;
            setTimeout(() => {
                notificacion.style.opacity = 0;
                setTimeout(() => {
                    contenedor.removeChild(notificacion);
                    if (contenedor.childNodes.length === 0) {
                        document.body.removeChild(contenedor);
                    }
                }, 500);
            }, 5500);
        }, 100);
    }

    static desplazarAlFinal(elemento) {
        elemento.scrollTop = elemento.scrollHeight;
    }

    static ajustarAlturaTextarea(textarea) {
        const alturaLinea = parseFloat(getComputedStyle(textarea).lineHeight);
        const maxLineas = 20;
        const alturaMaxima = maxLineas * alturaLinea;
        textarea.style.height = '0';
        textarea.style.height = `${Math.min(textarea.scrollHeight, alturaMaxima)}px`;
    }

    configurarEscuchadoresEventos() {
        const textarea = document.getElementById('user-input');
        textarea.addEventListener('input', () => GestorUI.ajustarAlturaTextarea(textarea));
    }

    static alternarBarraLateral(elemento) {
        const barra = document.getElementById(elemento);
        const mediaQuerysActivas = window.matchMedia("(max-width: 1023px)").matches || 
                                 window.matchMedia("(max-height: 740px)").matches;

        if (!mediaQuerysActivas) {
            if (barra.style.display === 'none' || barra.style.display === '') {
                barra.style.display = 'flex';
                barra.style.width = '15%';
            } else {
                barra.style.display = 'none';
            }
        } else {
            if (barra.style.display === 'none' || barra.style.display === '') {
                barra.style.display = 'block';
                barra.style.width = '100%';
            } else {
                barra.style.display = 'none';
            }
        }
    }
}

// Gestor de Conversaciones
class GestorConversaciones {
    constructor(mensajeSistema) {
        this.historial = [{ role: 'system', content: mensajeSistema }];
        this.respuestaActual = '';
        this.respuestaCompleta = '';
        this.idChat = ' ';
        this.conversacionIniciada = false;
    }

    agregarMensajeUsuario(mensaje) {
        this.historial.push({ role: 'user', content: mensaje });
    }

    agregarMensajeAsistente(mensaje) {
        this.historial.push({ role: 'assistant', content: mensaje });
    }

    limpiarHistorial() {
        this.historial = [this.historial[0]]; // Mantener mensaje del sistema
        this.respuestaActual = '';
        this.respuestaCompleta = '';
        this.idChat = ' ';
    }

    generarIdChat(mensajeUsuario) {
        const fechaActual = new Date();
        const fechaFormateada = `${fechaActual.getFullYear()}.${fechaActual.getMonth() + 1}.${fechaActual.getDate()}.${fechaActual.getHours()}.${fechaActual.getMinutes()}.${fechaActual.getSeconds()}`;
        const mensajeRecortado = mensajeUsuario.substring(0, 35).trim();
        return `${fechaFormateada}-${mensajeRecortado}`.replace(' ', '_');
    }

    guardarHistorial(idChat, contenido) {
        $.ajax({
            type: 'POST',
            url: '/actualizar_historial',
            data: JSON.stringify({ nombre_chat: idChat, historial: contenido }),
            contentType: 'application/json',
            success: function(data) {
                console.log('Historial guardado con éxito');
            },
            error: function(error) {
                console.error('Error al guardar el historial:', error);
            }
        });
    }

    cargarHistorial(nombreChat) {
        nombreChat = String(nombreChat);
        const self = this;
        $.ajax({
            type: 'GET',
            url: `/recuperar_historial?nombre_chat=${nombreChat}`,
            contentType: 'application/json',
            success: function(data) {
                if (data && Array.isArray(data)) {
                    self.historial = data;
                    self.idChat = nombreChat;
                    console.log('Historial cargado exitosamente:', self.historial);
                } else {
                    console.error('Error: No se pudieron recuperar datos válidos del historial.');
                }
                self.cargarMensajes();
            },
            error: function(error) {
                GestorUI.mostrarNotificacion('Error cargando historial', 'error');
                console.error('Error al cargar el historial:', error);
            }
        });
    }

    eliminarHistorial(nombreChat) {
        const self = this;
        $.ajax({
            url: `/eliminar_historial?nombre_chat=${nombreChat}`,
            type: 'DELETE',
            success: function(result) {
                console.log(`Historial ${nombreChat} eliminado exitosamente.`);
                self.eliminarDeListaConversaciones(nombreChat);
            },
            error: function(xhr, status, error) {
                console.error(`Error al eliminar el historial ${nombreChat}: ${xhr.status}`);
            }
        });
    }

    eliminarDeListaConversaciones(idChat) {
        const listaConversaciones = $('#conversations-list');
        const elementoAEliminar = $('#' + idChat);
        if (elementoAEliminar.length) {
            elementoAEliminar.remove();
        } else {
            const selectorIdFormateado = '.load-history[id^="' + idChat + '"]';
            const elementoAEliminarFormateado = $(selectorIdFormateado);
            if (elementoAEliminarFormateado.length) {
                elementoAEliminarFormateado.remove();
            } else {
                console.error(`Elemento con ID ${idChat} no encontrado en la lista de conversaciones.`);
            }
        }
    }

    cargarMensajes() {
        $('#chat-list').empty();
        for (let i = 0; i < this.historial.length; i++) {
            const mensajeData = this.historial[i];
            if (mensajeData.role === 'system') continue;

            const converter = new showdown.Converter();
            const contenidoHtml = converter.makeHtml(mensajeData.content);

            if (mensajeData.role === 'user') {
                const mensaje = $(`
                    <div class="user-message-container-${i} user-message-container">
                        <label for="chat-user-${i}">Usuario</label>
                        <div id="chat-user-${i}" class="user-message user-message-${i}">
                            ${this.escaparHtml(mensajeData.content)}
                        </div>
                    </div>`);
                $('#chat-list').append(mensaje);
            } else if (mensajeData.role === 'assistant') {
                const divAsistente = $(`
                    <div class="assistant-message-container-${i} assistant-message-container">
                        <label for="chat-assistant-${i}">Asistente<br></label>
                        <div id="chat-assistant-${i}" class="assistant-message">
                            ${contenidoHtml}
                        </div>
                    </div>`);
                $('#chat-list').append(divAsistente);
                divAsistente.find('pre code').each(function(i, block) {
                    Prism.highlightElement(block);
                });
            }
        }
    }
}

// Gestor de Tokens
class GestorTokens {
    constructor() {
        this.totalTokens = 0;
        this.totalTokensRespuesta = 0;
    }

    actualizarTokens(tokensRespuesta) {
        this.totalTokens += tokensRespuesta;
        this.actualizarVisualizacion();
    }

    actualizarVisualizacion() {
        const etiqueta = document.getElementById('tokens');
        etiqueta.textContent = ` ${this.totalTokens} Tokens`;
    }

    reiniciar() {
        this.totalTokens = 0;
        this.totalTokensRespuesta = 0;
        this.actualizarVisualizacion();
    }
}

// Clase Principal Chat
class Chat {
    constructor() {
        this.inicializar();
        this.configurarComponentes();
        this.configurarEscuchadores();
        GestorUI.ajustarAlturaTextarea(document.getElementById('user-input'));
    }

    // Método para alternar la barra lateral
    toggleSidebar(elementId) {
            GestorUI.alternarBarraLateral(elementId);
    }

    inicializar() {
        this.herramientas = false;
        this.rag = false;
        this.biblioteca = 'llama';
        this.numRespuestas = 0;
        this.mensajeSistema = 'Eres un asistente en español. Debes responder siempre en español';
    }

    configurarComponentes() {
        this.manejadorWS = new ManejadorWebSocket(document.domain, location.port, '/test');
        this.gestorUI = new GestorUI();
        this.gestorConversaciones = new GestorConversaciones(this.mensajeSistema);
        this.gestorTokens = new GestorTokens();
        
        this.manejadorWS.socket.on('assistant_response', respuesta => this.manejarRespuestaAsistente(respuesta));
        this.manejadorWS.socket.on('output_console', respuesta => this.manejarSalidaConsola(respuesta));
        this.manejadorWS.socket.on('utilidades', respuesta => this.manejarUtilidades(respuesta));
    }

    configurarEscuchadores() {
        const checkboxHerramientas = document.getElementById('checkbox-3');
        const checkboxRag = document.getElementById('checkbox-4');
        const areaTexto = document.getElementById('user-input');

        checkboxHerramientas.addEventListener('change', () => this.herramientas = checkboxHerramientas.checked);
        checkboxRag.addEventListener('change', () => this.rag = checkboxRag.checked);
        areaTexto.addEventListener('keydown', (e) => {
            if (e.which === 13 && !e.shiftKey) {
                e.preventDefault();
                this.enviarMensaje();
                GestorUI.ajustarAlturaTextarea(areaTexto);
            }
        });

        $('#stop-button').hide();
    }

    manejarRespuestaAsistente(respuesta) {
        let delta = '';
        let deltaEleccion = '';
        
        if (this.biblioteca === 'ollama') {
            delta = respuesta.content;
            this.gestorConversaciones.respuestaCompleta += delta;
            const tokensUsuarioTotal = respuesta.total_user_tokens;
            const tokensAsistenteTotal = respuesta.total_assistant_tokens;
            this.gestorTokens.totalTokensRespuesta = tokensUsuarioTotal + tokensAsistenteTotal;
        } else {
            const datosRespuesta = respuesta.content.choices[0];
            deltaEleccion = datosRespuesta.delta && Object.keys(datosRespuesta.delta).length !== 0 
                ? datosRespuesta.delta.content 
                : '';
            this.gestorConversaciones.respuestaCompleta += deltaEleccion;
            this.gestorTokens.totalTokensRespuesta = respuesta.total_user_tokens + respuesta.total_assistant_tokens;
        }

        $('#stop-button').show();
        $('#send-button').prop('disabled', true).hide();

        const respuestaModelo = this.biblioteca === 'ollama' ? delta : deltaEleccion;
        this.procesarRespuestaAsistente(respuestaModelo);
        GestorUI.desplazarAlFinal($('#chat-container')[0]);
    }

    procesarRespuestaAsistente(respuesta) {
        respuesta = respuesta.replace(/<0x0A>/g, '\n');

        if (!this.gestorConversaciones.conversacionIniciada) {
            this.gestorConversaciones.respuestaActual = respuesta;
            this.gestorConversaciones.conversacionIniciada = true;
        } else {
            this.gestorConversaciones.respuestaActual += respuesta;
        }

        const converter = new showdown.Converter();
        const respuestaHtml = converter.makeHtml(this.gestorConversaciones.respuestaActual);

        // Procesar tablas
        const regexTabla = /(?:\|.*(?:\|).*)+\|/gs;
        let respuestaHtmlProcesada = respuestaHtml.replace(regexTabla, (tabla) => {
            const filas = tabla.trim().split('\n')
                .map(fila => fila.trim().split('|')
                .filter(celda => celda.trim() !== ''));
            const filasFiltradas = filas.filter(fila => !fila.some(celda => celda.includes('---')));
            
            let tablaHtml = '<table>';
                filasFiltradas.forEach((fila, i) => {
                    tablaHtml += '<tr>';
                    fila.forEach(celda => {
                        tablaHtml += i === 0 
                            ? `<th>${celda}</th>` 
                            : `<td>${celda}</td>`;
                    });
                    tablaHtml += '</tr>';
                });
                tablaHtml += '</table>';
                return tablaHtml;
            });
        // Encontrar el contenedor específico para esta respuesta
        const divAsistente = $(`#chat-assistant-${this.numRespuestas}`);
        if (divAsistente.length === 0) {
            console.error(`No se encontró el contenedor para la respuesta ${this.numRespuestas}`);
            return;
        }

        // Actualizar solo el contenedor específico
        divAsistente.html(respuestaHtmlProcesada);

        // Aplicar formato a los bloques de código
        divAsistente.find('pre').addClass('line-numbers');
        divAsistente.find('pre code').each((i, bloque) => {
            Prism.highlightElement(bloque);
        });

        }
    
        manejarSalidaConsola(respuesta) {
            const divConsola = $('#consola');
            const { role, content } = respuesta;
            let divRespuesta;
            
            if (role === 'info') {
                divRespuesta = $(`<div id="outputConsole"><pre class="${role}">ialab-suite@agent:~$ ${content}</pre></div>`);
            } else {
                divRespuesta = $(`<div id="outputConsole"><pre class="${role}">${content}</pre></div>`);
            }
            
            divConsola.append(divRespuesta);
            GestorUI.desplazarAlFinal(divConsola[0]);
        }
    
        manejarUtilidades(respuesta) {
            const divResultados = document.getElementById(`resultados${this.numRespuestas}`);
            
            respuesta.ids.forEach(id => {
                const iframe = document.createElement('iframe');
                iframe.width = "64px";
                iframe.height = "32px";
                iframe.src = `https://www.youtube.com/embed/${id}`;
                iframe.frameborder = "0";
                iframe.allow = "encrypted-media; picture-in-picture";
                iframe.allowfullscreen = true;
                divResultados.appendChild(iframe);
            });
        }
    
        enviarMensaje() {
            if (!this.gestorConversaciones.conversacionIniciada) {
                const entradaUsuario = $('#user-input').val();
                if (!entradaUsuario.trim()) return;
    
                this.prepararNuevoMensaje(entradaUsuario);
                this.enviarMensajeAlServidor(entradaUsuario);
            }
        }
    
        prepararNuevoMensaje(entradaUsuario) {
            this.gestorConversaciones.conversacionIniciada = true;
            this.numRespuestas++;
            
            if (this.gestorConversaciones.idChat === ' ') {
                this.gestorConversaciones.idChat = this.gestorConversaciones.generarIdChat(entradaUsuario);
            }
    
            this.gestorConversaciones.agregarMensajeUsuario(this.escaparHtml(entradaUsuario));
            this.agregarMensajeUsuarioUI(entradaUsuario);
            
            $('#user-input').val('').focus();
        }
    
        agregarMensajeUsuarioUI(mensaje) {
            const mensajeUsuario = $(`
                <div class="user-message-container-${this.numRespuestas} user-message-container">
                    <div id="chat-user-${this.numRespuestas}" class="user-message user-message-${this.numRespuestas}">
                        ${this.escaparHtml(mensaje)}
                    </div>
                </div>
            `);
    
            const divAsistente = $(`
                <div class="assistant-message-container-${this.numRespuestas} assistant-message-container">
                    <div id="contenedor_respuesta">
                        <div id="chat-assistant-${this.numRespuestas}" class="assistant-message"></div>
                        <div id="resultados${this.numRespuestas}" class="resultados"></div>
                    </div>
                </div>
            `);
    
            const botonCompartir = $(`<button id="share" onclick="chat.compartirChat(${this.numRespuestas})">Compartir</button>`);
            
            $('#chat-list').append(mensajeUsuario, divAsistente);
            $(`.assistant-message-container-${this.numRespuestas}`).append(botonCompartir);
            
            GestorUI.desplazarAlFinal($('#chat-container')[0]);
        }
    
        enviarMensajeAlServidor(entradaUsuario) {
            const url = this.biblioteca === 'ollama' ? 'v1/chat/completions' : '/user_input';
            const datos = {
                content: this.gestorConversaciones.historial,
                tools: this.herramientas,
                rag: this.rag
            };
    
            $.ajax({
                type: 'POST',
                url: url,
                data: JSON.stringify(datos),
                contentType: 'application/json',
                success: respuesta => this.manejarExitoEnvio(respuesta),
                error: error => this.manejarErrorEnvio(error)
            });
        }
    
        manejarExitoEnvio(respuesta) {
            $('#stop-button').hide();
            $('#send-button').show().prop('disabled', false);
            
            this.gestorConversaciones.agregarMensajeAsistente(this.gestorConversaciones.respuestaCompleta);
            this.gestorTokens.actualizarTokens(this.gestorTokens.totalTokensRespuesta);
    
            this.actualizarListaConversaciones();
            this.gestorConversaciones.guardarHistorial(
                this.gestorConversaciones.idChat, 
                this.gestorConversaciones.historial
            );
    
            GestorUI.mostrarNotificacion(respuesta);
            this.gestorConversaciones.conversacionIniciada = false;
        }
    
        manejarErrorEnvio(error) {
            GestorUI.mostrarNotificacion(error, 'error');
            console.error('Error:', error);
            this.gestorConversaciones.conversacionIniciada = false;
        }
    
        actualizarListaConversaciones() {
            const self = this;
            const listaConversaciones = $('#conversations-list');
            let existeBoton = false;
            // Recorre cada elemento de la clase '.load-history'
            $('.load-history').each(function() {
                if ($(this).text() === '❌' + self.gestorConversaciones.idChat) {
                    existeBoton = true;
                    return false; // Rompe el bucle si ya existe
                }
            });
            // Si el botón no existe, crea uno nuevo
            if (!existeBoton) {
                const nuevoHistorialChat = $(`
                    <div class='load-history' id='${self.gestorConversaciones.idChat}'>
                        <button height='1em' width='1em' onclick="chat.gestorConversaciones.eliminarHistorial('${self.gestorConversaciones.idChat}')">❌</button>
                        <button class='btnLoadHistory' onclick="chat.gestorConversaciones.cargarHistorial('${self.gestorConversaciones.idChat}')">
                            ${self.gestorConversaciones.idChat}
                        </button>
                    </div>
                `);
                listaConversaciones.prepend(nuevoHistorialChat);
            }
        }
        
        limpiarChat() {
            $('#chat-list').html('');
            this.gestorConversaciones.limpiarHistorial();
            this.gestorTokens.reiniciar();
            $('#key-container').empty();
            GestorUI.mostrarNotificacion('¡Chat vaciado! 🗑️');
        }
    
        aplicarConfiguracion() {
            const modeloSeleccionado = $('#model-select').val();
            const formatoSeleccionado = $('#format-select').val();
            const mensajeSistema = $('#system-message').val();
            const capasGPU = $('#gpu-layers').val();
            const temperatura = $('#temperature').val();
            const contexto = $('#context').val();
    
            $.ajax({
                type: "POST",
                url: "/load_model",
                data: {
                    model_path: modeloSeleccionado,
                    format: formatoSeleccionado,
                    temperature: temperatura,
                    system_message: mensajeSistema,
                    gpu_layers: capasGPU,
                    context: contexto
                },
                success: data => {
                    GestorUI.mostrarNotificacion('Modelo cargado exitosamente');
                    this.limpiarChat();
                },
                error: error => {
                    GestorUI.mostrarNotificacion(error, 'error');
                    console.error('Error:', error);
                }
            });
        }
    
        compartirChat(numeroRespuesta) {
            if (navigator.share) {
                const pregunta = $(`.user-message-${numeroRespuesta}`).text();
                const respuesta = $(`#chat-assistant-${numeroRespuesta}`).html();
                const respuestaCompleta = `Usuario: \n${pregunta}\n\nAsistente:\n${respuesta}`;
                
                navigator.share({
                    title: pregunta,
                    text: respuestaCompleta.replace(/<br>/g, '\n'),
                    url: '/'
                })
                .then(() => GestorUI.mostrarNotificacion('Chat compartido exitosamente'))
                .catch(error => console.error('Error al compartir chat:', error));
            } else {
                GestorUI.mostrarNotificacion('Función de compartir no soportada en este navegador. 😤', 'error');
            }
        }
    
        escaparHtml(texto) {
            const mapeo = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return texto.replace(/[&<>"']/g, m => mapeo[m]);
        }
    
        detenerRespuesta() {
            $.ajax({
                type: "POST",
                url: "/stop_response",
                success: data => {
                    console.log(data);
                    GestorUI.mostrarNotificacion(data);
                    $('#stop-button').hide();
                    $('#send-button').show();
                },
                error: error => {
                    GestorUI.mostrarNotificacion(error, 'error');
                    console.error('Error:', error);
                }
            });
        }
    }
    
// Exportar para su uso
window.Chat = Chat;