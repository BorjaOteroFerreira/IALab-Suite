"""
@author: Borja Otero Ferreira
"""

import requests
from .base_tool import BaseTool, ToolMetadata, ToolCategory

class CriptoPrice(BaseTool):
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="Precios Criptomonedas",
            description="Obtiene el precio actual de criptomonedas en USD",
            category=ToolCategory.FINANCE,
            requires_api_key=False,
            usage_example={
                "búsqueda_simple": '{"tool": "cripto_price", "query": "bitcoin"}',
                "varias_criptos": '{"tool": "cripto_price", "query": ["bitcoin", "ethereum", "dogecoin"]}',
                "formato_lista": '{"tool": "cripto_price", "query": "bitcoin, ethereum, solana"}',
                "formatos_soportados": [
                    'query: nombre o lista de nombres de criptomonedas (string o lista de strings)'
                ]
            }
        )
    
    @classmethod
    def get_tool_name(cls) -> str:
        return "Precios Criptomonedas"
    
    def execute(self, query: str, **kwargs):
        """Ejecuta consulta de precios de criptomonedas"""
        # Convertir query string a lista si es necesario
        if isinstance(query, str):
            criptos = [c.strip() for c in query.split(',')]
        else:
            criptos = query
        return self.get_price(criptos)

    @staticmethod
    def get_price(criptos: list):
        """
        Fetches the current price of cryptocurrencies in USD from CoinGecko.
        
        Parameters:
        criptos : list
            A list of cryptocurrency names.
        
        Returns:
            str: A formatted string containing the prices in USD of the specified cryptocurrencies.
        """
        precios = "Precios"
  
        try:
            if not isinstance(criptos, list):
                raise ValueError("Input must be a list of cryptocurrency names.")
            
            if not criptos:
                raise ValueError("Provide a list of cryptocurrency names.")

            criptos_lower = [cripto.strip().lower() for cripto in criptos]
            for cripto in criptos_lower:
                url = f'https://api.coingecko.com/api/v3/simple/price?ids={cripto}&vs_currencies=usd'
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                
                precios += f"{cripto}: {data[cripto]['usd']}$\n"
              
            
            return precios
        except requests.exceptions.RequestException as e:
                return f"An error occurred while fetching prices: {e}"
        except Exception as e:
                return f"An error occurred: {e}"