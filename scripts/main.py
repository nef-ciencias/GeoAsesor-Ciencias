import os
import json
from pathlib import Path
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

BASE_DIR = Path(__file__).resolve().parent
PROMPT_PATH = BASE_DIR.parent / "prompts" / "system_prompt.txt"

def cargar_prompt_maestro(ruta_archivo):
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None

def consultar_asesor(pregunta_alumno):
    token = os.getenv("GITHUB_TOKEN")
    endpoint = "https://models.inference.ai.azure.com"
    
    if not token:
        return "⚠️ Error: Token no configurado."

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(token),
    )

    instrucciones = cargar_prompt_maestro(PROMPT_PATH)
    if instrucciones is None:
        return "⚠️ Error: No se halló el system_prompt.txt."

    response = client.complete(
        messages=[
            SystemMessage(content=instrucciones),
            UserMessage(content=pregunta_alumno),
        ],
        model="google/gemini-1.5-flash",
        temperature=0.7,
        max_tokens=1000
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    event_path = os.getenv("GITHUB_EVENT_PATH")
    
    if event_path:
        with open(event_path, "r") as f:
            event_data = json.load(f)
            
            # Extraemos el texto: busca en 'comment' primero, si no hay, busca en 'discussion'
            duda = event_data.get("comment", {}).get("body") or event_data.get("discussion", {}).get("body", "")
            user = event_data.get("comment", {}).get("user", {}).get("login") or event_data.get("discussion", {}).get("user", {}).get("login", "Alumno")
            
            if duda:
                # Omitimos imprimir "Respondiendo a..." para que no ensucie la respuesta final en GitHub
                respuesta = consultar_asesor(duda)
                print(respuesta)
            else:
                print("No se encontró texto ni en el comentario ni en la discusión.")
    else:
        print("Ejecutando en modo local...")
        print(consultar_asesor("¿Qué es una parábola?")) 
