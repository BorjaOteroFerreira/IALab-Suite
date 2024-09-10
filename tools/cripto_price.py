"""
@author: Borja Otero Ferreira
"""

import requests




class CriptoPrice():

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
        try:
            if not isinstance(criptos, list):
                raise ValueError("Input must be a list of cryptocurrency names.")
            
            if not criptos:
                raise ValueError("Provide a list of cryptocurrency names.")

            criptos_lower = [cripto.strip().lower() for cripto in criptos]
            cripto_ids = ','.join(criptos_lower)
            url = f'https://api.coingecko.com/api/v3/simple/price?ids={cripto_ids}&vs_currencies=usd'
            
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            precios = [f"{cripto}: {data[cripto]['usd']}$" for cripto in criptos_lower]
            precios_str = '\n'.join(precios)
            
            return precios_str
        except requests.exceptions.RequestException as e:
                return f"An error occurred while fetching prices: {e}"
        except Exception as e:
                return f"An error occurred: {e}"