"""Gera dashboard-tarefas.ndjson: data view, busca salva, visualizações e o
dashboard "Tarefas API - Logs e Métricas" (dashboard como código).

Uso: python3 gerar_dashboard.py  (depois: ./importar-dashboard.sh)
"""
import json
from pathlib import Path

DV = 'filebeat-tarefas'                      # id do data view
ACESSO = 'event.dataset : "tarefas.access"'  # apenas logs de acesso HTTP
REF_IDX = 'kibanaSavedObjectMeta.searchSourceJSON.index'
objs = []


def search_source(query=ACESSO, index=True):
    s = {'query': {'query': query, 'language': 'kuery'}, 'filter': []}
    if index:
        s['indexRefName'] = REF_IDX
    return {'searchSourceJSON': json.dumps(s)}


def vis(vid, title, vtype, params, aggs, query=ACESSO, index=True):
    objs.append({
        'type': 'visualization', 'id': vid,
        'attributes': {
            'title': title, 'description': '', 'version': 1, 'uiStateJSON': '{}',
            'visState': json.dumps({'title': title, 'type': vtype, 'params': params, 'aggs': aggs}),
            'kibanaSavedObjectMeta': search_source(query, index),
        },
        'references': [{'name': REF_IDX, 'type': 'index-pattern', 'id': DV}] if index else [],
    })


def agg(i, t, schema, **params):
    return {'id': str(i), 'enabled': True, 'type': t, 'schema': schema, 'params': params}


def xy(chart, metrics_axis_title, series, stacked=False):
    return {
        'type': chart, 'addTooltip': True, 'addTimeMarker': False, 'times': [],
        'legendPosition': 'bottom', 'legendSize': 'auto', 'truncateLegend': True, 'maxLegendLines': 1,
        'grid': {'categoryLines': False, 'valueAxis': 'ValueAxis-1'},
        'categoryAxes': [{'id': 'CategoryAxis-1', 'type': 'category', 'position': 'bottom', 'show': True,
                          'style': {}, 'scale': {'type': 'linear'}, 'labels': {'show': True, 'filter': True, 'truncate': 100},
                          'title': {}}],
        'valueAxes': [{'id': 'ValueAxis-1', 'name': 'LeftAxis-1', 'type': 'value', 'position': 'left', 'show': True,
                       'style': {}, 'scale': {'type': 'linear', 'mode': 'normal'},
                       'labels': {'show': True, 'rotate': 0, 'filter': False, 'truncate': 100},
                       'title': {'text': metrics_axis_title}}],
        'seriesParams': [{'show': True, 'type': chart, 'mode': 'stacked' if stacked else 'normal',
                          'data': {'label': lbl, 'id': sid}, 'valueAxis': 'ValueAxis-1',
                          'drawLinesBetweenPoints': True, 'lineWidth': 2, 'showCircles': True,
                          'interpolate': 'linear'} for sid, lbl in series],
        'labels': {}, 'thresholdLine': {'show': False, 'value': 10, 'width': 1, 'style': 'full', 'color': '#E7664C'},
        'palette': {'type': 'palette', 'name': 'default'}, 'fittingFunction': 'linear',
        'detailedTooltip': True, 'radiusRatio': 9, 'isVislibVis': True,
    }


def metric_params():
    return {'addTooltip': True, 'addLegend': False, 'type': 'metric',
            'metric': {'percentageMode': False, 'useRanges': False, 'colorSchema': 'Green to Red',
                       'metricColorMode': 'None', 'colorsRange': [{'from': 0, 'to': 10000}],
                       'labels': {'show': True}, 'invertColors': False,
                       'style': {'bgFill': '#000', 'bgColor': False, 'labelColor': False, 'subText': '', 'fontSize': 36}}}


HIST = dict(field='@timestamp', interval='auto', min_doc_count=1, extended_bounds={},
            useNormalizedEsInterval=True, scaleMetricValues=False, drop_partials=False)

# ---------------------------------------------------------------- data view
objs.append({'type': 'index-pattern', 'id': DV,
             'attributes': {'title': 'filebeat-*', 'timeFieldName': '@timestamp',
                            'name': 'Logs da API de Tarefas (filebeat-*)'}, 'references': []})

# ------------------------------------------------- 1. logs em tempo real
objs.append({
    'type': 'search', 'id': 'tarefas-logs-tempo-real',
    'attributes': {
        'title': 'Logs da aplicação em tempo real', 'description': '',
        'columns': ['log.level', 'http.request.method', 'url.path', 'http.response.status_code',
                    'response_time_ms', 'message'],
        'sort': [['@timestamp', 'desc']], 'grid': {}, 'hideChart': False,
        'kibanaSavedObjectMeta': search_source('origem : "tarefas-api"'),
    },
    'references': [{'name': REF_IDX, 'type': 'index-pattern', 'id': DV}],
})

# ------------------------------------------------------------ métricas
vis('tarefas-md', 'Sobre o dashboard', 'markdown',
    {'fontSize': 11, 'openLinksInNewTab': False,
     'markdown': '### API de Tarefas – Logs e Métricas\n'
                 'Fluxo: **app** (log JSON) → **Filebeat** → **Elasticsearch** → **Kibana**. '
                 'Atualização automática a cada 5 s.'}, [], index=False)

vis('tarefas-total', 'Total de requisições', 'metric', metric_params(),
    [agg(1, 'count', 'metric', customLabel='Requisições')])

