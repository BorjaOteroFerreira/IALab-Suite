import requests
from .base_tool import BaseTool, ToolMetadata, ToolCategory

class IpInfoTool(BaseTool):
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="Ip Lookup",
            description="Obtiene información geográfica y detalles sobre una dirección IP",
            category=ToolCategory.UTILITY,
            requires_api_key=False
        )
    
    def execute(self, query: str, **kwargs):
        """Obtiene información de una dirección IP"""
        return self.get_ip_info(query)
    
    @staticmethod
    def get_ip_info(ip_address):
        """Fetches geolocation and other information about a given IP address."""
        url = f"https://freeipapi.com/api/json/{ip_address}"

        try:
            # Realizar la solicitud HTTP para obtener la información de la IP
            response = requests.get(url)

            # Verificar que la solicitud fue exitosa
            if response.status_code == 200:
                data = response.json()

                # Devolver la información de la IP en formato de texto
                ip_info = (
                    f"Información de la IP proporcionada:\n"
                    f"Dirección IP: {data.get('ipAddress')}\n"
                    f"Versión de IP: {data.get('ipVersion')}\n"
                    f"Ubicación: {data.get('cityName')}, {data.get('regionName')}, {data.get('countryName')}\n"
                    f"Código de país: {data.get('countryCode')}\n"
                    f"Código postal: {data.get('zipCode')}\n"
                    f"Latitud: {data.get('latitude')}\n"
                    f"Longitud: {data.get('longitude')}\n"
                    f"Zona horaria: {data.get('timeZone')}\n"
                    f"ISP: {data.get('isProxy')}\n"
                )

                return ip_info
            else:
                return f"Error al obtener información de la IP: {response.status_code}"

        except Exception as e:
            return f"Error al obtener información de la IP: {str(e)}"
    
    @classmethod
    def get_tool_name(cls) -> str:
        return "Ip Lookup"
