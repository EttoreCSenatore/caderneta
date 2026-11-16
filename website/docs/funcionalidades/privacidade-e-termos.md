---
title: Privacidade e termos
---

# Política de privacidade e termos de uso

A Caderneta tem uma **política de privacidade** e **termos de uso** em linguagem simples, públicos (dá para ler antes de entrar) e com **confirmação registrada por versão**.

## Como funciona

- **Onde ler:** `/privacidade` e `/termos`, sem login, e nos links do rodapé do app e da tela de entrada.
- **Primeiro acesso:** antes de usar o app, a pessoa lê e marca **"Li e estou ciente"**. Isso é a **ciência** do texto, não um consentimento para o tratamento de dados: a base legal é o contrato da escola (veja a política).
- **Texto novo:** quando a versão muda, todo mundo vê a tela de confirmação de novo no próximo acesso. A confirmação guarda **quem**, **qual texto**, **qual versão** e **quando**, e fica na auditoria.
- **Sem internet** (modo offline do professor), a confirmação fica para o próximo acesso online.
- **Encarregado (DPO):** a direção informa o nome e o e-mail em **Escola**. O contato aparece na política (para quem está logado) e em **Meus dados**.
- **Cookies:** só há o cookie de sessão, essencial. Por isso **não há aviso de cookies**, e a política explica isso, junto com o armazenamento cifrado do modo offline.

## Para quem mantém os textos

Os textos ficam em `api/app/legal/privacidade.md` e `termos.md`, com `versao`, `titulo` e `status` no topo.

- Mudou algo relevante? **Troque a `versao`.** O teste `test_legal.py` confere que a política cita os prazos e recursos que o sistema de fato tem (365 e 180 dias, Meus dados, 15 dias, 5 anos, cookie, offline, encarregado), para o texto não ficar para trás.
- `status: rascunho` mostra a faixa **"Versão em revisão jurídica"**. Depois do parecer, troque para `vigente` e atualize a versão.
- Trechos entre colchetes e em maiúsculas (`[... A CONFIRMAR NO PARECER JURÍDICO]`) são pontos que dependem do advogado ou da implantação.

## O que ainda depende do parecer

Veja `.lgpd/gaps.md` (T30 e T31): base legal dos dados de saúde, ciência dos responsáveis para contas de alunos menores, lista de provedores e transferência internacional, prazos de auditoria e backups, foro e responsabilidade nos termos.

:::note Não é aconselhamento jurídico
Este é um **rascunho técnico** escrito com base no mapa de dados e nas leis. Ele só deve ser publicado para as escolas **depois da revisão de um(a) advogado(a)** especializado(a) em proteção de dados.
:::
