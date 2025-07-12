class BaseAgent:
    """
    Clase base para todos los agentes. Los agentes deben heredar de esta clase para ser autodetectados.
    """
    def get_agent_info(self):
        raise NotImplementedError("El agente debe implementar get_agent_info().")

    def get_response(self):
        raise NotImplementedError("El agente debe implementar get_response().")
