import json
import os
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from langchain_core.tools import tool


RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
RUTA_MOVIMIENTOS = RAIZ_PROYECTO / "data" / "movimientos_demo.json"
RUTA_BORRADORES = RAIZ_PROYECTO / "data" / "borradores_demo.json"
PERIODO_VALIDO = re.compile(r"\d{4}-(0[1-9]|1[0-2])")


def _rango_periodo(periodo: str) -> tuple[date, date] | None:
    if not PERIODO_VALIDO.fullmatch(periodo):
        return None
    anio, mes = (int(parte) for parte in periodo.split("-"))
    desde = date(anio, mes, 1)
    hasta = date(anio + (mes == 12), mes % 12 + 1, 1)
    return desde, hasta


def _resumen_demo(empresa_id: int, periodo: str) -> dict:
    movimientos = json.loads(RUTA_MOVIMIENTOS.read_text(encoding="utf-8"))
    del_mes = [
        movimiento
        for movimiento in movimientos
        if movimiento["cliente_id"] == empresa_id
        and movimiento["fecha"].startswith(f"{periodo}-")
    ]

    ingresos = sum(
        (
            Decimal(movimiento["monto"])
            for movimiento in del_mes
            if movimiento["tipo"] == "ingreso"
        ),
        Decimal("0"),
    )
    gastos = sum(
        (
            Decimal(movimiento["monto"])
            for movimiento in del_mes
            if movimiento["tipo"] == "gasto"
        ),
        Decimal("0"),
    )

    return {
        "empresa_id": empresa_id,
        "periodo": periodo,
        "cantidad_movimientos": len(del_mes),
        "ingresos_clp": str(ingresos),
        "gastos_clp": str(gastos),
        "origen": "datos ficticios para la demostración",
    }


def _resumen_postgres(empresa_id: int, periodo: str) -> dict:
    # Importación local para que el modo demo no requiera psycopg instalado.
    import psycopg
    from psycopg.rows import dict_row

    rango = _rango_periodo(periodo)
    if rango is None:
        return {"error": "Usa el formato YYYY-MM, por ejemplo 2026-10."}
    desde, hasta = rango

    with psycopg.connect(
        host=os.environ.get("DB_HOST", "db"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        row_factory=dict_row,
        options="-c default_transaction_read_only=on",
    ) as conexion:
        fila = conexion.execute(
            """
            SELECT
                COUNT(*) AS cantidad_movimientos,
                COALESCE(SUM(monto) FILTER (WHERE tipo = 'ingreso'), 0) AS ingresos,
                COALESCE(SUM(monto) FILTER (WHERE tipo = 'gasto'), 0) AS gastos,
                COUNT(*) FILTER (WHERE origen = 'demo') AS cantidad_movimientos_ficticios,
                COALESCE(SUM(monto) FILTER (WHERE tipo = 'ingreso' AND origen = 'demo'), 0) AS ingresos_ficticios,
                COALESCE(SUM(monto) FILTER (WHERE tipo = 'gasto' AND origen = 'demo'), 0) AS gastos_ficticios
            FROM movimientos
            WHERE cliente_id = %s
              AND fecha >= %s
              AND fecha < %s
            """,
            (empresa_id, desde, hasta),
        ).fetchone()

    return {
        "empresa_id": empresa_id,
        "periodo": periodo,
        "cantidad_movimientos": fila["cantidad_movimientos"],
        "ingresos_clp": str(fila["ingresos"]),
        "gastos_clp": str(fila["gastos"]),
        "cantidad_movimientos_ficticios": fila["cantidad_movimientos_ficticios"],
        "ingresos_ficticios_clp": str(fila["ingresos_ficticios"]),
        "gastos_ficticios_clp": str(fila["gastos_ficticios"]),
        "origen": "base de datos de ContaSimple; incluye movimientos ficticios de demostración, identificados por separado",
    }


def obtener_resumen(empresa_id: int, periodo: str) -> dict:
    if not PERIODO_VALIDO.fullmatch(periodo):
        return {"error": "Usa el formato YYYY-MM, por ejemplo 2026-10."}

    origen_datos = os.getenv("DATA_SOURCE", "demo").strip().lower()
    if origen_datos == "demo":
        return _resumen_demo(empresa_id, periodo)
    if origen_datos == "postgres":
        return _resumen_postgres(empresa_id, periodo)
    return {"error": "DATA_SOURCE debe ser 'demo' o 'postgres'."}


def crear_herramientas(empresa_id: int):
    @tool
    def consultar_resumen_mensual(periodo: str) -> str:
        """Consulta ingresos y gastos de la empresa activa para un mes YYYY-MM."""
        resumen = obtener_resumen(empresa_id, periodo)
        return json.dumps(resumen, ensure_ascii=False)

    @tool
    def guardar_borrador_resumen_mensual(periodo: str) -> str:
        """Guarda un borrador interno del resumen mensual.
        Úsala solo si la persona pidió explícitamente guardar un borrador.
        No crea ni presenta un formulario oficial del SII.
        """
        resumen = obtener_resumen(empresa_id, periodo)
        if "error" in resumen:
            return json.dumps(resumen, ensure_ascii=False)

        if RUTA_BORRADORES.exists():
            borradores = json.loads(RUTA_BORRADORES.read_text(encoding="utf-8"))
        else:
            borradores = []

        borrador = {
            "id": str(uuid4()),
            "creado_en": datetime.now(timezone.utc).isoformat(),
            "estado": "borrador",
            "datos": resumen,
        }
        borradores.append(borrador)
        RUTA_BORRADORES.write_text(
            json.dumps(borradores, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return json.dumps(
            {
                "mensaje": "Borrador interno guardado. No es una declaración oficial del SII.",
                "borrador": borrador,
            },
            ensure_ascii=False,
        )

    return [consultar_resumen_mensual, guardar_borrador_resumen_mensual]
