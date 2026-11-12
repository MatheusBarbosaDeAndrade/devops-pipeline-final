# DevOps na Prática – Pipeline CI/CD, Kubernetes e Elastic Stack

Projeto da **Atividade Avaliativa – DevOps na Prática** (disciplina DevOps Tools – UNAMA).
Uma API de tarefas em Node.js atravessa um ciclo DevOps completo:

```
 git push ──► GitHub Actions ──────────────────────────────────────────────────────────┐
              1. Testes (Jest)  ►  2. Build Docker + push GHCR  ►  3. Deploy Helm no K8s │
                                                                                        ▼
                    app (logs JSON) ──► Filebeat ──► Elasticsearch ──► Kibana (dashboard)
```

| Etapa | Entrega | Onde está |
|-------|---------|-----------|
| 1 – Conceitos | Relatório (DevOps × Ágil, CI × CD, VMs × containers) | `docs/Relatorio-DevOps-na-Pratica.pdf` |
| 2 – CI | Testes, build Docker e push para o GHCR | `.github/workflows/main.yml`, `app/` |
| 3 – CD + orquestração | Chart Helm, deploy automático, NodePort 30080 | `helm/devops-app/`, job *deploy* do workflow |
| 4 – Logging e métricas | Filebeat + Elasticsearch + Kibana, dashboard | `monitoring/` |
| 5 – Relatório final | Passo a passo, desafios, reflexão crítica | `docs/` |

## Estrutura

```
.
├── .github/workflows/main.yml   # pipeline CI/CD (GitHub Actions)
├── app/                         # API Node.js + testes + Dockerfile
│   ├── src/ (app.js, server.js, logger.js)
│   ├── test/app.test.js
│   └── Dockerfile
├── helm/devops-app/             # chart Helm (Deployment, Service NodePort, ConfigMap, HPA, Ingress, teste)
├── k8s/kind-config.yaml         # cluster Kind usado no pipeline (NodePort 30080 exposto)
├── monitoring/                  # Elastic Stack via Docker Compose
│   ├── docker-compose.yml
│   ├── filebeat/filebeat.yml
│   ├── gerar-trafego.sh         # gerador de tráfego para o dashboard
│   └── kibana/                  # dashboard como código (.ndjson) + script de importação
└── docs/                        # relatório ABNT (DOCX/PDF) e prints
```

## API

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Interface web |
| GET | `/health` | Health check (probes do Kubernetes) |
| GET | `/api/info` | Versão, ambiente, pod e contadores |
| GET/POST | `/api/tarefas` | Lista / cria tarefas |
| GET/PATCH/DELETE | `/api/tarefas/:id` | Consulta / atualiza / remove |
| GET | `/api/lento?ms=` | Resposta lenta (demonstração de latência) |
| GET | `/api/erro` | Erro 500 simulado (demonstração de monitoramento) |

## Como executar

### Aplicação e testes
```bash
cd app
npm ci
npm test        # Jest + Supertest, cobertura mínima de 80 %
npm start       # http://localhost:3000
```

### Pipeline (Etapas 2 e 3)
A cada `push` na branch `main` o GitHub Actions:
1. executa os testes automatizados;
2. constrói a imagem Docker e a envia para `ghcr.io/<usuario>/devops-tarefas-api` (tags `sha-<commit>` e `latest`);
3. cria um cluster Kubernetes (Kind), instala/atualiza o release com `helm upgrade --install`,
   expõe a aplicação via **NodePort 30080**, faz teste de fumaça (`/health` e `/api/info`) e roda `helm test`.

Não é preciso configurar segredos: o login no GHCR usa o `GITHUB_TOKEN` automático.

**Deploy no Minikube local (opcional):** registre um runner self-hosted na máquina com o Minikube
(*Settings → Actions → Runners*) e crie a variável de repositório `DEPLOY_MINIKUBE=true`;
o job `deploy-minikube` passa a publicar cada nova versão também nesse cluster.

### Kubernetes manual (Minikube)
```bash
minikube start
docker build -t devops-tarefas-api:local app
minikube image load devops-tarefas-api:local
helm upgrade --install tarefas helm/devops-app -n devops --create-namespace \
  --set image.repository=devops-tarefas-api --set image.tag=local --set image.pullPolicy=Never
minikube service tarefas-devops-app -n devops --url
helm test tarefas -n devops --logs
```

### Elastic Stack (Etapa 4)
```bash
cd monitoring
docker compose up -d --build          # Elasticsearch, Kibana, Filebeat, app e gerador de tráfego
./kibana/importar-dashboard.sh        # importa o dashboard "Tarefas API - Logs e Métricas"
```
- Kibana: <http://localhost:5601/app/dashboards#/view/tarefas-dashboard>
- Elasticsearch: <http://localhost:9200>
- Aplicação: <http://localhost:3000>

Requer cerca de 3 GB de RAM livres (Elasticsearch limitado a 512 MB de heap).
Para encerrar: `docker compose down -v`.

**Como os dados são coletados:** a aplicação grava cada requisição como uma linha JSON (campos ECS:
`http.request.method`, `url.path`, `http.response.status_code`, `event.duration`, `response_time_ms`)
em `/var/log/app/app.log`. O **Filebeat** lê esse arquivo por meio de um volume compartilhado (input
`filestream`), decodifica o JSON (parser `ndjson`), acrescenta metadados do host e envia os eventos ao
**Elasticsearch** (data stream `filebeat-8.17.0`). O **Kibana** consulta esse índice e exibe o dashboard
com atualização automática a cada 5 s.

### APM (extra opcional)
O agente `elastic-apm-node` é iniciado automaticamente quando a variável `ELASTIC_APM_SERVER_URL`
está definida (ex.: `http://apm-server:8200`).

## Tecnologias
Node.js 20 · Express · Jest · Docker · GitHub Actions · GitHub Container Registry · Kubernetes
(Kind / Minikube) · Helm 3 · Elasticsearch 8.17 · Kibana 8.17 · Filebeat 8.17
