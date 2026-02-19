import os
import json
from datetime import datetime
from pathlib import Path
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

BASE_DIR = Path(__file__).resolve().parent
PROMPT_PATH = BASE_DIR.parent / "prompts" / "system_prompt.txt"
# Definimos la ruta de nuestra base de datos
DB_PATH = BASE_DIR.parent / "db_alumnos.json"
LIMITE_DIARIO = 3  # Límite de preguntas por alumno al día

def cargar_prompt_maestro(ruta_archivo):
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None

def verificar_limite(usuario):
    """Revisa si el alumno tiene consultas disponibles hoy y actualiza la BD"""
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Cargar la base de datos si existe
    if DB_PATH.exists():
        with open(DB_PATH, "r", encoding="utf-8") as f:
            try:
                db = json.load(f)
            except json.JSONDecodeError:
                db = {}
    else:
        db = {}

    # 2. Inicializar al usuario si es nuevo o si cambió de día
    if usuario not in db or db[usuario].get("fecha") != hoy:
        db[usuario] = {"fecha": hoy, "consultas": 0}

    # 3. Verificar si ya llegó al límite
    if db[usuario]["consultas"] >= LIMITE_DIARIO:
        return False

    # 4. Incrementar la consulta y guardar la base de datos
    db[usuario]["consultas"] += 1
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4)
    
    return True

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
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1000
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    event_path = os.getenv("GITHUB_EVENT_PATH")
    
    if event_path:
        with open(event_path, "r") as f:
            event_data = json.load(f)
            
            duda = event_data.get("comment", {}).get("body") or event_data.get("discussion", {}).get("body", "")
            user = event_data.get("comment", {}).get("user", {}).get("login") or event_data.get("discussion", {}).get("user", {}).get("login", "Alumno")
            
            if duda:
                # AQUÍ APLICAMOS EL CONTROL DE LÍMITES
                tiene_permiso = verificar_limite(user)
                
                if not tiene_permiso:
                    print(f"Hola @{user}. Has alcanzado tu límite de {LIMITE_DIARIO} consultas diarias para el GeoAsesor. Recuerda repasar la bibliografía oficial (como el libro de Ramírez Galarza o Bracho) o acércate a las ayudantías con Fabián Elizalde. ¡Vuelve mañana para más dudas!")
                else:
                    respuesta = consultar_asesor(duda)
                    print(respuesta)
            else:
                print("No se encontró texto en el comentario.")
    else:
        print("Ejecutando en modo local...")
        print(consultar_asesor("¿Qué es una parábola?"))
