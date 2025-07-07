"""
@Author: Borja Otero Ferreira
Default Agent Configuration - Configuración para el agente default
Define constantes y configuraciones específicas del agente default
"""

class DefaultAgentConfig:
    """
    Configuración para el agente default
    Contiene constantes y parámetros de configuración
    """
    
    # Configuración de iteraciones
    MAX_ITERATIONS = 3  # Máximo número de iteraciones para detección de herramientas
    
    # Configuración de socket
    ENABLE_SOCKET_EMISSION = True  # Habilitar emisión de mensajes via socket
    
    # Configuración de logging
    ENABLE_DETAILED_LOGGING = True  # Habilitar logging detallado
    
    # Configuración de herramientas
    ENABLE_TOOL_VALIDATION = True  # Habilitar validación de herramientas
    ENABLE_TOOL_ITERATION = True  # Habilitar iteración de herramientas
    
    # Configuración de timeouts
    TOOL_EXECUTION_TIMEOUT = 30  # Timeout en segundos para ejecución de herramientas
    MODEL_RESPONSE_TIMEOUT = 60  # Timeout en segundos para respuesta del modelo
    
    # Configuración de prompts
    MAX_PROMPT_LENGTH = 128000  # Longitud máxima de prompt
    MAX_RESPONSE_LENGTH = 8192  # Longitud máxima de respuesta
    
    # Configuración de patrones JSON
    ENABLE_JSON_PATTERN_DETECTION = True  # Habilitar detección de patrones JSON
    ENABLE_BASIC_PATTERN_FALLBACK = True  # Habilitar fallback a patrones básicos
    
    # Configuración de errores
    MAX_ERROR_RETRIES = 2  # Máximo número de reintentos en caso de error
    ENABLE_ERROR_RECOVERY = True  # Habilitar recuperación de errores
    
    @classmethod
    def get_config_dict(cls):
        """Retorna la configuración como diccionario"""
        config = {}
        for attr in dir(cls):
            if not attr.startswith('_') and not callable(getattr(cls, attr)):
                config[attr] = getattr(cls, attr)
        return config
    
    @classmethod
    def validate_config(cls):
        """Valida la configuración"""
        errors = []
        
        if cls.MAX_ITERATIONS <= 0:
            errors.append("MAX_ITERATIONS debe ser mayor que 0")
            
        if cls.TOOL_EXECUTION_TIMEOUT <= 0:
            errors.append("TOOL_EXECUTION_TIMEOUT debe ser mayor que 0")
            
        if cls.MODEL_RESPONSE_TIMEOUT <= 0:
            errors.append("MODEL_RESPONSE_TIMEOUT debe ser mayor que 0")
            
        if cls.MAX_PROMPT_LENGTH <= 0:
            errors.append("MAX_PROMPT_LENGTH debe ser mayor que 0")
            
        if cls.MAX_RESPONSE_LENGTH <= 0:
            errors.append("MAX_RESPONSE_LENGTH debe ser mayor que 0")
            
        if cls.MAX_ERROR_RETRIES < 0:
            errors.append("MAX_ERROR_RETRIES debe ser mayor o igual a 0")
        
        return errors
