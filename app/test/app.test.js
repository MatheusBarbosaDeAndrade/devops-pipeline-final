'use strict';

process.env.LOG_SILENT = 'true';

const request = require('supertest');
const { createApp } = require('../src/app');

describe('API de Tarefas', () => {
  let app;

  beforeEach(() => {
    app = createApp();
  });

  test('GET /health responde status ok', async () => {
    const res = await request(app).get('/health');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('ok');
  });

  test('GET / serve a página inicial', async () => {
    const res = await request(app).get('/');
    expect(res.status).toBe(200);
    expect(res.text).toContain('Tarefas');
  });

  test('GET /api/info retorna versão e contadores', async () => {
    await request(app).get('/health');
    const res = await request(app).get('/api/info');
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('versao');
    expect(res.body.requisicoes).toBeGreaterThanOrEqual(1);
  });

  test('lista inicia vazia', async () => {
    const res = await request(app).get('/api/tarefas');
    expect(res.status).toBe(200);
    expect(res.body).toEqual([]);
  });

  test('cria, consulta, atualiza e remove uma tarefa', async () => {
    const criada = await request(app).post('/api/tarefas').send({ titulo: 'Configurar pipeline' });
    expect(criada.status).toBe(201);
    expect(criada.body).toMatchObject({ id: 1, titulo: 'Configurar pipeline', concluida: false });

    const consulta = await request(app).get('/api/tarefas/1');
    expect(consulta.status).toBe(200);

    const atualizada = await request(app).patch('/api/tarefas/1').send({ concluida: true, titulo: 'Pipeline ok' });
    expect(atualizada.body).toMatchObject({ concluida: true, titulo: 'Pipeline ok' });

    const removida = await request(app).delete('/api/tarefas/1');
    expect(removida.status).toBe(204);

    const lista = await request(app).get('/api/tarefas');
    expect(lista.body).toHaveLength(0);
  });

  test('rejeita tarefa sem título (400)', async () => {
    const res = await request(app).post('/api/tarefas').send({ titulo: '   ' });
    expect(res.status).toBe(400);
  });

  test('retorna 404 para tarefa inexistente', async () => {
    expect((await request(app).get('/api/tarefas/99')).status).toBe(404);
    expect((await request(app).patch('/api/tarefas/99').send({ concluida: true })).status).toBe(404);
    expect((await request(app).delete('/api/tarefas/99')).status).toBe(404);
  });

  test('retorna 404 para rota desconhecida', async () => {
    const res = await request(app).get('/nao-existe');
    expect(res.status).toBe(404);
  });

  test('GET /api/erro gera erro 500 tratado', async () => {
    const res = await request(app).get('/api/erro');
    expect(res.status).toBe(500);
    expect(res.body.erro).toBe('Erro interno do servidor');
  });

  test('GET /api/lento respeita o atraso solicitado', async () => {
    const res = await request(app).get('/api/lento?ms=50');
    expect(res.status).toBe(200);
    expect(res.body.atraso_ms).toBe(50);
  });
});
