"""
@Author: Borja Otero Ferreira
Data models for IALab Suite API
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class ChatMessage:
    """Represents a single chat message"""
    role: str
    content: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ChatHistory:
    """Represents a chat conversation history"""
    id: str
    name: str
    messages: List[ChatMessage]
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class ModelConfig:
    """Represents model configuration"""
    path: str
    temperature: float = 0.81
    gpu_layers: int = -1
    context_size: int = 8192
    system_message: str = ""
    chat_format: str = "chatml"

@dataclass
class UserInput:
    """Represents user input with additional parameters"""
    content: Any
    tools: Optional[bool] = False  # Boolean flag for tools usage
    rag: Optional[bool] = False    # Boolean flag for RAG usage
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
        # Asegurar que tools y rag siempre sean booleanos
        if self.tools is None:
            self.tools = False
        else:
            self.tools = bool(self.tools)  
            
        if self.rag is None:
            self.rag = False
        else:
            self.rag = bool(self.rag) 

@dataclass
class ApiResponse:
    """Standard API response format"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'success': self.success,
            'message': self.message,
            'data': self.data,
            'error': self.error,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
