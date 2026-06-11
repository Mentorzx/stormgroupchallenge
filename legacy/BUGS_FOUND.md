# Bugs encontrados em `legacy/breach_matcher.py`

## 1. `domain_matches` comparava a query com sensibilidade a maiúsculas

- **Função afetada:** `domain_matches`
- **Comportamento esperado:** comparação parcial e case-insensitive tanto no domínio quanto na query.
- **Comportamento encontrado:** o domínio era normalizado com `.lower()`, mas a query não era. `query="Dropbox"` não casava com `Domain="dropbox.com"`.
- **Como reproduzir:** chamar `domain_matches({"Domain": "dropbox.com"}, "Dropbox")`; antes da correção retornava `False`.
- **Teste criado:** `tests/legacy/test_breach_matcher.py::test_domain_matches_is_case_insensitive_for_domain_and_query`
- **Severidade:** alta.
- **Impacto em produção:** um filtro por domínio poderia omitir breaches relevantes por diferença de capitalização, criando falso negativo em uma consulta cybersec.
- **Correção aplicada:** normalização de `query` com `.lower()` e garantia de que breaches sem domínio não casam.

## 2. `within_breach_date` excluía indevidamente o limite superior

- **Função afetada:** `within_breach_date`
- **Comportamento esperado:** janela inclusiva `[date_from, date_to]`.
- **Comportamento encontrado:** a condição `bd >= date_to` excluía o próprio `date_to`; um breach em `2019-12-31` não entrava na janela até `2019-12-31`.
- **Como reproduzir:** chamar `within_breach_date({"BreachDate": "2019-12-31"}, "2019-01-01", "2019-12-31")`; antes retornava `False`.
- **Teste criado:** `tests/legacy/test_breach_matcher.py::test_within_breach_date_includes_date_to`
- **Severidade:** alta.
- **Impacto em produção:** breaches exatamente no fim do intervalo sumiriam do índice, com risco de relatório incompleto.
- **Correção aplicada:** troca da comparação para `bd > date_to`.

## 3. `paginate` perdia o último item da página

- **Função afetada:** `paginate`
- **Comportamento esperado:** retornar até `page_size` itens, com slicing `[start:end]`.
- **Comportamento encontrado:** calculava `end = start + page_size - 1`, e como o limite superior do slicing Python é exclusivo, cada página perdia um item.
- **Como reproduzir:** chamar `paginate(list(range(20)), 1, 20)`; antes retornava 19 itens.
- **Teste criado:** `tests/legacy/test_breach_matcher.py::test_paginate_returns_exactly_page_size_and_does_not_drop_items`
- **Severidade:** média/alta.
- **Impacto em produção:** paginação poderia ocultar registros, gerando lacunas ao varrer todo o catálogo.
- **Correção aplicada:** cálculo correto `end = start + page_size`.
