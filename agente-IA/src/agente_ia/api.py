import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .agente import conversar, historial


app = FastAPI(title="ContaSimple IA", docs_url=None, redoc_url=None)
logger = logging.getLogger("agente_ia.api")


class MensajeChat(BaseModel):
    empresa_id: int = Field(gt=0)
    mensaje: str = Field(min_length=1, max_length=4000)


@app.post("/chat")
def chat(datos: MensajeChat):
    try:
        respuesta = conversar(datos.empresa_id, datos.mensaje.strip())
    except Exception as error:
        detalle = str(error)
        logger.exception("Falló la respuesta del agente para empresa %s", datos.empresa_id)
        if "RESOURCE_EXHAUSTED" in detalle or "quota" in detalle.lower():
            raise HTTPException(
                status_code=429,
                detail="Gemini alcanzó el límite de solicitudes de la cuota actual. Inténtalo de nuevo cuando se renueve.",
            ) from error
        if "UNAVAILABLE" in detalle or "high demand" in detalle.lower():
            raise HTTPException(
                status_code=503,
                detail="Gemini está temporalmente con alta demanda. Espera un momento y vuelve a enviar tu consulta.",
            ) from error
        raise HTTPException(
            status_code=503,
            detail="El agente no pudo completar la consulta. Revisa su configuración e inténtalo más tarde.",
        ) from error
    return {"respuesta": respuesta}


@app.get("/historial/{empresa_id}")
def obtener_historial(empresa_id: int):
    try:
        return {"mensajes": historial(empresa_id)}
    except Exception as error:
        raise HTTPException(status_code=503, detail="No se pudo cargar el historial del chat.") from error
