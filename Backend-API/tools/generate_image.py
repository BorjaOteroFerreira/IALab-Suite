import os
import shutil
from typing import List
from pydantic import BaseModel, Field
from langchain.tools import tool
from gradio_client import Client
from huggingface_hub import login

from .base_tool import BaseTool, ToolMetadata, ToolCategory


class ImageGenerationResult(BaseModel):
    file_path: str


class ImageGenerationToolInput(BaseModel):
    prompt: str = Field(..., description="El prompt para generar la imagen.")
    width: int = Field(1024, description="El ancho de la imagen.")
    height: int = Field(1024, description="La altura de la imagen.")
    guidance_scale: float = Field(3.5, description="El guidance scale.")
    num_inference_steps: int = Field(28, description="El número de pasos de inferencia.")
    randomize_seed: bool = Field(True, description="Si se debe aleatorizar la semilla.")
    seed: float = Field(0, description="La semilla utilizada.")


class ImageGenerationTool(BaseTool):
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="generate_image",
            description="Genera imágenes basadas en prompts de texto usando IA",
            category=ToolCategory.IMAGE,
            requires_api_key=True,
            api_key_env_var="HUGGINGFACE_TOKEN"
        )
    
    @classmethod
    def get_tool_name(cls) -> str:
        return "generate_image"
    
    def execute(self, query: str, **kwargs):
        """Ejecuta generación de imagen"""
        width = kwargs.get('width', 1024)
        height = kwargs.get('height', 1024)
        guidance_scale = kwargs.get('guidance_scale', 3.5)
        num_inference_steps = kwargs.get('num_inference_steps', 28)
        randomize_seed = kwargs.get('randomize_seed', True)
        seed = kwargs.get('seed', 0)
        
        return self.run(query, width, height, guidance_scale, num_inference_steps, randomize_seed, seed)
    @staticmethod
    @tool("Generate Image with Flux")
    def run(
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        guidance_scale: float = 3.5,
        num_inference_steps: int = 28,
        randomize_seed: bool = True,
        seed: float = 0
    ) -> str:
        """
        Genera una imagen basándose en un prompt usando el cliente de Gradio y retorna la URL de la imagen.
        """
        try:
            hf_token = os.getenv("HUGGINGFACE_TOKEN", "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")  # Asegúrate de tener un token válido
            login(token=hf_token, add_to_git_credential=True)
        except Exception as e:
            raise Exception("❌ No se pudo iniciar sesión en Hugging Face Hub. Verifica tu token.", e)

        try:
            # Cliente para el espacio
            client = Client("black-forest-labs/FLUX.1-dev")

            # Predicción usando el endpoint correcto y parámetros completos
            result = client.predict(
                prompt,
                seed,
                randomize_seed,
                width,
                height,
                guidance_scale,
                num_inference_steps,
                api_name="/infer"
            )

            # El resultado es una tupla: [0] dict con 'path', [1] float seed
            image_info = result[0]
            temp_file_path = image_info.get("path")

            if not temp_file_path or not os.path.isfile(temp_file_path):
                raise ValueError("La ruta del archivo generado no es válida.")

            # Ruta destino
            images_folder = "static/tools/generate_image"
            os.makedirs(images_folder, exist_ok=True)

            # Guardar con nombre limpio
            file_name = f"{prompt}.webp".replace(" ", "_")
            destination_path = os.path.join(images_folder, file_name)
            shutil.move(temp_file_path, destination_path)

            # Solo retornar la etiqueta <img> como pide el formato
            imagen = f"<img src='static/tools/generate_image/{file_name}' width='590' height='345'>"
            return imagen

        except Exception as e:
            return f"❌ Error al generar la imagen: {str(e)}"
