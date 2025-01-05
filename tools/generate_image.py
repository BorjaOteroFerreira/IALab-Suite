import os
import shutil
from typing import List
from pydantic import BaseModel, Field
from langchain.tools import tool
from gradio_client import Client
from huggingface_hub import login


class ImageGenerationResult(BaseModel):
    file_path: str

class ImageGenerationToolInput(BaseModel):
    """Input para la herramienta de generación de imágenes."""
    prompt: str = Field(..., description="El prompt para generar la imagen.")
    width: int = Field(1024, description="El ancho de la imagen.")
    height: int = Field(1024, description="La altura de la imagen.")
    guidance_scale: float = Field(3.5, description="El guidance scale.")
    num_inference_steps: int = Field(28, description="El número de pasos de inferencia.")
    randomize_seed: bool = Field(True, description="Si se debe aleatorizar la semilla.")
    seed: float = Field(0, description="La semilla utilizada.")

class ImageGenerationTool:
    @staticmethod
    @tool("Generate Image with Flux")
    def run(
        prompt: str,
        width: int = 512,
        height: int = 512,
        guidance_scale: float = 3.5,
        num_inference_steps: int = 18,
        randomize_seed: bool = True,
        seed: float = 0
    ) -> List[ImageGenerationResult]:
        """
        Genera una imagen basándose en un prompt usando el cliente de Gradio y retorna la URL de la imagen.

        Parameters:
            prompt (str): El prompt para la generación de la imagen.
            width (int, optional): El ancho de la imagen. Defaults to 1024.
            height (int, optional): La altura de la imagen. Defaults to 1024.
            guidance_scale (float, optional): El guidance scale para la generación. Defaults to 3.5.
            num_inference_steps (int, optional): El número de pasos de inferencia. Defaults to 28.
            randomize_seed (bool, optional): Si se debe aleatorizar la semilla. Defaults to True.
            seed (float, optional): La semilla utilizada para la generación. Defaults to 0.

        Returns:
            List[ImageGenerationResult]: Una lista con la URL del archivo generado y la semilla utilizada.
        """
        try: 
            login(token="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", add_to_git_credential=True)
        except Exception as e:
            raise Exception("No se pudo iniciar sesión en Hugging Face Hub. Por favor, verifica tu token.", e)
        
        try:
            # Crear el cliente de Gradio
            client = Client("black-forest-labs/FLUX.1-dev")
            # Realizar la predicción para generar la imagen
            result = client.predict(
                prompt=prompt,
                seed=seed,
                randomize_seed=randomize_seed, 
                width=width,
                height=height,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                api_name="/infer"
            )

            images_folder = "static/tools/generate_image"
            temp_file_path = result[0]
            file_name = f"{prompt}.webp"
            # Definir la ruta completa del archivo en la carpeta 'static/images'
            destination_path = os.path.join(images_folder, file_name)
            # Mover la imagen desde la carpeta temporal a 'static/images'
            shutil.move(temp_file_path, destination_path)
            # Devolver la URL de la imagen generada
            imagen = f"<img src='static/tools/generate_image/{file_name}' width='590' height='345'>", 
            respuesta = f'IMAGEN de {prompt} -> {imagen}, ES IMPORTANTISIMO QUE RESPONDAS SOLO CON LA ETIQUETA DE IMAGEN EN TU RESPUESTA RESPETANDO EL FORMATO,  sin texto adicional despues de la etiqueta. NO ALTERES LA URL'
            return str(respuesta)
        except Exception as e:
            print(e)

