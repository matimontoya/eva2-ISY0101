-- Crea dos empresas de demostración con movimientos sintéticos.
-- Los nombres y descripciones dejan claro que son simulaciones académicas.
-- Se puede volver a ejecutar sin duplicar empresas ni movimientos.
INSERT INTO clientes (nombre)
SELECT datos.nombre
FROM (VALUES
    ('Empresa Demo Diseño (Simulación)'),
    ('Empresa Demo Servicios (Simulación)')
) AS datos(nombre)
WHERE NOT EXISTS (
    SELECT 1 FROM clientes existente WHERE existente.nombre = datos.nombre
);

WITH empresas_demo AS (
    SELECT id, nombre,
           CASE nombre
               WHEN 'Empresa Demo Diseño (Simulación)' THEN 1
               ELSE 2
           END AS variante
    FROM clientes
    WHERE nombre IN (
        'Empresa Demo Diseño (Simulación)',
        'Empresa Demo Servicios (Simulación)'
    )
), meses AS (
    SELECT (DATE '2025-11-01' + (serie.mes || ' months')::interval)::date AS inicio_mes
    FROM generate_series(0, 11) AS serie(mes)
), base AS (
    SELECT
        empresa.id AS cliente_id,
        empresa.variante,
        meses.inicio_mes,
        (600000 + (EXTRACT(MONTH FROM meses.inicio_mes)::integer * 17000)
            + ((EXTRACT(YEAR FROM meses.inicio_mes)::integer - 2025) * 90000)
            + ((empresa.variante - 1) * 180000))::numeric AS ingreso
    FROM empresas_demo empresa
    CROSS JOIN meses
), candidatos AS (
    SELECT
        cliente_id,
        'ingreso'::text AS tipo,
        'DEMO FICTICIO: servicio mensual de diseño y asesoría'::text AS descripcion,
        ingreso AS monto,
        inicio_mes + 7 AS fecha,
        'DEMO-' || TO_CHAR(inicio_mes, 'YYYYMM') || '-V' || variante AS folio,
        'Cliente de demostración'::text AS contraparte
    FROM base
    UNION ALL
    SELECT
        cliente_id,
        'gasto'::text AS tipo,
        'DEMO FICTICIO: materiales y suscripción de software'::text AS descripcion,
        ROUND(ingreso * 0.35, 2) AS monto,
        inicio_mes + 14 AS fecha,
        'DEMO-' || TO_CHAR(inicio_mes, 'YYYYMM') || '-C' || variante AS folio,
        'Proveedor de demostración'::text AS contraparte
    FROM base
)
INSERT INTO movimientos (
    cliente_id, tipo, descripcion, monto, neto, exento, iva, fecha,
    documento_tipo, folio, contraparte, sii_estado, origen
)
SELECT
    c.cliente_id,
    c.tipo,
    c.descripcion,
    c.monto,
    ROUND(c.monto / 1.19, 2),
    0,
    c.monto - ROUND(c.monto / 1.19, 2),
    c.fecha,
    'Documento demo',
    c.folio,
    c.contraparte,
    'ficticio',
    'demo'
FROM candidatos c
WHERE NOT EXISTS (
    SELECT 1
    FROM movimientos existente
    WHERE existente.cliente_id = c.cliente_id
      AND existente.origen = 'demo'
      AND existente.folio = c.folio
);
