<h1> Proyecto de IA basado en LLama-2</h1>

Actualmente en fase de desarollo, pensado para ejecutar en local
para entornos en producción utilizar otro servidor wsgi

Instalar dependencias
con pip : 
<ul>
  <li>pip install Flask</li>
  <li>pip install flask_socketio</li>
  <li>pip instal CORS</li>
  <li>pip install llama-cpp-python</li>
</ul>




<span color="red>Instalar llama2 </span> > ver en <a href="https://github.com/abetlen/llama-cpp-python">repositorio oficial </a>

Descargar <a href="https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q8_0.gguf?download=true">modelo</a> y meterlo en la carpeta models.

Modo de empleo : 

<ul>
  <li>cd ruta/a/carpeta/del/proyecto</li>
  <li>python3 ./app.py </li>
</ul>

Se inicia el servidor en el localhost 127.0.0.1:5000

abrir en el navegador :D 


