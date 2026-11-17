---
title: "ADR 0004: file storage"
sidebar_label: "ADR 0004: files"
---

# ADR 0004: files encrypted on disk, behind an interface

- **Status:** accepted (2026-11-16); review in M9 (pilot)
- **Context:** M5 needs to store exams and assignments, which are **confidential until they are taken**. The architecture foresaw S3-compatible
  storage (MinIO). Starting and operating an extra service just for this, before a production server exists, adds
  attack surface and complexity with no gain for development.

## Decision

1. Files live in a **local directory** (`CADERNETA_STORAGE_DIR`, one folder per school), **encrypted at rest with AES-GCM**
   (the same key as the sensitive data; the file id is used as associated data, so a file moved elsewhere does not open).
2. All access goes through `app/arquivos.py` (`grava`, `le`, `apaga`: write, read, delete). Switching to S3-compatible storage only requires rewriting those three functions.
3. The browser never receives the path: it downloads through a **signed link** (HMAC, 5 minutes, bound to the user and the school), and the API **checks
   access again** on every download, which is recorded in the audit log.
4. Validation looks at the **content**: PDF or DOCX signature, 15 MB, PDF without JavaScript, attachments or execution, DOCX without macros, invalid
   paths or decompression "bombs". Message attachments: PDF, JPG and PNG up to 10 MB.
5. **Antivirus (ClamAV, `clamd`)** on every upload, **failing closed**: if it is on and down, the file is rejected.
   It is **mandatory in production** (the API does not start without `CADERNETA_ANTIVIRUS=clamav`).
6. **Images lose their metadata** (EXIF, XMP, comments, dates), which can reveal location and device, something sensitive because they are
   photos of children and families.
7. **DOCX becomes PDF** with headless LibreOffice (`CADERNETA_CONVERSOR=libreoffice`), an isolated conversion per upload (temporary folder,
   fresh profile, minimal environment, CPU and size limits, maximum time), and the result is revalidated as a PDF. Only the PDF is stored, which
   also removes the risk of the original DOCX.
8. **Retention:** requests are deleted 365 days after the exam date, stalled drafts after 90 days and message attachments after 365 days
   (the message text stays). Orphan files on disk are swept. All done by the worker, with a `retencao.eliminar` audit entry.

## Consequences

- In development and in a one-school pilot, one server is enough. For more than one application server (M9), migrate to S3-compatible
  storage, keeping client-side encryption.
- **Backup:** the directory must go into the backup together with the database, and the **data key** kept separately: without it the files
  do not open. Losing the key means losing the files.
- LibreOffice becomes a server dependency, and processing untrusted documents is an attack surface. That is why it runs isolated
  per upload and with limits. In production, running the converter in a container with no network is the next hardening step (M8).
- ClamAV needs a daily update of the virus database (`freshclam`) and memory (about 1 GB).
- The retention period is global for now. Per-school periods are left for M8, together with the legal opinion.
