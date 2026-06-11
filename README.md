# Breach Radar

[![CI](https://github.com/Mentorzx/stormgroupchallenge/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Mentorzx/stormgroupchallenge/actions/workflows/ci.yml)

Breach Radar é uma API Python + PostgreSQL para sincronizar o catálogo público de data breaches da Have I Been Pwned (HIBP) e consultar esse cache local com filtros combináveis.

A entrega segue o desafio técnico Neuroscan: `/docs`, `POST /sync`, `GET /breaches`, `GET /breaches/{name}`, persistência em PostgreSQL, sync idempotente por `Name`, validação clara e testes sem chamada real para HIBP.

Os PDFs do enunciado ficam em `docs/challenge/`.

## Stack

- Python 3.12
- FastAPI + Pydantic v2
- SQLAlchemy 2.x + Alembic
- PostgreSQL 16
- httpx
- pytest, pytest-cov, respx
- ruff
- Docker Compose
- GitHub Actions

## Arquitetura

Monólito modular, separado por responsabilidade:

```text
app/api                         rotas, dependências HTTP e handlers de erro
app/application                 casos de uso, validações e exceções
app/domain                      filtros e regras puras
app/infrastructure/hibp         cliente e mapper do payload HIBP
app/infrastructure/persistence  modelo, sessão e repositório SQLAlchemy
app/schemas                     schemas Pydantic
legacy                          bug hunt legado
tests                           testes de API, unidade e legado
```

Rotas não fazem SQL direto nem chamada HTTP externa. Elas validam entrada, chamam serviços e devolvem schemas.

## Rodando com Docker Compose

Docker Compose é o caminho principal da entrega. Não precisa de Python, Postgres ou venv local.

```bash
cp .env.example .env
docker compose build
docker compose up -d
docker compose exec app alembic upgrade head
curl http://localhost:8000/health
```

A API fica em:

- Swagger: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Healthcheck: `http://localhost:8000/health`

Serviços:

- `app`: FastAPI/Uvicorn na porta `8000`.
- `db`: PostgreSQL 16 na porta `5432`.

O Compose fixa o projeto como `breach-radar`, evitando nomes gerados a partir da pasta local.

O Dockerfile usa build multi-stage. A etapa final copia o ambiente Python já montado, não mantém `build-essential`/headers de compilação e roda a API com usuário não-root. As dependências de teste continuam na imagem de entrega porque o fluxo oficial do desafio roda lint/testes pelo próprio Compose.

O container da API também executa `alembic upgrade head` ao iniciar. O comando manual de migration fica documentado para avaliador conseguir validar o passo isoladamente.

Para limpar banco e volumes:

```bash
docker compose down -v
```

## Comandos úteis

Via Makefile, todos os comandos principais usam Docker:

```bash
make build
make up
make migrate
make smoke
make lint
make format-check
make test
make test-cov
make compile
make e2e
make down
```

Equivalentes explícitos:

```bash
docker compose config
docker compose build
docker compose up -d db
docker compose run --rm app alembic upgrade head
docker compose up -d app
curl -f http://localhost:8000/health
curl -f http://localhost:8000/openapi.json
docker compose run --rm --no-deps app ruff check .
docker compose run --rm --no-deps app ruff format --check .
docker compose run --rm app pytest --cov=app --cov=legacy --cov-report=term-missing --cov-fail-under=90
docker compose exec -T -e E2E_BASE_URL=http://localhost:8000 app pytest tests/e2e
docker compose run --rm --no-deps app python -m compileall -q app legacy tests
docker compose down -v
```

Comandos locais existem só como conveniência:

```bash
make local-install
make local-test
make local-lint
make local-run
```

## Configuração

Variáveis principais em `.env.example`:

- `DATABASE_URL`: banco usado pela API.
- `TEST_DATABASE_URL`: banco isolado usado pelos testes Docker.
- `POSTGRES_PORT`: porta local opcional para expor o Postgres no host. Default: `5432`.
- `HIBP_BREACHES_URL`: feed público da HIBP.
- `HIBP_USER_AGENT`: obrigatório pela HIBP.
- `HIBP_TIMEOUT_SECONDS`: timeout da chamada externa.
- `PAGE_SIZE_DEFAULT` e `PAGE_SIZE_MAX`: paginação.
- `LOG_LEVEL`: nível de logs.

O Compose cria dois bancos: `breach_radar` para a aplicação e `breach_radar_test` para testes. O banco de teste é recriado pelas fixtures a cada teste.

## Endpoints

### `POST /sync`

Sincroniza com `https://haveibeenpwned.com/api/v3/breaches` usando `httpx`, timeout configurável e header obrigatório:

```text
User-Agent: BreachRadar-Neuroscan-Challenge/1.0
```

Exemplo:

```bash
curl -X POST http://localhost:8000/sync
```

Resposta:

```json
{
  "source": "remote",
  "total_received": 1004,
  "inserted": 1004,
  "updated": 0,
  "ignored": 0,
  "local_total": 1004,
  "errors": []
}
```

Os números acima são só exemplo; o total muda conforme a HIBP publica novos breaches.

Se HIBP falhar por timeout, HTTP 403/5xx ou JSON inválido, `/sync` retorna `source="cache_fallback"`, preserva dados locais e inclui a mensagem de erro. Leituras continuam usando PostgreSQL local.

### `GET /breaches`

Lista breaches paginados com filtros AND:

```bash
curl "http://localhost:8000/breaches?page=1&page_size=20"
curl "http://localhost:8000/breaches?domain=adobe&data_class=passwords&min_pwn_count=100000"
curl "http://localhost:8000/breaches?breach_date_from=2019-01-01&breach_date_to=2019-12-31"
curl "http://localhost:8000/breaches?is_verified=true&is_sensitive=false&is_spam_list=false"
```

Filtros:

- `domain`: parcial, case-insensitive, trata `%` e `_` como texto literal e não casa registros sem domínio.
- `name`: busca exata, aceita letras, dígitos, ponto e hífen.
- `breach_date_from` / `breach_date_to`: `YYYY-MM-DD`, inclusivo.
- `added_date_from` / `added_date_to`: ISO 8601, inclusivo; valores sem offset são normalizados como UTC.
- `data_class`: case-insensitive contra cada item de `DataClasses`.
- `min_pwn_count` / `max_pwn_count`: inteiros `>= 0`.
- `is_verified`, `is_sensitive`, `is_spam_list`: `true` ou `false`.

Parâmetro malformado retorna HTTP 400 com o campo problemático na mensagem.
Filtros textuais vazios, como `domain=` ou `data_class=`, também retornam 400 para evitar consulta ambígua.

### `GET /breaches/{name}`

```bash
curl http://localhost:8000/breaches/Adobe
```

- Nome inválido: HTTP 400.
- Nome inexistente: HTTP 404.

## Paginação

Foi usada paginação `page`/`page_size` porque o catálogo da HIBP é pequeno/médio, essa estratégia é simples de avaliar e não exige cursor para um desafio desse tamanho.

Defaults:

- `page=1`
- `page_size=20`
- `PAGE_SIZE_MAX=100`

Se `page_size` passar do máximo, a API limita para `PAGE_SIZE_MAX`.

## Persistência

Tabela principal: `breaches`.

`name` é chave primária e chave de idempotência. A migration cria índices para filtros frequentes: `lower(domain)`, `breach_date`, `added_date`, `pwn_count` e flags booleanas.

`data_classes` é armazenado como JSONB no PostgreSQL, junto com `data_classes_normalized`, uma lista auxiliar em minúsculas usada só para busca. O filtro `data_class` usa containment em JSONB no PostgreSQL e índice GIN. No fallback SQLite local, o mesmo filtro continua em memória para manter feedback rápido sem depender de extensão específica.

## Testes

A suíte cobre API, sync, filtros, validações, paginação e bug hunt legado.

No Docker, os testes usam PostgreSQL real via `TEST_DATABASE_URL` e mockam HIBP com `respx`:

```bash
docker compose run --rm app pytest --cov=app --cov=legacy --cov-report=term-missing --cov-fail-under=90
```

`httpx2` aparece apenas nas dependências de desenvolvimento porque o `TestClient` atual de FastAPI/Starlette usa essa compatiblidade no ambiente de testes. A dependência fica limitada à faixa `2.x`; a aplicação em si continua usando `httpx` no cliente HIBP.

Sem `TEST_DATABASE_URL`, as fixtures usam SQLite em memória para feedback local rápido. Esse fallback não é o caminho oficial de validação da entrega.

Os testes E2E ficam em `tests/e2e` e chamam uma API rodando por HTTP. Use depois de `docker compose up -d app`:

```bash
docker compose exec -T -e E2E_BASE_URL=http://localhost:8000 app pytest tests/e2e
```

## Bug hunt

Os 3 bugs plantados em `legacy/breach_matcher.py` foram corrigidos e documentados em `legacy/BUGS_FOUND.md`:

1. domínio precisava comparar domínio e query sem diferenciar maiúsculas/minúsculas;
2. `date_to` precisava ser inclusivo;
3. paginação perdia item por erro de slicing.

## CI

O workflow `.github/workflows/ci.yml` valida Compose, build, migration, smoke test, E2E HTTP, ruff, format check, pytest com cobertura e compile check dentro do ambiente Docker.

## Decisões e limites

- `/sync` retorna HTTP 200 com `source="cache_fallback"` quando o feed externo falha. A decisão deixa claro que a falha foi externa e que o cache local foi preservado.
- Campos ausentes como `DataClasses`, `Domain` e `BreachDate` são normalizados para `[]` ou `null`, preservando registros parcialmente úteis.
- Campos da HIBP fora do contrato do desafio, como flags recentes e metadados extras, ficam preservados em `raw_payload`, mas não são expostos no schema público para não aumentar a API sem requisito.
- `description` é devolvido como recebido da HIBP. A API não renderiza HTML; consumidores que exibirem esse campo em frontend devem sanitizar antes de usar `innerHTML` ou equivalente.
- Duplicatas de `Name` dentro do mesmo payload remoto são ignoradas antes do upsert para evitar conflito no banco.
- Logs são JSON e evitam despejar payload completo ou segredos.

### Opcionais avaliados

Scheduler automático e ETag/If-None-Match foram deixados fora da implementação principal por ROI. O desafio pede uma API reproduzível, filtros corretos, persistência, sync manual e bug hunt; esses dois opcionais melhoram operação em produção, mas também puxam estado extra, concorrência e mais cenários de teste.

A alternativa de menor risco foi documentar o caminho:

- **Scheduler:** criar uma tarefa periódica fora do ciclo da request, preferencialmente em um processo dedicado ou job do orquestrador. Em um deploy pequeno, APScheduler funcionaria, desde que protegido contra múltiplas instâncias executando o mesmo sync ao mesmo tempo. O job chamaria o mesmo `BreachSyncService`, com intervalo configurável por env, lock simples no banco e logs do resultado.
- **ETag/If-None-Match:** persistir o `ETag` recebido da HIBP em uma tabela de metadados de sync, enviar `If-None-Match` na próxima chamada e tratar HTTP 304 como "sem alteração". Isso exigiria guardar também o último sync bem-sucedido, testar 200/304/erro, e manter o fallback atual quando o cache remoto não puder ser revalidado.

A API da HIBP também expõe `/latestBreach`, indicado pela própria documentação como forma eficiente de saber se há breach novo antes de fazer consultas mais caras. Se o projeto virasse serviço contínuo, eu começaria por esse endpoint no scheduler e só adicionaria ETag depois, se medição de tráfego/latência justificasse.

### Referências

- [HIBP API v3](https://haveibeenpwned.com/API/v3): contrato do feed público, `User-Agent`, `/breaches` e `/latestBreach`.
- [MDN ETag](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/ETag), [If-None-Match](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-None-Match) e [304](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/304): base para a decisão de não implementar revalidação HTTP sem persistência de metadados.
- [FastAPI dependencies with yield](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/): fechamento e rollback de sessão em dependências.
- [Docker Compose interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/): uso de `POSTGRES_PORT` com default no Compose.
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) e [PEP 257](https://peps.python.org/pep-0257/): estilo das docstrings adicionadas.
