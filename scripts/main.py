import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

def cargar_prompt_maestro(ruta_archivo):
    """Lee las instrucciones del cerebro del bot desde el archivo .txt"""
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        return f.read()

def consultar_asesor(pregunta_alumno):
    # 1. Configuración de acceso (Asegúrate de tener tu token en una variable de entorno)
    # Para pruebas locales puedes ponerlo directo, pero en GitHub usaremos Secrets.
    token = os.getenv("GITHUB_TOKEN") 
    endpoint = "https://models.inference.ai.azure.com"
    
    if not token:
        return "⚠️ Error: No se encontró el GITHUB_TOKEN. Configúralo en tus variables de entorno."

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(token),
    )

    # 2. Cargar el cerebro del bot
    instrucciones = cargar_prompt_maestro("../prompts/system_prompt.txt")

    # 3. Realizar la consulta al modelo Gemini 1.5 Flash
    response = client.complete(
        messages=[
            SystemMessage(content=instrucciones),
            UserMessage(content=pregunta_alumno),
        ],
        model="gemini-1.5-flash",
        temperature=0.7, # Balance entre creatividad y precisión
        max_tokens=1000
    )

    return response.choices[0].message.content

# --- PRUEBA TÉCNICA ---
if __name__ == "__main__":
    duda = "¿Cómo se define una elipse según lo que vimos con el Prof. Nebbia?"
    print(f"Buscando respuesta para: {duda}...\n")
    print(consultar_asesor(duda))
