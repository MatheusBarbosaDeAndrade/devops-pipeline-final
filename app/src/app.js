'use strict';

const express = require('express');
const path = require('path');
const os = require('os');
const logger = require('./logger');

/**
 * Cria a aplicação Express. Os dados ficam em memória: o foco do projeto é
 * o pipeline DevOps (testes, container, Kubernetes e observabilidade).
 */
function createApp() {
  const app = express();
  app.use(express.json());

  const tarefas = new Map();
  let proximoId = 1;
  const iniciadoEm = Date.now();
  const contadores = { requisicoes: 0, erros: 0 };

  // Middleware de log de acesso: registra método, rota, status e tempo de resposta.
  app.use((req, res, next) => {
    const inicio = process.hrtime.bigint();
    res.on('finish', () => {
      const duracaoNs = Number(process.hrtime.bigint() - inicio);
      const tempoMs = Math.round(duracaoNs / 1e4) / 100; // 2 casas decimais
      const status = res.statusCode;
      contadores.requisicoes += 1;
      if (status >= 500) contadores.erros += 1;
      const nivel = status >= 500 ? 'error' : status >= 400 ? 'warn' : 'info';
      logger[nivel](`${req.method} ${req.originalUrl} ${status} ${tempoMs}ms`, {
        event: { kind: 'event', category: ['web'], dataset: 'tarefas.access', duration: duracaoNs },
        http: { request: { method: req.method }, response: { status_code: status } },
        url: { path: req.path, original: req.originalUrl },
        user_agent: { original: req.get('user-agent') || '' },
        client: { ip: req.ip },
        host: { hostname: os.hostname() },
        response_time_ms: tempoMs,
      });
    });
    next();
  });

  app.use(express.static(path.join(__dirname, '..', 'public')));

  app.get('/health', (req, res) => {
    res.json({ status: 'ok', uptime_s: Math.round((Date.now() - iniciadoEm) / 1000) });
  });

  app.get('/api/info', (req, res) => {
    res.json({
      servico: process.env.SERVICE_NAME || 'devops-tarefas-api',
      versao: process.env.APP_VERSION || require('../package.json').version,
      ambiente: process.env.APP_ENV || 'local',
      pod: os.hostname(),
      requisicoes: contadores.requisicoes,
      erros: contadores.erros,
    });
  });

  app.get('/api/tarefas', (req, res) => {
    res.json([...tarefas.values()]);
  });

  app.get('/api/tarefas/:id', (req, res) => {
    const tarefa = tarefas.get(Number(req.params.id));
    if (!tarefa) return res.status(404).json({ erro: 'Tarefa não encontrada' });
    return res.json(tarefa);
  });

  app.post('/api/tarefas', (req, res) => {
    const titulo = typeof req.body?.titulo === 'string' ? req.body.titulo.trim() : '';
    if (!titulo) return res.status(400).json({ erro: 'O campo "titulo" é obrigatório' });
    const tarefa = { id: proximoId++, titulo, concluida: false, criadaEm: new Date().toISOString() };
    tarefas.set(tarefa.id, tarefa);
    return res.status(201).json(tarefa);
  });

  app.patch('/api/tarefas/:id', (req, res) => {
    const tarefa = tarefas.get(Number(req.params.id));
    if (!tarefa) return res.status(404).json({ erro: 'Tarefa não encontrada' });
    if (typeof req.body?.concluida === 'boolean') tarefa.concluida = req.body.concluida;
    if (typeof req.body?.titulo === 'string' && req.body.titulo.trim()) tarefa.titulo = req.body.titulo.trim();
    return res.json(tarefa);
  });

  app.delete('/api/tarefas/:id', (req, res) => {
    if (!tarefas.delete(Number(req.params.id))) return res.status(404).json({ erro: 'Tarefa não encontrada' });
    return res.status(204).end();
  });

  // Rotas de demonstração para gerar latência e erros visíveis no Kibana.
  app.get('/api/lento', (req, res) => {
    const atraso = Math.min(Number(req.query.ms) || 300 + Math.floor(Math.random() * 900), 5000);
    setTimeout(() => res.json({ atraso_ms: atraso }), atraso);
  });

  app.get('/api/erro', () => {
    throw new Error('Erro simulado para demonstração de monitoramento');
  });

  app.use((req, res) => res.status(404).json({ erro: 'Rota não encontrada' }));

  // eslint-disable-next-line no-unused-vars
  app.use((err, req, res, next) => {
    logger.error(err.message, { error: { message: err.message, type: err.name, stack_trace: err.stack } });
    res.status(500).json({ erro: 'Erro interno do servidor' });
  });

  return app;
}

module.exports = { createApp };
