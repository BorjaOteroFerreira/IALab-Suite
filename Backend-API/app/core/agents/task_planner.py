"""
@Author: Borja Otero Ferreira
Planificador de tareas para el agente autónomo
"""
import json
import re
import datetime
from typing import Dict, Any, Optional, List
from .models import TaskPlan, TaskStep, TaskStatus
from app.utils.logger import logger


class TaskPlanner:
    """Crea planes de ejecución detallados basados en el análisis de tareas"""
    
    def __init__(self, model, tools_manager, tool_registry):
        self.model = model
        self.tools_manager = tools_manager
        self.tool_registry = tool_registry
    
    def create_execution_plan(self, task_analysis: Dict[str, Any], original_prompt: List[Dict]) -> Optional[TaskPlan]:
        """Crea un plan de ejecución detallado basado en el análisis"""
        try:
            # Crear prompt para planificación
            planning_prompt = self._create_planning_prompt(task_analysis, original_prompt)
            
            # Obtener plan del modelo
            plan_response = ""
            for chunk in self.model.create_chat_completion(messages=planning_prompt, max_tokens=1200, stream=True):
                if 'content' in chunk['choices'][0]['delta']:
                    plan_response += chunk['choices'][0]['delta']['content']
            
            # Parsear el plan
            parsed_plan = self._parse_execution_plan(plan_response, task_analysis)
            
            return parsed_plan
            
        except Exception as e:
            logger.error(f"Error creando plan de ejecución: {e}")
            return None

    def _create_planning_prompt(self, task_analysis: Dict[str, Any], original_prompt: List[Dict]) -> List[Dict]:
        """Crea el prompt para planificación de ejecución"""
        active_tools = []
        if self.tools_manager:
            active_tools = self.tools_manager.get_active_tools()
        
        tools_info = "Herramientas disponibles:\n"
        for tool_name in active_tools:
            tool_info = self.tool_registry.get_tool_info(tool_name)
            if tool_info:
                tools_info += f"- {tool_name}: {tool_info.get('description', 'Sin descripción')}\n"
        
        user_message = ""
        for message in reversed(original_prompt):
            if message['role'] == 'user':
                user_message = message['content']
                break
        
        planning_prompt = [
            {
                "role": "system",
                "content": f"""Eres un planificador experto. Tu trabajo es crear un plan detallado de ejecución para completar la tarea del usuario.

{tools_info}

Análisis de la tarea:
- Tipo: {task_analysis.get('task_type', 'unknown')}
- Complejidad: {task_analysis.get('complexity', 'unknown')}
- Objetivos: {task_analysis.get('objectives', [])}
- Herramientas necesarias: {task_analysis.get('tools_needed', [])}

Crea un plan paso a paso en formato JSON:
{{
    "task_description": "descripción clara de la tarea",
    "steps": [
        {{
            "id": "step_1",
            "description": "descripción del paso",
            "tool_name": "nombre_herramienta",
            "query": "consulta específica",
            "dependencies": ["step_anterior"],
            "reasoning": "por qué este paso es necesario"
        }}
    ],
    "success_criteria": "cómo saber si la tarea se completó exitosamente"
}}

Reglas importantes:
1. Solo usa herramientas disponibles en la lista
2. Ordena los pasos lógicamente
3. Especifica dependencias entre pasos
4. Haz consultas específicas y claras
5. Máximo 8 pasos por plan
6. Cada paso debe tener un propósito claro"""
            },
            {
                "role": "user",
                "content": f"Crea un plan para: {user_message}"
            }
        ]
        
        return planning_prompt

    def _parse_execution_plan(self, plan_response: str, task_analysis: Dict[str, Any]) -> Optional[TaskPlan]:
        """Parsea la respuesta del plan de ejecución"""
        try:
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{.*\}', plan_response, re.DOTALL)
            if not json_match:
                return None
            
            json_str = json_match.group(0)
            plan_data = json.loads(json_str)
            
            # Crear objetos TaskStep
            steps = []
            for i, step_data in enumerate(plan_data.get('steps', [])):
                step = TaskStep(
                    id=step_data.get('id', f'step_{i+1}'),
                    description=step_data.get('description', 'Sin descripción'),
                    tool_name=step_data.get('tool_name', ''),
                    query=step_data.get('query', ''),
                    dependencies=step_data.get('dependencies', []),
                    status=TaskStatus.PENDING
                )
                steps.append(step)
            
            # Crear TaskPlan
            task_plan = TaskPlan(
                task_description=plan_data.get('task_description', 'Tarea sin descripción'),
                steps=steps,
                context={'analysis': task_analysis, 'success_criteria': plan_data.get('success_criteria', '')},
                created_at=datetime.datetime.now(),
                status=TaskStatus.PENDING
            )
            
            return task_plan
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parseando plan de ejecución: {e}")
            return None

    def display_execution_plan(self, current_plan: TaskPlan, emit_status_func):
        """Muestra el plan de ejecución al usuario"""
        if not current_plan:
            return
        
        plan_text = f"📋 **Plan de Ejecución**\n\n"
        plan_text += f"**Tarea:** {current_plan.task_description}\n\n"
        plan_text += f"**Pasos a ejecutar:**\n"
        
        for i, step in enumerate(current_plan.steps, 1):
            plan_text += f"{i}. **{step.description}**\n"
            plan_text += f"   - Herramienta: `{step.tool_name}`\n"
            plan_text += f"   - Consulta: `{step.query}`\n"
            if step.dependencies:
                plan_text += f"   - Depende de: {', '.join(step.dependencies)}\n"
            plan_text += "\n"
        
        emit_status_func(plan_text)
        logger.info(f"Plan de ejecución mostrado: {len(current_plan.steps)} pasos")
