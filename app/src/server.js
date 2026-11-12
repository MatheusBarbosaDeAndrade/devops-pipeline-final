'use strict';

// APM opcional (extra da Aula 5): só é ativado se ELASTIC_APM_SERVER_URL estiver definido.
// Precisa ser carregado antes de qualquer outro módulo para instrumentar o Express.
if (process.env.ELASTIC_APM_SERVER_URL) {
  require('elastic-apm-node').start({
    serviceName: process.env.SERVICE_NAME || 'devops-tarefas-api',
    serverUrl: process.env.ELASTIC_APM_SERVER_URL,
    environment: process.env.APP_ENV || 'local',
  });
}

const { createApp } = require('./app');
const logger = require('./logger');

const PORT = Number(process.env.PORT) || 3000;

const server = createApp().listen(PORT, () => {
  logger.info(`Servidor iniciado na porta ${PORT}`, { event: { dataset: 'tarefas.app' } });
});

function encerrar(sinal) {
  logger.info(`Recebido ${sinal}, encerrando servidor`, { event: { dataset: 'tarefas.app' } });
  server.close(() => process.exit(0));
}
process.on('SIGTERM', () => encerrar('SIGTERM'));
process.on('SIGINT', () => encerrar('SIGINT'));
