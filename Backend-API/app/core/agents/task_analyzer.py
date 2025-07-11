"""
@Author: Borja Otero Ferreira
Analizador de tareas del usuario para el agente autónomo
"""
import json
import re
from typing import Dict, Any, Optional, List
from app.utils.logger import logger


class TaskAnalyzer:
    """Analiza las tareas del usuario para determinar si necesitan procesamiento autónomo"""
    
    def __init__(self, model, tools_manager, tool_registry):
        self.model = model
        self.tools_manager = tools_manager
        self.tool_registry = tool_registry
    
    def analyze_user_task(self, original_prompt: List[Dict]) -> Optional[Dict[str, Any]]:
        """Analiza la tarea del usuario para determinar si necesita procesamiento autónomo"""
        try:
            # Obtener el último mensaje del usuario
            user_message = ""
            for message in reversed(original_prompt):
                if message['role'] == 'user':
                    user_message = message['content']
                    break
            
            if not user_message:
                return None
            
            # Crear prompt para análisis de tarea
            analysis_prompt = self._create_task_analysis_prompt(user_message)
            
            # Obtener análisis del modelo
            analysis_response = ""
            for chunk in self.model.create_chat_completion(messages=analysis_prompt, max_tokens=800, stream=True):
                if 'content' in chunk['choices'][0]['delta']:
                    analysis_response += chunk['choices'][0]['delta']['content']
            
            # Parsear la respuesta del análisis
            task_analysis = self._parse_task_analysis(analysis_response)
            
            if task_analysis and task_analysis.get('requires_tools', False):
                return task_analysis
            
            return None
            
        except Exception as e:
            logger.error(f"Error analizando tarea: {e}")
            return None

    def _create_task_analysis_prompt(self, user_message: str) -> List[Dict]:
        """Crea el prompt para análizar la tarea del usuario"""
        active_tools = []
        if self.tools_manager:
            active_tools = self.tools_manager.get_active_tools()
        
        tools_info = "Estas son las únicas herramientas disponibles que puedes utilizar, no te inventes nombes de herramientas:\n"
        for tool_name in active_tools:
            tool_info = self.tool_registry.get_tool_info(tool_name)
            if tool_info:
                tools_info += f"- {tool_name}: {tool_info.get('description', 'Sin descripción')}\n"
        
        analysis_prompt = [
            {
                "role": "system",
                "content": f"""Eres un asistente experto en análisis de tareas. Tu trabajo es determinar si una solicitud del usuario requiere el uso de herramientas externas y planificación de pasos.

{tools_info}

Analiza la solicitud del usuario y determina:
1. Si requiere herramientas externas (requires_tools: true/false)
2. El tipo de tarea (task_type: simple/research/analysis/creative/multi_step)
3. La complejidad (complexity: low/medium/high)
4. Los objetivos principales (objectives: lista de objetivos)
5. Las herramientas necesarias (tools_needed: lista de herramientas)

Responde ÚNICAMENTE en formato JSON válido:
{{
    "requires_tools": boolean,
    "task_type": "string",
    "complexity": "string",
    "objectives": ["objetivo1", "objetivo2"],
    "tools_needed": ["herramienta1", "herramienta2"],
    "reasoning": "explicación breve"
}}

Ejemplos de tareas que requieren herramientas:
- Buscar información actualizada
- Encontrar videos específicos
- Investigar temas complejos
- Análisis de datos externos

Ejemplos de tareas que NO requieren herramientas:
- Explicaciones teóricas
- Escritura creativa
- Cálculos matemáticos simples
- Consejos generales"""
            },
            {
                "role": "user",
                "content": f"Analiza esta solicitud: {user_message}"
            }
        ]
        
        return analysis_prompt

    def _parse_task_analysis(self, analysis_response: str) -> Optional[Dict[str, Any]]:
        """Parsea la respuesta del análisis de tarea"""
        try:
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{.*\}', analysis_response, re.DOTALL)
            if not json_match:
                return None
            
            json_str = json_match.group(0)
            analysis = json.loads(json_str)
            
            # Validar estructura mínima
            required_fields = ['requires_tools', 'task_type', 'complexity']
            if not all(field in analysis for field in required_fields):
                return None
            
            return analysis
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parseando análisis de tarea: {e}")
            return None
