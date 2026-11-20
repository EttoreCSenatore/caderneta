---
id: licenca
title: License
---

# License

Caderneta is free software under the **GNU Affero General Public License, version 3 or later** (`AGPL-3.0-or-later`). The full text is in the
[`LICENSE`](https://github.com/EttoreCSenatore/caderneta/blob/main/LICENSE) file of the repository.

## What it allows

- **Use** Caderneta in any school, including installing it on your own server.
- **Study and audit** the code. This matters here: the system holds data about children and health data, and the school can see how they are handled.
- **Modify** and **distribute** the code, always under the same license.
- **Charge** for hosting, support and deployment.

## What it requires

- Anyone who **modifies** Caderneta and offers it as an **internet service** must give the people who use the service access to the **source code of the modified version**
  (section 13 of the AGPL). This is the difference between the AGPL and the ordinary GPL, which does not cover use over a network.
- Distributing copies requires keeping the copyright notice and the license, and delivering the source code.
- Derivative works stay under the AGPL. A modified version cannot be closed.

You do not need to publish anything to **just use** Caderneta without changing it, nor your school's settings and data.

## Third-party dependencies

The API (Python) and the web app use open-source components with permissive licenses (MIT, BSD, Apache-2.0, ISC) and one LGPL library (`psycopg`), all
**compatible** with the AGPL. The full list, with the license texts, is in
[`THIRD_PARTY_NOTICES.md`](https://github.com/EttoreCSenatore/caderneta/blob/main/THIRD_PARTY_NOTICES.md).

CI checks every change (`scripts/auditar-licencas.py`) and **fails** it if a runtime dependency with an unknown, proprietary or
incompatible license comes in (for example GPL-2.0 only, SSPL or "non-commercial use").

## Documentation and images

The text of the documentation site and the screenshots (made with fictitious data only) are under the
[**Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**](https://creativecommons.org/licenses/by-sa/4.0/) license.
You may copy, adapt and redistribute, including commercially, as long as you **give credit** and **keep the same license** on derivative versions. It is the equivalent,
for text and images, of the spirit of the AGPL. The notice is in [`LICENSE-DOCS.md`](https://github.com/EttoreCSenatore/caderneta/blob/main/LICENSE-DOCS.md).

## What is still open

- **Name and logo "Caderneta":** the license covers the code and the documentation, **not** the trademark. The [NOTICE](https://github.com/EttoreCSenatore/caderneta/blob/main/NOTICE) file puts this in writing: a modified version offered to others must make clear it is not the official Caderneta. Registering it with INPI (the Brazilian trademark office) is optional and will not be done for now; before the
  pilot a quick, free look at the INPI database is enough, because the installation service is commercial. If there is a conflict, the name can be changed.
- **Copyright:** the notice uses the maintainer's GitHub handle. Change it to the legal name of the person or owning organization before the pilot.

:::note Notice
This page explains the license in plain language and **is not legal advice**. If in doubt about obligations, consult a lawyer.
:::
