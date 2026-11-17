---
title: Modo offline
---

# Modo offline para notas e chamada

Sala de aula nem sempre tem internet. O **professor** consegue continuar lançando **notas** e **chamada** sem conexão; o que foi lançado fica guardado no aparelho
e é enviado sozinho quando a internet volta.

## Quem pode e o que funciona

- **Só professores**, nas turmas deles. Famílias, alunos, coordenação e direção veem os dados apenas online, sem nada guardado no aparelho.
- Ao entrar com a internet funcionando, o app guarda no aparelho o diário das suas turmas. Depois disso é possível **abrir o diário, lançar notas e registrar chamada** mesmo sem conexão.
- Uma faixa avisa **"Sem conexão"** e quantas alterações aguardam envio. Quando a internet volta, o envio é automático (também há o botão **Enviar agora**).
- Se o servidor recusar algo (por exemplo, o período foi fechado enquanto você estava offline), a alteração **não é perdida em silêncio**: fica na faixa com o motivo, e você decide descartar.
- A média aparece atualizada só depois do envio, porque o cálculo é feito no servidor.
- **Abrir o app sem internet:** com o app instalado, ele abre mesmo sem conexão e mostra o início, as turmas e os diários que estavam guardados (a identidade e a lista de turmas também ficam no cofre cifrado). Telas que dependem do servidor, como avisos e mensagens, mostram "Sem conexão".
- Não duplica: se a resposta do servidor se perder depois de gravar uma chamada, o app confere antes de reenviar.

## O que fica no aparelho (privacidade)

| Fica | **Não** fica |
|---|---|
| Nomes dos alunos das suas turmas, notas, médias, faltas e chamadas; seu nome e e-mail, os perfis, as turmas e o nome da escola | Ficha de saúde, anotações, mensagens, anexos, CPF, contatos, autorizações |
| O que você lançou e ainda não foi enviado | Dados de turmas que não são suas |

- **Cifrado:** tudo é cifrado (AES-GCM) no navegador, com uma chave que o próprio navegador guarda sem permitir exportá-la.
- **Apagado** quando você: sai da conta, troca de perfil, outra pessoa entra no mesmo aparelho, abre a tela de entrada sem nada pendente de envio,
  ou fica **7 dias sem conexão com o servidor**. Dois dias antes, uma faixa avisa se houver algo ainda não enviado.
- Há o botão **Apagar dados offline deste aparelho** na faixa.
- O cache do navegador (service worker) **nunca** guarda respostas da API; os dados offline ficam só no cofre cifrado.

:::note Limite
A cifra protege contra quem copia os arquivos do navegador, não contra quem usa o app com o celular desbloqueado. Use bloqueio de tela, e **saia da conta em aparelhos compartilhados**.
:::

## Instalar o app

- **Android e computador (Chrome, Edge):** aparece um convite **Instalar** no topo do app. Depois de instalado, abre como app, com atalhos para Avisos, Calendário e Notificações.
- **iPhone (Safari):** toque em Compartilhar e depois em **Adicionar à Tela de Início**. O app mostra essa dica.
- Atualizações são aplicadas sozinhas; o que está na fila de envio não se perde.
- O convite pode ser dispensado com **Agora não**.

## Teste automático

`npm run e2e:offline` (em `web/`) abre um Chromium de verdade, entra como a professora da demonstração, **corta a internet** e confere que o app abre e mostra o diário guardado.
Precisa da API com o seed e do build servido (`npx vite preview`).

## O que ainda falta

- Testar em **aparelhos reais** (Android e iPhone) com a PWA instalada, incluindo o push: faz parte do [plano do piloto](../piloto.md).
- **Capacitor e lojas:** fora do piloto (decisão do responsável); reavaliar depois, se a escola pedir.
