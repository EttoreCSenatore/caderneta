---
id: versoes
title: Versions and What's new
---

# Versions and What's new

Every Caderneta version has a number and a summary of what changed. Everything comes from a single file,
[`releases.yaml`](https://github.com/EttoreCSenatore/caderneta/blob/main/releases.yaml) at the root of the repository.

## Version number: `MAJOR.MINOR.PATCH`

| Part | Goes up when | Example |
|---|---|---|
| **PATCH** | a fix or security adjustment, with nothing new to learn | 0.9.0 → 0.9.1 |
| **MINOR** | a new feature or a visible improvement | 0.9.1 → 0.10.0 |
| **MAJOR** | a change that requires action from whoever installs it (new configuration, a manual step when updating) | 0.10.0 → 1.0.0 |

**1.0.0** is reserved for the start of the pilot with a real school. Until then, versions are `0.x`.

## The `releases.yaml` file

The newest version is always at the **top**. The texts are in Portuguese, because the app is.

```yaml
- versao: 0.9.1
  data: 2026-11-25
  titulo: Correções no diário
  itens:
    - tipo: correcao            # novo | melhoria | correcao | seguranca
      publico: [equipe]         # equipe and/or familia
      texto: >
        A média do período agora aparece certa quando há prova de recuperação.
```

- **`publico`:** `equipe` is the school management, coordination and teachers; `familia` is guardians and students. Each person only sees the items for their audience, and a version with no item for them does not show up.
- **`texto`:** plain language, from the user's point of view ("Now you can..."). No file, table or library names.
- **What stays out:** internal changes with no effect for users (tests, documentation, library updates without a security fix).

The API validates the file on startup and the tests fail a file out of format: a version not in `X.Y.Z`, out of order or repeated, an invalid date, an unknown type or audience, an empty text.

## Where the version shows up

- **What's new page** (`/novidades`): in the menu footer and in **My account**, with a filter by type.
- **New version notice:** "Version X: see what changed", at the top of the screen, until the person opens What's new or dismisses it. It is stored only on the device (browser).
- **Menu footer** and **My account:** "Caderneta X.Y.Z".
- **`/api/saude`:** `{"ok": true, "versao": "X.Y.Z"}`, public, for monitoring and the smoke test (`deploy/smoke.sh` shows the version running). The code is open, so the version is not a secret; operators should update when a security advisory is published.

## Publishing a version

1. In the PR that changes something for users, add the new version at the top of `releases.yaml`.
2. Change the same number in `api/pyproject.toml` and `web/package.json` (and run `npm install --package-lock-only` in `web/`). A test fails if the three differ.
3. After the merge into `main`, with CI green, the **Release da versão** job creates the `vX.Y.Z` tag and the GitHub release with the notes (`scripts/notas-versao.py`). If the tag already exists, it does nothing.

Several PRs can go into the same version: the second one adds items to the top version, if it has not been published yet.
