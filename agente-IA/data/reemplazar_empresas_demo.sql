-- Reemplaza únicamente las dos empresas de simulación creadas por el script anterior.
-- Aborta si alguna contiene movimientos que no tengan origen demo.
BEGIN;

DO $$
DECLARE
    ids_anteriores BIGINT[];
BEGIN
    SELECT ARRAY_AGG(id) INTO ids_anteriores
    FROM clientes
    WHERE nombre IN (
        'Empresa Demo Diseño (Simulación)',
        'Empresa Demo Servicios (Simulación)'
    );

    IF ids_anteriores IS NOT NULL THEN
        IF EXISTS (
            SELECT 1 FROM movimientos
            WHERE cliente_id = ANY(ids_anteriores)
              AND origen <> 'demo'
        ) THEN
            RAISE EXCEPTION 'No se eliminaron las empresas: tienen movimientos que no son de demostración.';
        END IF;

        DELETE FROM movimientos WHERE cliente_id = ANY(ids_anteriores);
        DELETE FROM clientes WHERE id = ANY(ids_anteriores);
    END IF;
END $$;

INSERT INTO clientes (nombre)
SELECT datos.nombre
FROM (VALUES
    ('Diseño Norte (Empresa de demostración)'),
    ('Servicios Creativos (Empresa de demostración)')
) AS datos(nombre)
WHERE NOT EXISTS (
    SELECT 1 FROM clientes existente WHERE existente.nombre = datos.nombre
);

WITH empresas AS (
    SELECT id, nombre,
           CASE nombre
               WHEN 'Diseño Norte (Empresa de demostración)' THEN 1
               ELSE 2
           END AS variante
    FROM clientes
    WHERE nombre IN (
        'Diseño Norte (Empresa de demostración)',
        'Servicios Creativos (Empresa de demostración)'
    )
), meses AS (
    SELECT
        serie.n AS indice_mes,
        (DATE '2025-11-01' + (serie.n || ' months')::interval)::date AS inicio_mes
    FROM generate_series(0, 11) AS serie(n)
), conteos AS (
    SELECT
        empresa.id AS cliente_id,
        empresa.variante,
        meses.indice_mes,
        meses.inicio_mes,
        CASE (meses.indice_mes + empresa.variante) % 4
            WHEN 0 THEN 1
            WHEN 1 THEN 2
            WHEN 2 THEN 3
            ELSE 1
        END AS cantidad_ventas,
        CASE (meses.indice_mes + empresa.variante) % 3
            WHEN 0 THEN 1
            ELSE 2
        END AS cantidad_gastos
    FROM empresas empresa
    CROSS JOIN meses
), ventas AS (
    SELECT
        c.cliente_id,
        'ingreso'::text AS tipo,
        CASE c.variante
            WHEN 1 THEN 'Diseño de identidad visual y piezas gráficas'
            ELSE 'Servicios de producción y contenido digital'
        END AS descripcion,
        (280000 + c.indice_mes * 13500 + c.variante * 55000 + n.venta * 32000)::numeric AS monto,
        c.inicio_mes + (2 + n.venta * 6) AS fecha,
        'SIM-' || TO_CHAR(c.inicio_mes, 'YYYYMM') || '-V' || c.variante || '-' || n.venta AS folio,
        CASE c.variante
            WHEN 1 THEN 'Cliente de diseño'
            ELSE 'Cliente de servicios creativos'
        END AS contraparte
    FROM conteos c
    CROSS JOIN LATERAL generate_series(1, c.cantidad_ventas) AS n(venta)
), gastos AS (
    SELECT
        c.cliente_id,
        'gasto'::text AS tipo,
        CASE c.variante
            WHEN 1 THEN 'Materiales y licencias de diseño'
            ELSE 'Servicios de alojamiento y producción'
        END AS descripcion,
        (55000 + c.indice_mes * 4200 + c.variante * 18000 + n.gasto * 12500)::numeric AS monto,
        c.inicio_mes + (10 + n.gasto * 8) AS fecha,
        'SIM-' || TO_CHAR(c.inicio_mes, 'YYYYMM') || '-C' || c.variante || '-' || n.gasto AS folio,
        CASE c.variante
            WHEN 1 THEN 'Proveedor de materiales'
            ELSE 'Proveedor de servicios digitales'
        END AS contraparte
    FROM conteos c
    CROSS JOIN LATERAL generate_series(1, c.cantidad_gastos) AS n(gasto)
), candidatos AS (
    SELECT * FROM ventas
    UNION ALL
    SELECT * FROM gastos
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
    'Documento de prueba',
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

COMMIT;
