# Deploy msgbus-ws to Kubernetes (Helm)

Deploy once, keep running: the store lives on a PVC so `messages.jsonl` + `files/`
survive pod restarts — no re-setup. Single replica by design (in-memory WS
registry + single-writer store).

## 0. Prerequisites
- Image pushed to `registry.gitlab.com/hngan.it/message-bus`.
- An nginx Ingress controller + a DNS record for your domain → the ingress LB.
- (Optional) cert-manager ClusterIssuer for automatic TLS.

## 1. Build & push the image
```bash
# from the repo root (where the Dockerfile is)
docker build -t registry.gitlab.com/hngan.it/message-bus:1.0.0 .
docker login registry.gitlab.com          # user + a GitLab token with write_registry
docker push registry.gitlab.com/hngan.it/message-bus:1.0.0
```

## 2. Namespace + copy the GitLab pull secret from ns-waas
```bash
kubectl create namespace ns-msgbus
# copy the existing pull secret so the cluster can PULL the private image
kubectl -n ns-waas get secret gitlab-registry-secret -o yaml \
  | sed 's/namespace: ns-waas/namespace: ns-msgbus/' \
  | kubectl -n ns-msgbus apply -f -
```

## 3. Install with Helm
```bash
helm upgrade --install msgbus-ws deploy/helm/msgbus-ws \
  --namespace ns-msgbus --create-namespace \
  --set image.tag=1.0.0 \
  --set token="$(openssl rand -hex 24)" \
  --set ingress.host=msgbus.hngan.it \
  --set ingress.tls.clusterIssuer=letsencrypt-prod
```
Print the token you generated (clients need it):
```bash
kubectl -n ns-msgbus get secret msgbus-ws-secret -o jsonpath='{.data.MSGBUS_TOKEN}' | base64 -d; echo
```

## 4. Verify
```bash
kubectl -n ns-msgbus rollout status deploy/msgbus-ws
curl -s https://msgbus.hngan.it/health          # {"ok":true,...}
```

## 5. Connect a client (over the domain, TLS)
```bash
export MSGBUS_HOST=msgbus.hngan.it MSGBUS_TLS=1 MSGBUS_TOKEN=<the-token>
export MSGBUS_FROM="Minh Khôi"
python scripts/msgbus_client.py listen           # wss:// realtime
python scripts/msgbus_client.py send "chào" --to "Bảo Ngọc"
```

## Key values (see values.yaml)
| Value | Meaning |
| :-- | :-- |
| `image.repository` / `image.tag` | image (default `registry.gitlab.com/hngan.it/message-bus`) |
| `imagePullSecrets[0].name` | `gitlab-registry-secret` (copied in step 2) |
| `token` / `existingSecret` | shared auth token: chart-created vs pre-existing Secret |
| `persistence.size` / `storageClass` | store PVC |
| `ingress.host` / `ingress.className` | your domain + ingress class |
| `ingress.tls.clusterIssuer` | cert-manager issuer for auto TLS (optional) |

## Notes
- Horizontal scaling (replicas > 1) is NOT supported as-is (broadcast/routing/seq
  are in-memory + single-writer). HA would need a shared pub/sub + RWX volume.
- E2EE is client-side only; the server/relay never sees plaintext (see ../SKILL.md §7).
