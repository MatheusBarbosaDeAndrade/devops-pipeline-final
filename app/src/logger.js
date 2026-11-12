'use strict';

/*
 * Logger estruturado em JSON (uma linha por evento - formato NDJSON).
 * Os nomes dos campos seguem o Elastic Common Schema (ECS), de modo que o
 * Filebeat e o Elasticsearch reconhecem os tipos automaticamente
 * (ex.: http.response.status_code como número).
 */
const fs = require('fs');
const path = require('path');

const SERVICE_NAME = process.env.SERVICE_NAME || 'devops-tarefas-api';
const SERVICE_VERSION = process.env.APP_VERSION || require('../package.json').version;
const ENVIRONMENT = process.env.APP_ENV || 'local';
const LOG_FILE = process.env.LOG_FILE || '';
const SILENT = process.env.LOG_SILENT === 'true';

let fileStream = null;
if (LOG_FILE) {
  fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
  fileStream = fs.createWriteStream(LOG_FILE, { flags: 'a' });
}

function write(level, message, fields = {}) {
  const entry = {
    '@timestamp': new Date().toISOString(),
    log: { level },
    message,
    service: { name: SERVICE_NAME, version: SERVICE_VERSION, environment: ENVIRONMENT },
    ...fields,
  };
  const line = JSON.stringify(entry);
  if (!SILENT) process.stdout.write(line + '\n');
  if (fileStream) fileStream.write(line + '\n');
  return entry;
}

module.exports = {
  info: (msg, fields) => write('info', msg, fields),
  warn: (msg, fields) => write('warn', msg, fields),
  error: (msg, fields) => write('error', msg, fields),
};
