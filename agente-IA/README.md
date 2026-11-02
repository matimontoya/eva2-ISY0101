# Agente IA para ContaSimple

Prototipo académico de un asistente contable para empresas en Chile. En modo de integración consulta ContaSimple; también conserva un modo de demostración con datos ficticios. No presenta declaraciones al SII.

## Funciones actuales

- Historial de chat persistente y separado por empresa.
- Consulta mensual de ingresos y gastos desde la base de ContaSimple o desde datos ficticios de demostración.
- Guardado de borradores internos bajo solicitud.
- Memoria semántica de notas, filtrada por empresa.
- Gemini API como modelo y LangGraph para organizar el flujo de herramientas.
- Chat integrado en ContaSimple, disponible desde la esquina inferior izquierda al abrir una empresa.

## Componentes

- `src/agente_ia/agente.py`: grafo y conversación por empresa.
- `src/agente_ia/modelo.py`: configuración de Gemini.
- `src/agente_ia/tools/consultas.py`: consulta de movimientos y borradores.
- `src/agente_ia/memory/semantica.py`: almacenamiento y búsqueda semántica.
- `Dockerfile` y `compose.yaml`: ejecución del agente en la red privada de ContaSimple.
- `src/agente_ia/api.py`: servicio interno para el chat web y la carga del historial.
- `data/movimientos_demo.json`: movimientos ficticios.
- `data/agregar_movimientos_ficticios.sql`: carga movimientos ficticios en las empresas que ya existen en ContaSimple; se puede volver a ejecutar sin duplicarlos.
- `data/crear_empresas_demo_con_movimientos.sql`: crea dos empresas de simulación y movimientos de noviembre de 2025 a octubre de 2026.
- `data/reemplazar_empresas_demo.sql`: reemplaza las dos empresas de simulación anteriores con actividad mensual variable.
- `data/conversaciones.sqlite`: historial de chat persistente.
- `data/memoria_semantica.sqlite`: notas y vectores.
- `data/borradores_demo.json`: borradores internos.
- `docs/arquitectura.md`: diagrama del sistema.

## Preparación

Desde esta carpeta, crea y activa el entorno virtual con `python3 -m venv .venv` y `source .venv/bin/activate`. Luego instala las dependencias con `python -m pip install -r requirements.txt`.

Crea `.env` a partir de `.env.example` y configura `GEMINI_API_KEY`, `GEMINI_MODEL`, `DB_NAME`, `DB_USER` y `DB_PASSWORD`. No subas `.env` al repositorio. El Compose asigna `DB_HOST=db`, `DB_PORT=5432` y `DATA_SOURCE=postgres` dentro de la red privada de Docker.

## Ejecución

Para iniciar ContaSimple con el chat integrado, desde la carpeta raíz del proyecto ejecuta `sudo docker compose build` y `sudo docker compose up -d`. Inicia sesión, abre una empresa y presiona **ContaSimple IA** en la esquina inferior izquierda. Cada empresa conserva un hilo separado. Para seguir usando el chat de terminal, ejecuta `sudo docker compose -f agente-IA/compose.yaml run --rm --user "$(id -u):$(id -g)" agente`.

Para cargar datos de demostración en todas las empresas existentes, ejecuta desde la raíz del proyecto `sudo docker compose exec -T db psql -U appuser -d contasimple -v ON_ERROR_STOP=1 < agente-IA/data/agregar_movimientos_ficticios.sql`. Los movimientos quedan marcados con origen `demo` y su descripción dice `DEMO FICTICIO`.

Para crear las dos empresas de simulación con 24 movimientos cada una, usa el mismo comando con `agente-IA/data/crear_empresas_demo_con_movimientos.sql` como archivo de entrada.

Para reemplazar esas empresas por otras con entre 2 y 5 movimientos al mes, ejecuta desde la raíz `sudo docker compose exec -T db psql -U appuser -d contasimple -v ON_ERROR_STOP=1 < agente-IA/data/reemplazar_empresas_demo.sql`. La marca de simulación queda en el nombre de la empresa y en los campos internos de los movimientos; las descripciones de ventas y gastos usan texto normal.

Para ejecutar el prototipo con movimientos ficticios desde el entorno virtual, usa `DATA_SOURCE=demo PYTHONPATH=src python -m agente_ia`.

## Demostración

1. Preguntar por los ingresos y gastos de octubre de 2026 en la empresa 1.
2. Solicitar un borrador interno del resumen.
3. Guardar una nota ficticia y recuperarla con una pregunta formulada de otra manera.
4. Cambiar a la empresa 2 y observar que su memoria está separada.

La demo requiere cuota disponible en Gemini API.

## Alcance y límites

La herramienta de Postgres consulta solo totales mensuales y usa transacciones de solo lectura. El modo demo usa movimientos ficticios. Ninguno de los modos calcula impuestos oficiales, completa un F29 real ni presenta formularios al SII; los borradores son registros internos.

## Justificación técnica del equipo

[Completar con la justificación propia del equipo para LangGraph, Gemini, SQLite y la memoria por empresa.]

## Declaración de uso de IA

[Declarar las herramientas de IA utilizadas y cómo se aplicaron, según las instrucciones de la evaluación.]

## Referencias

Google AI for Developers. (s. f.). *Gemini API embeddings*. https://ai.google.dev/gemini-api/docs/embeddings

LangChain. (s. f.). *LangGraph checkpointing*. https://reference.langchain.com/python/langgraph/checkpoints

LangChain. (s. f.). *Google Generative AI embeddings integration*. https://docs.langchain.com/oss/python/integrations/embeddings/google_generative_ai
