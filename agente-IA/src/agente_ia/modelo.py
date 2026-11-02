import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ_PROYECTO / ".env")


def crear_modelo() -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta GEMINI_API_KEY. Configúrala en el archivo agente-IA/.env."
        )

    nombre_modelo = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    return ChatGoogleGenerativeAI(
        model=nombre_modelo,
        vertexai=False,
        max_retries=2,
    )
