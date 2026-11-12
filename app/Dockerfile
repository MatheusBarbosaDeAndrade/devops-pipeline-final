# ---------- Etapa 1: dependências de produção ----------
FROM node:20.18.1-alpine3.20 AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force

# ---------- Etapa 2: imagem final enxuta ----------
FROM node:20.18.1-alpine3.20
LABEL org.opencontainers.image.title="devops-tarefas-api" \
      org.opencontainers.image.description="API de tarefas - Atividade DevOps na Prática"
ENV NODE_ENV=production \
    PORT=3000
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY package.json ./
COPY src ./src
COPY public ./public
# Diretório de logs gravável pelo usuário sem privilégios (lido pelo Filebeat)
RUN mkdir -p /var/log/app && chown -R node:node /var/log/app
USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/health || exit 1
CMD ["node", "src/server.js"]
