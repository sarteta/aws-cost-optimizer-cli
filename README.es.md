# aws-cost-optimizer-cli

CLI en Python que escanea una cuenta AWS y lista las fugas de costo más
comunes -- las que cualquier equipo puede limpiar en un sprint:

- EC2 idle (CPU promedio <5% en los últimos 14 días)
- EBS desasociados (facturados, nunca montados)
- Snapshots viejos (>90 días, con el volumen padre borrado)
- Elastic IPs no asociadas ($0.005/h cada una, fácil de olvidar)
- RDS sobredimensionados (CPU <20% + conexiones <10% del máximo)
- Buckets S3 sin lifecycle policy (storage standard >180 días)
- NAT gateways en VPCs de dev

Salida: un CSV ranqueado + un resumen en Markdown que pegás en Jira o Slack.

## Por qué existe

Toda cuenta AWS que me tocó administrar tenía entre 15-25% de gasto en
recursos que nadie usaba. Las herramientas comerciales que detectan esto
(Compute Optimizer, Trusted Advisor Business, Vantage, CloudHealth) cobran
por cuenta y los hallazgos suelen ser los mismos. Este CLI cubre esos
patrones en ~800 líneas de Python que leés en una tarde.

Solo lectura. No borra, no redimensiona, no modifica nada -- genera un
reporte y la limpieza real la hace una persona en un PR de Terraform aparte.

## Quickstart

```bash
# Requiere Python 3.11+ y credenciales AWS (env / profile / rol)
pip install -r requirements.txt

# Scan seco del profile configurado (solo lectura, ~30-90s)
python -m src.scan --profile default --region us-east-1

# Scan multi-región, escribe reportes
python -m src.scan \
  --profile prod \
  --regions us-east-1,us-west-2,eu-west-1 \
  --output reports/2026-04-prod

# Mock mode -- sin cuenta AWS, útil para demos / CI
python -m src.scan --mock --output reports/mock-demo
```

## Permisos IAM

Solo lectura. La política `iam/cost-optimizer-readonly.json` es mínima:
~25 acciones entre `ec2:Describe*`, `rds:Describe*`, `s3:GetBucket*`,
`ce:GetCostAndUsage`, `cloudwatch:GetMetricStatistics`.

## Notas de diseño

Ver `docs/ARCHITECTURE.md` para:

- Cómo se estiman los precios (usa list-price por tipo de instancia;
  Savings Plans / RIs distorsionan los números -- el reporte es señal de
  ranking, no una factura).
- Por qué cada finding es su propio módulo bajo `src/findings/`. Los
  equipos pueden desactivar los que no apliquen a su cuenta.
- Qué hace el mock mode (cuenta sintética con leaks conocidos para demo
  y test sin credenciales reales).

## Licencia

MIT © 2026 Santiago Arteta
