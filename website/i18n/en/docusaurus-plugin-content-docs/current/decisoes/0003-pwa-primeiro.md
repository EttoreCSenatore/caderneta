---
title: "ADR 0003: PWA first"
sidebar_label: "ADR 0003: PWA first"
---

# ADR 0003: PWA first, app stores later

- **Status:** accepted (2026-11-15)
- **Context:** the request is for a web app and a mobile app. Maintaining two codebases (web and native) doubles the work.

## Decision

1. **M1–M6:** the web app is a PWA: installable on the home screen (Android and iOS 16.4+), with push and offline cache.
2. **M7:** package the same PWA with **Capacitor** to publish on the Play Store and the App Store, using native push
   where the PWA is limited (iOS).

## Consequences

- One codebase for web and mobile from the start.
- Parents with an older iPhone may not receive push through the PWA until M7; e-mail covers that case.
- Developer accounts for the stores (Google and Apple) are only needed in M7.

## Update (2026-11-17)

**Capacitor and the app stores were left out of the pilot**: the installed PWA is enough, and the stores bring the cost of a paid account, review, and they reopen the privacy analysis. PWA push, the teacher's offline mode and phone installation were delivered in M7. Re-evaluate after the pilot, if a school asks.
