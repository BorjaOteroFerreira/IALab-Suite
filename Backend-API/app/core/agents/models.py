"""
@Author: Borja Otero Ferreira
Modelos de datos para el sistema de agente autónomo
"""
import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class TaskStatus(Enum):
    """Estados posibles de una tarea o paso"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskStep:
    """Representa un paso individual en la ejecución de una tarea"""
    id: str
    description: str
    tool_name: str
    query: str
    dependencies: List[str]
    status: TaskStatus
    result: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2


@dataclass
class TaskPlan:
    """Representa un plan completo de ejecución de tareas"""
    task_description: str
    steps: List[TaskStep]
    context: Dict[str, Any]
    created_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    status: TaskStatus = TaskStatus.PENDING
