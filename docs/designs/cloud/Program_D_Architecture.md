# Program D Architecture – Cloud Interface & Gateway

## 1. Vision & Responsibilities
Cổng Gateway định tuyến traffic hiệu năng cao và dashboard React Web UI.

## 2. Scope & Out of Scope
- **Scope**: Reverse proxy, WAF protection, rate limit, admin UI portal.
- **Out of Scope**: Business task logic translation.

## 3. Topologies & Services
- **Service Topology**: GatewayProxy, RateLimiter, AdminConsole.
- **Deployment Topology**: Deploy behind Cloudflare CDN and AWS NLB.

## 4. Interface & APIs
- `ANY /api/v1/gateway/*`