vis('tarefas-tempo-medio', 'Tempo médio de resposta (ms)', 'metric', metric_params(),
    [agg(1, 'avg', 'metric', field='response_time_ms', customLabel='Tempo médio (ms)')])

vis('tarefas-erros', 'Erros 5xx', 'metric', metric_params(),
    [agg(1, 'count', 'metric', customLabel='Respostas 5xx')],
    query=ACESSO + ' and http.response.status_code >= 500')

vis('tarefas-status-pizza', 'Requisições por status code', 'pie',
    {'type': 'pie', 'addTooltip': True, 'legendDisplay': 'show', 'legendPosition': 'right',
     'legendSize': 'auto', 'isDonut': True, 'distinctColors': True, 'nestedLegend': False,
     'truncateLegend': True, 'maxLegendLines': 1, 'palette': {'type': 'palette', 'name': 'default'},
     'labels': {'show': True, 'position': 'default', 'values': True, 'valuesFormat': 'percent',
                'percentDecimals': 1, 'last_level': True, 'truncate': 100}},
    [agg(1, 'count', 'metric'),
     agg(2, 'terms', 'segment', field='http.response.status_code', size=10, order='desc',
         orderBy='1', otherBucket=False, missingBucket=False, customLabel='Status code')])

vis('tarefas-status-tempo', 'Requisições ao longo do tempo por status code', 'histogram',
    xy('histogram', 'Requisições', [('1', 'Requisições')], stacked=True),
    [agg(1, 'count', 'metric', customLabel='Requisições'),
     agg(2, 'date_histogram', 'segment', **HIST, customLabel='Tempo'),
     agg(3, 'terms', 'group', field='http.response.status_code', size=10, order='desc',
         orderBy='1', otherBucket=False, missingBucket=False, customLabel='Status')])

vis('tarefas-latencia', 'Tempo de resposta (ms): médio e máximo', 'line',
    xy('line', 'Milissegundos', [('1', 'Média (ms)'), ('3', 'Máximo (ms)')]),
    [agg(1, 'avg', 'metric', field='response_time_ms', customLabel='Média (ms)'),
     agg(3, 'max', 'metric', field='response_time_ms', customLabel='Máximo (ms)'),
     agg(2, 'date_histogram', 'segment', **HIST, customLabel='Tempo')])

vis('tarefas-rotas', 'Rotas mais acessadas e tempo de resposta', 'table',
    {'perPage': 10, 'showPartialRows': False, 'showMetricsAtAllLevels': False, 'showTotal': False,
     'totalFunc': 'sum', 'percentageCol': '', 'autoFitRowToContent': False},
    [agg(1, 'count', 'metric', customLabel='Requisições'),
     agg(3, 'avg', 'metric', field='response_time_ms', customLabel='Tempo médio (ms)'),
     agg(4, 'max', 'metric', field='response_time_ms', customLabel='Tempo máx. (ms)'),
     agg(2, 'terms', 'bucket', field='http.request.method', size=5, order='desc', orderBy='1',
         otherBucket=False, missingBucket=False, customLabel='Método'),
     agg(5, 'terms', 'bucket', field='url.path', size=10, order='desc', orderBy='1',
         otherBucket=False, missingBucket=False, customLabel='Rota')])

# ------------------------------------------------------------ dashboard
layout = [  # (tipo, id, x, y, w, h)
    ('visualization', 'tarefas-md', 0, 0, 12, 7),
    ('visualization', 'tarefas-total', 12, 0, 12, 7),
    ('visualization', 'tarefas-tempo-medio', 24, 0, 12, 7),
    ('visualization', 'tarefas-erros', 36, 0, 12, 7),
    ('visualization', 'tarefas-status-pizza', 0, 7, 16, 13),
    ('visualization', 'tarefas-status-tempo', 16, 7, 32, 13),
    ('visualization', 'tarefas-latencia', 0, 20, 24, 13),
    ('visualization', 'tarefas-rotas', 24, 20, 24, 13),
    ('search', 'tarefas-logs-tempo-real', 0, 33, 48, 18),
]
panels, refs = [], []
for n, (t, oid, x, y, w, h) in enumerate(layout, 1):
    panels.append({'type': t, 'panelIndex': str(n), 'embeddableConfig': {'enhancements': {}},
                   'gridData': {'x': x, 'y': y, 'w': w, 'h': h, 'i': str(n)},
                   'panelRefName': f'panel_{n}'})
    refs.append({'name': f'panel_{n}', 'type': t, 'id': oid})

objs.append({
    'type': 'dashboard', 'id': 'tarefas-dashboard',
    'attributes': {
        'title': 'Tarefas API - Logs e Métricas',
        'description': 'Logs em tempo real, status code e tempo de resposta da API de Tarefas',
        'panelsJSON': json.dumps(panels),
        'optionsJSON': json.dumps({'useMargins': True, 'syncColors': False, 'syncCursor': True,
                                   'syncTooltips': False, 'hidePanelTitles': False}),
        'timeRestore': True, 'timeFrom': 'now-15m', 'timeTo': 'now',
        'refreshInterval': {'pause': False, 'value': 5000},
        'kibanaSavedObjectMeta': {'searchSourceJSON': json.dumps(
            {'query': {'query': '', 'language': 'kuery'}, 'filter': []})},
        'version': 1,
    },
    'references': refs,
})

out = Path(__file__).with_name('dashboard-tarefas.ndjson')
out.write_text(''.join(json.dumps(o, ensure_ascii=False) + '\n' for o in objs), encoding='utf-8')
print(f'{len(objs)} objetos gravados em {out}')
