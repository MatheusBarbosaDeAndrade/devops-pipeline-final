#!/bin/sh
# Gera tráfego contínuo e variado (200, 201, 400, 404, 500 e respostas lentas)
URL=http://app:3000
sleep 5
i=0
while true; do
  i=$((i+1))
  curl -s -o /dev/null "$URL/"
  curl -s -o /dev/null "$URL/api/tarefas"
  curl -s -o /dev/null -X POST -H 'Content-Type: application/json' -d "{\"titulo\":\"Tarefa $i\"}" "$URL/api/tarefas"
  curl -s -o /dev/null "$URL/api/tarefas/$i"
  curl -s -o /dev/null -X PATCH -H 'Content-Type: application/json' -d '{"concluida":true}' "$URL/api/tarefas/$i"
  [ $((i % 3)) -eq 0 ] && curl -s -o /dev/null "$URL/api/lento"
  [ $((i % 4)) -eq 0 ] && curl -s -o /dev/null "$URL/api/tarefas/99999"
  [ $((i % 5)) -eq 0 ] && curl -s -o /dev/null -X POST -H 'Content-Type: application/json' -d '{}' "$URL/api/tarefas"
  [ $((i % 7)) -eq 0 ] && curl -s -o /dev/null "$URL/api/erro"
  [ $((i % 6)) -eq 0 ] && curl -s -o /dev/null -X DELETE "$URL/api/tarefas/$((i-1))"
  sleep 1
done
