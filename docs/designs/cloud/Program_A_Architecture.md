# Program A Architecture – Cloud Operations (Fleet & Telemetry)

## 1. Vision & Responsibilities
Quản lý vòng đời và đo lường telemetry cho toàn bộ các worker nodes phân tán chéo khu vực.

## 2. Scope & Out of Scope
- **Scope**: OTA update server, ClickHouse logs ingestion pipeline.
- **Out of Scope**: OS hypervisor provisioning.

## 3. Topologies & Services
- **Service Topology**: FleetManager, LogIngester, MetricExporter.
- **Deployment Topology**: Multi-region EKS deployment with ClickHouse cluster backup.

## 4. Interface & APIs
- `GET /api/v1/telemetry/nodes`
- `POST /api/v1/ota/push`
