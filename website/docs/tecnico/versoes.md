---
id: versoes
title: Versões e Novidades
---

# Versões e Novidades

Cada versão da Caderneta tem um número e um resumo do que mudou. Tudo sai de um único arquivo, o
[`releases.yaml`](https://github.com/EttoreCSenatore/caderneta/blob/main/releases.yaml) na raiz do repositório.

## Número da versão: `MAJOR.MINOR.PATCH`

| Parte | Sobe quando | Exemplo |
|---|---|---|
| **PATCH** | correção ou ajuste de segurança, sem nada novo para aprender | 0.9.0 → 0.9.1 |
| **MINOR** | funcionalidade nova ou melhoria visível | 0.9.1 → 0.10.0 |
| **MAJOR** | mudança que exige ação de quem instala (configuração nova, passo manual na atualização) | 0.10.0 → 1.0.0 |

A **1.0.0** fica para o começo do piloto com uma escola real. Até lá, as versões são `0.x`.

## O arquivo `releases.yaml`

A versão mais nova fica sempre no **topo**.

```yaml
- versao: 0.9.1
  data: 2026-11-25
  titulo: Correções no diário
  itens:
    - tipo: correcao            # novo | melhoria | correcao | seguranca
      publico: [equipe]         # equipe e/ou familia
      texto: >
        A média do período agora aparece certa quando há prova de recuperação.
```

- **`publico`:** `equipe` é direção, coordenação e professores; `familia` é responsáveis e alunos. Cada pessoa só vê os itens do seu público, e uma versão sem nenhum item para ela não aparece.
- **`texto`:** linguagem simples, do ponto de vista de quem usa ("Agora você pode..."). Sem nomes de arquivos, de tabelas ou de bibliotecas.
- **O que não entra:** mudanças internas sem efeito para quem usa (testes, documentação, atualização de bibliotecas sem correção de segurança).

A API valida o arquivo ao iniciar e os testes reprovam um arquivo fora do formato: versão fora de `X.Y.Z`, fora de ordem ou repetida, data inválida, tipo ou público desconhecido, texto vazio.

## Onde a versão aparece

- **Página Novidades** (`/novidades`): no rodapé do menu e em **Minha conta**, com filtro por tipo.
- **Aviso de versão nova:** "Versão X: veja o que mudou", no topo da tela, até a pessoa abrir as Novidades ou dispensar. Fica guardado só no aparelho (navegador).
- **Rodapé do menu** e **Minha conta:** "Caderneta X.Y.Z".
- **`/api/saude`:** `{"ok": true, "versao": "X.Y.Z"}`, público, para o monitoramento e o teste de fumaça (`deploy/smoke.sh` mostra a versão no ar). O código é aberto, então a versão não é segredo; quem opera a instalação deve atualizar quando sair um aviso de segurança.

## Publicar uma versão

1. No PR que muda algo para quem usa, acrescente a versão nova no topo do `releases.yaml`.
2. Mude o mesmo número em `api/pyproject.toml` e em `web/package.json` (e rode `npm install --package-lock-only` em `web/`). Um teste reprova se os três divergirem.
3. Depois do merge na `main`, com a CI verde, o job **Release da versão** cria a tag `vX.Y.Z` e a release do GitHub com as notas (`scripts/notas-versao.py`). Se a tag já existe, ele não faz nada.

Vários PRs podem entrar na mesma versão: o segundo acrescenta itens à versão do topo, se ela ainda não foi publicada.
