-- Agrega movimientos de demostración a todas las empresas existentes.
-- Se puede ejecutar más de una vez: no duplica filas con origen 'demo' y el mismo folio.
-- Los textos dejan claro en ContaSimple que estos registros son ficticios.
WITH ejemplos(periodo, tipo, sufijo, fecha, descripcion, monto_base, contraparte) AS (
    VALUES
        ('2026-09', 'ingreso', 'V01', DATE '2026-09-05', 'DEMO FICTICIO: venta de servicios de diseño', 595000::numeric, 'Cliente Demo Septiembre'),
        ('2026-09', 'ingreso', 'V02', DATE '2026-09-18', 'DEMO FICTICIO: proyecto de diseño gráfico', 357000::numeric, 'Estudio Demo Septiembre'),
        ('2026-09', 'gasto',   'C01', DATE '2026-09-08', 'DEMO FICTICIO: compra de materiales', 119000::numeric, 'Proveedor Demo Septiembre'),
        ('2026-09', 'gasto',   'C02', DATE '2026-09-22', 'DEMO FICTICIO: suscripción de software', 178500::numeric, 'Software Demo Septiembre'),
        ('2026-10', 'ingreso', 'V01', DATE '2026-10-04', 'DEMO FICTICIO: venta de servicios de diseño', 714000::numeric, 'Cliente Demo Octubre'),
        ('2026-10', 'ingreso', 'V02', DATE '2026-10-16', 'DEMO FICTICIO: proyecto de diseño gráfico', 476000::numeric, 'Estudio Demo Octubre'),
        ('2026-10', 'gasto',   'C01', DATE '2026-10-10', 'DEMO FICTICIO: compra de materiales', 142800::numeric, 'Proveedor Demo Octubre'),
        ('2026-10', 'gasto',   'C02', DATE '2026-10-24', 'DEMO FICTICIO: suscripción de software', 238000::numeric, 'Software Demo Octubre')
), empresas AS (
    SELECT id FROM clientes
), candidatos AS (
    SELECT
        c.id AS cliente_id,
        e.periodo,
        e.tipo,
        e.sufijo,
        e.fecha,
        e.descripcion,
        e.monto_base + (c.id * 1000)::numeric AS monto,
        e.contraparte
    FROM empresas c
    CROSS JOIN ejemplos e
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
    'DEMO-' || REPLACE(c.periodo, '-', '') || '-' || c.sufijo,
    c.contraparte,
    'ficticio',
    'demo'
FROM candidatos c
WHERE NOT EXISTS (
    SELECT 1
    FROM movimientos existente
    WHERE existente.cliente_id = c.cliente_id
      AND existente.origen = 'demo'
      AND existente.folio = 'DEMO-' || REPLACE(c.periodo, '-', '') || '-' || c.sufijo
);
