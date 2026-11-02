import os
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage, SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .modelo import crear_modelo
from .tools.consultas import crear_herramientas
from .memory.semantica import crear_herramientas_memoria


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_MEMORIA = RAIZ_PROYECTO / "data" / "conversaciones.sqlite"


def _indice_ultima_respuesta_completa(mensajes) -> int:
    for indice in range(len(mensajes) - 1, -1, -1):
        mensaje = mensajes[indice]
        if isinstance(mensaje, AIMessage) and not mensaje.tool_calls and mensaje.text.strip():
            return indice
    return -1


def _descartar_turno_incompleto(agente, configuracion: dict) -> None:
    estado = agente.get_state(configuracion)
    mensajes = (estado.values or {}).get("messages", [])
    ultimo_completo = _indice_ultima_respuesta_completa(mensajes)
    incompletos = mensajes[ultimo_completo + 1:]
    eliminaciones = [RemoveMessage(id=mensaje.id) for mensaje in incompletos if mensaje.id]
    if eliminaciones:
        agente.update_state(configuracion, {"messages": eliminaciones})


def crear_grafo(checkpointer: SqliteSaver, empresa_id: int):
    herramientas = crear_herramientas(empresa_id)
    herramientas.extend(crear_herramientas_memoria(empresa_id))
    modelo = crear_modelo().bind_tools(herramientas)

    def responder(state: MessagesState):
        instrucciones = SystemMessage(
            content=(
                f"Eres un asistente contable educativo para la empresa activa ID {empresa_id} en Chile. "
                "Responde en español. Si preguntan por ingresos o gastos de un "
                "mes, usa consultar_resumen_mensual; no inventes cifras ni hagas "
                "sumas mentalmente. Si no indican el periodo, pregúntalo. "
                "Responde únicamente a la solicitud más reciente de la persona. "
                "Usa mensajes anteriores solo si la solicitud actual se refiere claramente a ellos; "
                "no retomes preguntas anteriores, no agregues respuestas a otros temas "
                "y no enumeres consultas previas. Mantén todas las consultas limitadas "
                "a la empresa activa indicada aquí. "
                "Las herramientas incluyen el origen de cada resultado; indícalo. "
                "Si aparecen movimientos ficticios, aclara que son datos de demostración "
                "y separa sus montos de los demás movimientos. "
                "Si preguntan por una nota que la persona pidió recordar, usa buscar_memorias_empresa antes de responder. Usa guardar_memoria_empresa solo cuando pidan explícitamente recordar o guardar una nota; nunca guardes claves, RUT reales ni datos confidenciales. No calcules impuestos ni presentes montos como determinaciones "
                "oficiales del SII: la herramienta todavía no contiene las reglas "
                "ni todos los datos necesarios para eso."
            )
        )
        respuesta = modelo.invoke([instrucciones, *state["messages"]])
        respuesta = respuesta.model_copy(
            update={
                "additional_kwargs": {
                    **respuesta.additional_kwargs,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            }
        )
        return {"messages": [respuesta]}

    flujo = StateGraph(MessagesState)
    flujo.add_node("responder", responder)
    flujo.add_node("herramientas", ToolNode(herramientas))
    flujo.add_edge(START, "responder")
    flujo.add_conditional_edges(
        "responder",
        tools_condition,
        {"tools": "herramientas", END: END},
    )
    flujo.add_edge("herramientas", "responder")

    return flujo.compile(checkpointer=checkpointer)


def conversar(empresa_id: int, pregunta: str) -> str:
    if empresa_id <= 0:
        raise ValueError("El identificador de empresa debe ser positivo.")
    if not pregunta.strip():
        raise ValueError("Escribe una pregunta.")

    RUTA_MEMORIA.parent.mkdir(parents=True, exist_ok=True)
    thread_id = f"empresa:{empresa_id}:chat"
    configuracion = {"configurable": {"thread_id": thread_id}}

    with SqliteSaver.from_conn_string(str(RUTA_MEMORIA)) as checkpointer:
        agente = crear_grafo(checkpointer, empresa_id)
        _descartar_turno_incompleto(agente, configuracion)
        resultado = agente.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=pregunta,
                        additional_kwargs={"timestamp": datetime.now(timezone.utc).isoformat()},
                    )
                ]
            },
            config=configuracion,
        )

    return resultado["messages"][-1].text


def historial(empresa_id: int) -> list[dict[str, str | None]]:
    if empresa_id <= 0:
        raise ValueError("El identificador de empresa debe ser positivo.")

    RUTA_MEMORIA.parent.mkdir(parents=True, exist_ok=True)
    configuracion = {"configurable": {"thread_id": f"empresa:{empresa_id}:chat"}}
    with SqliteSaver.from_conn_string(str(RUTA_MEMORIA)) as checkpointer:
        agente = crear_grafo(checkpointer, empresa_id)
        estado = agente.get_state(configuracion)

    mensajes = (estado.values or {}).get("messages", [])
    ultimo_completo = _indice_ultima_respuesta_completa(mensajes)
    mensajes = mensajes[:ultimo_completo + 1]
    return [
        {
            "rol": "usuario" if isinstance(mensaje, HumanMessage) else "agente",
            "texto": mensaje.text,
            "timestamp": mensaje.additional_kwargs.get("timestamp"),
        }
        for mensaje in mensajes
        if isinstance(mensaje, (HumanMessage, AIMessage)) and mensaje.text.strip()
    ]
