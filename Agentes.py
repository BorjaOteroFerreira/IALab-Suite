import os
os.environ["OPENAI_API_KEY"] = "hola"
os.environ["OPENAI_API_BASE"] = "http://localhost:8080/v1/"
import duckduckgo_search
from duckduckgo_search import duckduckgo_search_async
from crewai import Agent,Task
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun
from langchain_community import agent_toolkits

search_tool = DuckDuckGoSearchRun()
output_file = 'nuevo_articulo.md'
# Tema para la ejecución de la tripulacion
tema = 'Avances en exploración espacial'

# Creación de un agente investigador senior con memoria y modo detallado
investigador = Agent(
  role='Investigador Senior',
  goal=f'Descubrir tecnologías innovadoras en {tema}',
  verbose=True,
  memory=True,
  backstory="""Impulsado por la curiosidad, estás a la vanguardia de
  la innovación, ansioso por explorar y compartir conocimientos que podrían cambiar
  el mundo.""",
  herramientas=[search_tool],
  allow_delegation=True
)

# Creación de un agente escritor con herramientas personalizadas y capacidad de delegación
escritor = Agent(
  role='Escritor',
  goal=f'Narrar historias  convincentes sobre {tema}',
  verbose=True,
  memory=True,
  backstory="""Con un talento para simplificar temas complejos, creas
  narrativas cautivadoras que cautivan y educan, revelando nuevos
  descubrimientos de una manera accesible.""",
  tools=[search_tool],
  allow_delegation=False
)

traductor = Agent(
  role='Traductor',
  goal=f'Traducir textos del ingles al español {tema}',
  verbose=True,
  memory=True,
  backstory="""Con un talento increible para el idioma español, 
  como experto traductor senior te encanta traducir informes al español.""",
  allow_delegation=False
)


from crewai import Task

# Tarea de investigación
tarea_investigacion = Task(
  description=f"""Identificar la próxima gran tendencia en {tema}.
  Concéntrate en identificar pros y contras y la narrativa general.
  Tu informe final debería articular claramente los puntos clave,
  sus oportunidades de mercado y posibles riesgos.""",
  expected_output=f'Un informe completo de 3 párrafos sobre las últimas tendencias en {tema}',
  tools=[search_tool],
  agent=investigador,
)

# Tarea de escritura con configuración del modelo de lenguaje
tarea_escritura = Task(
  description=f"""Redactar un artículo perspicaz sobre {tema}.
  Concéntrate en las últimas tendencias y cómo impactan en la industria.
  Este artículo debe ser fácil de entender, atractivo y positivo.
  Debes asegurarte de redactarlo en idioma español.""",
  expected_output=f'Un artículo en español de 4 párrafos sobre los avances en {tema} formateado en markdown.',
  tools=[search_tool],
  agent=escritor,
  output_file=output_file
)
# Tarea de traduccion con configuración del modelo de lenguaje
tarea_traduccion = Task(
  description=f"""Traducir informe anterior al español.""",
  expected_output=f'una traduccion completa al español',
  agent=traductor,
  async_execution=False,


)


from crewai import Crew, Process

#Preparando la tripulacion 
crew = Crew(
  agents=[investigador,escritor, ],
  tasks=[tarea_investigacion, tarea_escritura ],
  process=Process.sequential  # Optional: Sequential task execution is default
)
#Patada en el culo y a correr
result = crew.kickoff()

os.system('clear')
print("Este es el resultado para nuevo_articulo.md")
print("===============================")
print(result)
