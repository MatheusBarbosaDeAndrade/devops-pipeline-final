# DevOps na Prática – Pipeline CI/CD, Kubernetes e Elastic Stack

Projeto da **Atividade Avaliativa – DevOps na Prática** (disciplina DevOps Tools – UNAMA,
Prof. Rodrigo Silva Marques).

## Integrantes

| Nome | Matrícula |
|------|-----------|
| Breno Luiz da Silva Ferreira | 04135868 |
| Caique Pinto da Costa | 04135745 |
| Matheus Barbosa de Andrade | 04126063 |
| Thalison Ribeiro Mendes | 04146790 |


Curso: [NOME DO CURSO]

Uma API de tarefas em Node.js atravessa um ciclo DevOps completo:

```
 git push ──► GitHub Actions ──────────────────────────────────────────────────────────┐
              1. Testes (Jest)  ►  2. Build Docker + push GHCR  ►  3. Deploy Helm no K8s │
                                                                                        ▼
                    app (logs JSON) ──► Filebeat ──► Elasticsearch ──► Kibana (dashboard)
```

| Etapa | Entrega | Onde está |
|-------|---------|-----------|
| 1 – Conceitos | DevOps × Ágil, CI × CD (Delivery/Deployment), VMs × containers | [`docs/relatorio-etapa1.md`](docs/relatorio-etapa1.md) |
| 2 – CI | Testes, build Docker e push para o GHCR | `.github/workflows/main.yml`, `app/` |
| 3 – CD + orquestração | Chart Helm, deploy automático, NodePort 30080 | `helm/devops-app/`, job *deploy* do workflow |
| 4 – Logging e métricas | Filebeat + Elasticsearch + Kibana, dashboard (+ APM) | `monitoring/`, [`docs/aula5-entrega.md`](docs/aula5-entrega.md) |
| 5 – Relatório final | Passo a passo, desafios, reflexão crítica, roteiro da apresentação | [`docs/relatorio-final.md`](docs/relatorio-final.md) |

### Prints

| Etapa | Print |
|-------|-------|
| 2 – Testes e pipeline executado com sucesso | [`docs/prints/etapa2-testes-locais.png`](docs/prints/etapa2-testes-locais.png), [`etapa2-pipeline.png`](docs/prints/etapa2-pipeline.png) |
| 3 – Serviço rodando no Kubernetes | [`docs/prints/etapa3-kubernetes-servico.png`](docs/prints/etapa3-kubernetes-servico.png), [`etapa3-app-navegador.png`](docs/prints/etapa3-app-navegador.png), [`etapa3-helm-test.png`](docs/prints/etapa3-helm-test.png) |
| 4 – Dashboard no Kibana | [`docs/prints/etapa4-dashboard-kibana.png`](docs/prints/etapa4-dashboard-kibana.png), [`etapa4-filebeat-coleta.png`](docs/prints/etapa4-filebeat-coleta.png) |
| Extra – APM | [`docs/prints/aula5-apm-kibana.png`](docs/prints/aula5-apm-kibana.png) |

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
└── docs/                        # relatórios (Markdown) e prints
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
docker compose up -d --build          # Elasticsearch, Kibana, Filebeat, APM Server, app e gerador de tráfego
./kibana/importar-dashboard.sh        # importa o dashboard "Tarefas API - Logs e Métricas"
```
- Kibana: <http://localhost:5601/app/dashboards#/view/tarefas-dashboard>
- Elasticsearch: <http://localhost:9200>
- Aplicação: <http://localhost:3000>
- APM: <http://localhost:5601/app/apm/services>

Requer cerca de 3,5 GB de RAM livres (Elasticsearch limitado a 512 MB de heap).
Para encerrar: `docker compose down -v`.

**Como os dados são coletados:** a aplicação grava cada requisição como uma linha JSON (campos ECS:
`http.request.method`, `url.path`, `http.response.status_code`, `event.duration`, `response_time_ms`)
em `/var/log/app/app.log`. O **Filebeat** lê esse arquivo por meio de um volume compartilhado (input
`filestream`), decodifica o JSON (parser `ndjson`), acrescenta metadados do host e envia os eventos ao
**Elasticsearch** (data stream `filebeat-8.17.0`). O **Kibana** consulta esse índice e exibe o dashboard
com atualização automática a cada 5 s.

### APM (extra da Aula 5)
O agente `elastic-apm-node` é iniciado quando a variável `ELASTIC_APM_SERVER_URL` está definida.
No Docker Compose ela aponta para o serviço `apm-server` (`http://apm-server:8200`), então as
transações de cada rota (latência, throughput e erros com stack trace) aparecem em
**Kibana → Observability → APM → devops-tarefas-api**. No Kubernetes a variável não é definida
e o agente fica desligado.

## Tecnologias
Node.js 20 · Express · Jest · Docker · GitHub Actions · GitHub Container Registry · Kubernetes
(Kind / Minikube) · Helm 3 · Elasticsearch 8.17 · Kibana 8.17 · Filebeat 8.17 · APM Server 8.17
