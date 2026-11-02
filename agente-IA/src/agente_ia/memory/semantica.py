import json
import math
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings


RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
RUTA_BASE = RAIZ_PROYECTO / "data" / "memoria_semantica.sqlite"
load_dotenv(RAIZ_PROYECTO / ".env")


@contextmanager
def conexion_memoria():
    RUTA_BASE.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(RUTA_BASE)
    try:
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS memorias_empresa (
                id TEXT PRIMARY KEY,
                empresa_id INTEGER NOT NULL,
                contenido TEXT NOT NULL,
                vector_json TEXT NOT NULL,
                creado_en TEXT NOT NULL
            )
            """
        )
        conexion.execute(
            """
            CREATE INDEX IF NOT EXISTS memorias_empresa_idx
            ON memorias_empresa (empresa_id)
            """
        )
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def crear_embedding(texto: str, tipo: str) -> list[float]:
    modelo = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        task_type=tipo,
        output_dimensionality=768,
    )
    return modelo.embed_query(texto)


def similitud_coseno(vector_a: list[float], vector_b: list[float]) -> float:
    producto = sum(a * b for a, b in zip(vector_a, vector_b))
    norma_a = math.sqrt(sum(a * a for a in vector_a))
    norma_b = math.sqrt(sum(b * b for b in vector_b))
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return producto / (norma_a * norma_b)


def crear_herramientas_memoria(empresa_id: int):
    @tool
    def guardar_memoria_empresa(contenido: str) -> str:
        """Guarda una nota ficticia para la empresa activa.
        Úsala solo cuando la persona pida explícitamente recordar o guardar algo.
        No guardes claves, RUT reales ni información confidencial.
        """
        contenido = contenido.strip()
        if not contenido:
            return "No se guardó la memoria: el texto está vacío."
        if len(contenido) > 1500:
            return "No se guardó la memoria: limita la nota a 1500 caracteres."

        vector = crear_embedding(contenido, "RETRIEVAL_DOCUMENT")
        memoria_id = str(uuid4())
        creado_en = datetime.now(timezone.utc).isoformat()

        with conexion_memoria() as conexion:
            conexion.execute(
                """
                INSERT INTO memorias_empresa
                    (id, empresa_id, contenido, vector_json, creado_en)
                VALUES (?, ?, ?, ?, ?)
                """,
                (memoria_id, empresa_id, contenido, json.dumps(vector), creado_en),
            )

        return (
            f"Nota guardada para la empresa activa. "
            f"Identificador de memoria: {memoria_id}"
        )

    @tool
    def buscar_memorias_empresa(consulta: str) -> str:
        """Busca por significado entre las notas guardadas para la empresa activa."""
        vector_consulta = crear_embedding(consulta, "RETRIEVAL_QUERY")

        with conexion_memoria() as conexion:
            filas = conexion.execute(
                """
                SELECT contenido, vector_json, creado_en
                FROM memorias_empresa
                WHERE empresa_id = ?
                """,
                (empresa_id,),
            ).fetchall()

        if not filas:
            return "No hay notas guardadas para esta empresa."

        resultados = []
        for contenido, vector_json, creado_en in filas:
            vector_guardado = json.loads(vector_json)
            puntuacion = similitud_coseno(vector_consulta, vector_guardado)
            resultados.append(
                {
                    "contenido": contenido,
                    "similitud": round(puntuacion, 4),
                    "creado_en": creado_en,
                }
            )

        resultados.sort(key=lambda item: item["similitud"], reverse=True)
        return json.dumps(resultados[:3], ensure_ascii=False)

    return [guardar_memoria_empresa, buscar_memorias_empresa]
