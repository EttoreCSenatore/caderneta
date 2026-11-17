---
title: Offline mode
---

# Offline mode for grades and roll call

A classroom does not always have internet. The **teacher** can keep entering **grades** and **roll call** without a connection; what was entered stays on the device
and is sent automatically when the internet comes back.

## Who can and what works

- **Teachers only**, in their own classes. Families, students, coordination and principal's office see data only online, with nothing stored on the device.
- On signing in with a working internet, the app stores the gradebook of their classes on the device. After that you can **open the gradebook, enter grades and record roll call** even without a connection.
- A banner shows **"No connection"** and how many changes are waiting to be sent. When the internet returns, sending is automatic (there is also a **Send now** button).
- If the server refuses something (for example, the term was closed while you were offline), the change **is not silently lost**: it stays in the banner with the reason, and you decide whether to discard it.
- The average only shows updated after sending, because the calculation is done on the server.
- **Opening the app without internet:** with the app installed, it opens even with no connection and shows the home screen, classes and the gradebooks that were stored (the identity and the class list also live in the encrypted vault). Screens that depend on the server, such as notices and messages, show "No connection".
- No duplicates: if the server's response is lost after saving a roll call, the app checks before resending.

## What stays on the device (privacy)

| Stays | Does **not** stay |
|---|---|
| Names of students in your classes, grades, averages, absences and roll calls; your name and e-mail, roles, classes and school name | Health file, notes, messages, attachments, CPF, contacts, authorizations |
| What you entered and has not been sent yet | Data of classes that are not yours |

- **Encrypted:** everything is encrypted (AES-GCM) in the browser, with a key the browser itself keeps without allowing it to be exported.
- **Deleted** when you: sign out, switch role, someone else signs in on the same device, open the sign-in screen with nothing pending to send,
  or go **7 days without contact with the server**. Two days before, a banner warns if something is still unsent.
- There is an **Erase offline data from this device** button in the banner.
- The browser cache (service worker) **never** stores API responses; offline data lives only in the encrypted vault.

:::note Limit
The encryption protects against someone copying the browser's files, not against someone using the app on an unlocked phone. Use a screen lock, and **sign out on shared devices**.
:::

## Installing the app

- **Android and computer (Chrome, Edge):** an **Install** invitation appears at the top of the app. Once installed, it opens as an app, with shortcuts to Notices, Calendar and Notifications.
- **iPhone (Safari):** tap Share and then **Add to Home Screen**. The app shows this tip.
- Updates are applied on their own; what is in the send queue is not lost.
- The invitation can be dismissed with **Not now**.

## Automated test

`npm run e2e:offline` (in `web/`) opens a real Chromium, signs in as the demo teacher, **cuts the internet** and checks that the app opens and shows the stored gradebook.
It needs the API with the seed and the built app served (`npx vite preview`).

## What is still missing

- Testing on **real devices** (Android and iPhone) with the PWA installed, including push: part of the [pilot plan](../piloto.md).
- **Capacitor and app stores:** out of the pilot (maintainer's decision); re-evaluate later, if a school asks.
