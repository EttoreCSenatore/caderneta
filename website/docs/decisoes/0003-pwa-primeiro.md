---
title: "ADR 0003: PWA primeiro"
sidebar_label: "ADR 0003: PWA primeiro"
---

# ADR 0003: PWA primeiro, lojas depois

- **Status:** aceita (2026-11-15)
- **Contexto:** o pedido é um web app e um app de celular. Manter dois códigos (web e nativo) dobra o trabalho.

## Decisão

1. **M1–M6:** o web app é uma PWA: instalável na tela inicial (Android e iOS 16.4+), com push e cache offline.
2. **M7:** empacotar a mesma PWA com **Capacitor** para publicar na Play Store e na App Store, usando push nativo
   onde a PWA é limitada (iOS).

## Consequências

- Um só código para web e celular desde o início.
- Pais com iPhone antigo podem não receber push pela PWA até o M7; o e-mail cobre esse caso.
- Contas de desenvolvedor das lojas (Google e Apple) só são necessárias no M7.

## Atualização (2026-11-17)

O **Capacitor e as lojas ficaram fora do piloto**: a PWA instalada basta, e as lojas trazem custo de conta paga, revisão e reabrem a análise de privacidade. O push da PWA, o modo offline do professor e a instalação no celular foram entregues no M7. Reavaliar depois do piloto, se a escola pedir.
