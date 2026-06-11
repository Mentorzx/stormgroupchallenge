# Plano de testes — Breach Radar

## Estratégia

A validação oficial roda em Docker Compose com PostgreSQL real. O serviço `db` cria dois bancos: `breach_radar` para a API e `breach_radar_test` para testes. As fixtures recriam as tabelas a cada teste para manter isolamento.

Quando `TEST_DATABASE_URL` não existe, os testes usam SQLite em memória. Esse fallback é só para feedback local rápido; a entrega deve ser validada com Docker.

Chamadas externas para HIBP são mockadas com `respx`. Nenhum teste depende de rede externa.

## Casos positivos

- `POST /sync` persiste registros válidos.
- `POST /sync` duas vezes atualiza sem duplicar.
- `GET /health` retorna status simples.
- `/openapi.json` expõe o contrato OpenAPI.
- Testes E2E chamam `/health`, `/openapi.json` e `/breaches` por HTTP contra a API rodando no Compose.
- `GET /breaches` lista com paginação padrão.
- `GET /breaches/{name}` retorna detalhe existente.
- Filtros isolados: `domain`, `name`, datas, `data_class`, faixa de `pwn_count` e flags booleanas.
- Combinações de filtros usam semântica AND.
- Paginação cobre primeira página, última página, página vazia e `page_size` acima do limite.

## Casos negativos

- Timeout no feed externo.
- HTTP 403 e HTTP 500 vindos da HIBP.
- JSON malformado.
- Registro inválido no payload remoto é ignorado sem impedir persistência dos válidos.
- Registro duplicado por `Name` no mesmo payload remoto é ignorado antes do upsert.
- `name` inválido retorna 400.
- Datas malformadas retornam 400.
- Ranges invertidos retornam 400.
- `pwn_count` negativo ou não inteiro retorna 400.
- Booleanos fora de `true`/`false` retornam 400.
- Detalhe inexistente retorna 404.
- Configurações inválidas falham cedo: User-Agent vazio, timeout não positivo e paginação incoerente.
- Wildcards de SQL em `domain` (`%` e `_`) são tratados como texto literal.
- Filtros textuais vazios retornam 400.

## Edge cases

- Registro sem `DataClasses`.
- Registro sem `Domain`.
- Registro sem `BreachDate`.
- Limite superior de `BreachDate` inclusivo.
- Query de domínio com capitalização diferente.
- `added_date` sem offset explícito é normalizado para UTC para evitar comparação ambígua.
- Paginação sem perda de itens no módulo legado.

## O que não foi testado

- Performance com centenas de milhares de registros. O catálogo esperado fica na ordem de mil itens, e o desafio foca correção dos filtros.
- Scheduler automático, porque não foi implementado.
- ETag/If-None-Match, porque não foi implementado.
- Chamada real à HIBP em CI, por decisão explícita do desafio.

## Riscos

- Falso negativo em consulta cybersec: mitigado por testes de filtros, ranges inclusivos e bug hunt.
- Duplicidade no sync: mitigada por chave primária `name` e upsert.
- Falha externa derrubar leitura: mitigada por cache local e fallback controlado.
- Diferença entre ambiente local e CI: mitigada por Docker Compose como caminho oficial e E2E HTTP no CI.
