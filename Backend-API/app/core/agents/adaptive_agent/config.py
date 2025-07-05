"""
@Author: Borja Otero Ferreira
Configuración del Agente Adaptativo
"""
import os
from typing import Dict, Any


class AdaptiveAgentConfig:
    """Configuración para el agente adaptativo"""
    
    # Configuración del modo adaptativo
    ADAPTIVE_MODE_ENABLED = True  # Por defecto usar modo adaptativo
    
    # Configuración de iteraciones
    MAX_ADAPTIVE_ITERATIONS = 15  # Máximo de pasos en modo adaptativo
    MAX_TRADITIONAL_ITERATIONS = 10  # Máximo en modo tradicional
    
    # Configuración de reflexión
    REFLECTION_ENABLED = True  # Habilitar reflexión entre pasos
    REFLECTION_VERBOSITY = "medium"  # low, medium, high
    
    # Configuración de tiempo
    STEP_DELAY_SECONDS = 0.5  # Pausa entre pasos para procesamiento
    
    # Configuración de herramientas
    TOOL_TIMEOUT_SECONDS = 30  # Timeout para ejecución de herramientas
    
    # Configuración de confianza
    MIN_CONFIDENCE_LEVEL = "bajo"  # Nivel mínimo de confianza para continuar
    
    # Configuración de respuesta
    MAX_RESPONSE_TOKENS = 800  # Máximo de tokens para reflexión
    MAX_STEP_TOKENS = 500  # Máximo de tokens para generación de pasos
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Obtiene la configuración actual como diccionario"""
        return {
            "adaptive_mode_enabled": cls.ADAPTIVE_MODE_ENABLED,
            "max_adaptive_iterations": cls.MAX_ADAPTIVE_ITERATIONS,
            "max_traditional_iterations": cls.MAX_TRADITIONAL_ITERATIONS,
            "reflection_enabled": cls.REFLECTION_ENABLED,
            "reflection_verbosity": cls.REFLECTION_VERBOSITY,
            "step_delay_seconds": cls.STEP_DELAY_SECONDS,
            "tool_timeout_seconds": cls.TOOL_TIMEOUT_SECONDS,
            "min_confidence_level": cls.MIN_CONFIDENCE_LEVEL,
            "max_response_tokens": cls.MAX_RESPONSE_TOKENS,
            "max_step_tokens": cls.MAX_STEP_TOKENS
        }
    
    @classmethod
    def set_adaptive_mode(cls, enabled: bool):
        """Cambiar modo adaptativo"""
        cls.ADAPTIVE_MODE_ENABLED = enabled
    
    @classmethod
    def set_reflection_verbosity(cls, level: str):
        """Cambiar nivel de verbosidad de reflexión"""
        if level.lower() in ["low", "medium", "high"]:
            cls.REFLECTION_VERBOSITY = level.lower()
    
    @classmethod
    def is_adaptive_mode(cls) -> bool:
        """Verificar si el modo adaptativo está habilitado"""
        return cls.ADAPTIVE_MODE_ENABLED
    
    @classmethod
    def load_from_env(cls):
        """Cargar configuración desde variables de entorno"""
        cls.ADAPTIVE_MODE_ENABLED = os.getenv('ADAPTIVE_MODE_ENABLED', 'true').lower() == 'true'
        cls.MAX_ADAPTIVE_ITERATIONS = int(os.getenv('MAX_ADAPTIVE_ITERATIONS', '15'))
        cls.REFLECTION_VERBOSITY = os.getenv('REFLECTION_VERBOSITY', 'medium').lower()
        cls.STEP_DELAY_SECONDS = float(os.getenv('STEP_DELAY_SECONDS', '0.5'))
        cls.TOOL_TIMEOUT_SECONDS = int(os.getenv('TOOL_TIMEOUT_SECONDS', '30'))


# Cargar configuración desde variables de entorno al importar
AdaptiveAgentConfig.load_from_env()
