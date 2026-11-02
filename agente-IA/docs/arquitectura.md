# Arquitectura del agente

```mermaid
flowchart LR
    U[Persona usuaria] --> W[Chat flotante en ContaSimple]
    W -->|sesión autenticada y empresa activa| A[API ContaSimple]
    A -->|pregunta e ID de empresa| G[LangGraph en el contenedor agente]
    G -->|thread_id por empresa| C[(SQLite: historial)]
    G --> M[Gemini 3.6 Flash]

    M -->|respuesta sin herramientas| G
    M -->|solicitud de herramienta| T[ToolNode de LangGraph]

    T --> Q[Consultar resumen mensual]
    Q --> D[(Modo demo: JSON ficticio)]
    Q --> P[(Postgres: tabla movimientos)]
    G -. red privada mi-plataforma_default .-> P

    T --> B[Guardar borrador interno]
    B --> F[(Borradores JSON)]

    T --> S[Guardar o buscar memoria]
    S --> E[Gemini Embeddings]
    E --> V[(SQLite: memoria semántica)]
    V -->|filtrado por empresa_id| S

    Q --> M
    B --> M
    S --> M
    M --> G
    G --> A
    A --> W
```

## Separación por empresa

Cada conversación usa un `thread_id` asociado al ID de la empresa. La API valida la sesión y comprueba que la empresa exista antes de enviar la pregunta al servicio interno del agente. Las memorias semánticas se guardan con `empresa_id`, y las búsquedas filtran por la empresa activa. En modo ContaSimple, la consulta Postgres filtra por el ID activo y fuerza `default_transaction_read_only`.

## Decisiones del equipo

[Completar con el análisis y la justificación técnica propia del equipo.]
