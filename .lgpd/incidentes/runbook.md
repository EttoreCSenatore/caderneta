# Plano de resposta a incidentes de segurança (rascunho)

> **Rascunho técnico, não é parecer jurídico.** Prazos e itens vêm da skill `lgpd-incident-response` ([goul4rt/lgpd-skills](https://github.com/goul4rt/lgpd-skills), MIT), que descreve a **Res. CD/ANPD nº 15/2024** e o **art. 48 da LGPD**. O repositório `ctresb/leis` não traz as resoluções da ANPD: **conferir no texto oficial** e validar com o jurídico. ⏸ Checkpoint: revisão do encarregado e do advogado.

## Quem faz o quê

| Papel | Quem | Faz |
|---|---|---|
| **Controladora** | A escola | Decide comunicar à ANPD e aos titulares; assina as comunicações |
| **Encarregado (DPO)** | Informado em *Escola* no app | Coordena a resposta, conversa com a ANPD e com os titulares |
| **Operadora** | `CADERNETA_OPERADORA_NOME` (quem hospeda esta instalação) | Detecta, contém, preserva evidências, investiga, informa a escola **sem demora** |
| **Jurídico** | Advogado(a) de proteção de dados | Decide se o incidente é notificável (art. 5º) |

Antes do piloto, a escola e a operadora preenchem **nomes e telefones de plantão** (item aberto T33).

## O que conta como incidente

Qualquer evento que comprometa a **confidencialidade, integridade ou disponibilidade** de dados pessoais, confirmado ou suspeito. Exemplos nesta plataforma: acesso a dados de outra escola; conta de equipe invadida; banco, backup ou diretório de arquivos copiado; anexo ou prova exposta; chave de dados vazada; link secreto (iCal, assinado) divulgado; aparelho de professor perdido com o modo offline; e-mail enviado à pessoa errada; erro que mostra o aluno de um responsável para outro.

## Prazos (padrão; escola de pequeno porte pode ter o dobro, a confirmar)

| Obrigação | Prazo |
|---|---|
| Comunicar à ANPD (se notificável) | **3 dias úteis** da ciência de que afetou dados pessoais |
| Comunicar aos titulares (se notificável) | **3 dias úteis** (mesmo marco) |
| Complementar a comunicação preliminar | até **20 dias úteis** |
| Registro interno de **todos** os incidentes | **mínimo 5 anos** |

**Marco zero (T+0):** o instante em que a escola ou a operadora soube que dados pessoais foram afetados. Anote data, hora e fuso.

## Passo a passo

### 1. T+0: abrir
- Registrar T+0. Avisar o encarregado, a segurança/engenharia e o jurídico. Abrir uma entrada em `log.md`.
- **Não apagar nada.** Evidência primeiro.

### 2. T+0 a T+4h: conter e preservar
Antes de reiniciar ou limpar qualquer coisa, **guardar cópia** dos logs (aplicação, proxy, banco) e da tabela `auditoria`. Depois conter:

- **Encerrar todas as sessões** da instalação ou de uma escola:
  ```bash
  python -m app.cli revogar-sessoes            # todas as escolas
  python -m app.cli revogar-sessoes <escola_id> # só uma escola
  ```
- **Uma pessoa:** ela mesma usa *Minha conta → Sair em todos os aparelhos* (também cancela o push), ou a direção redefine a senha.
- **Notificações do aparelho:** apagar as inscrições (`push_inscricao`) ou remover as chaves VAPID da configuração.
- **Conta de equipe invadida:** redefinir a senha, refazer o 2FA e revisar a `auditoria` (`login`, `saude_lida`, `titular.exportou`, `notas_corrigidas`).
- **Link secreto exposto:** revogar o link do calendário na tela de calendário; links assinados expiram em 5 minutos.
- **Chave de dados (`CADERNETA_DATA_KEY`) vazada:** a rotação de chave ainda não existe (T14, M8.5). Tratar como incidente grave e acionar o jurídico.
- **Falha no código:** corrigir, publicar e adicionar teste de regressão.
- Se o incidente foi em **provedor** (hospedagem, e-mail), exigir relatório técnico por escrito.

### 3. T+4h a T+24h: dimensionar (decisão humana)
- Que dados? Estavam cifrados com a chave intacta (saúde, arquivos)? Isso muda o risco.
- Quantos titulares? **Separar crianças, adolescentes** e adultos.
- Aplicar o **teste do art. 5º**: precisa de **(A)** potencial de afetar significativamente interesses e direitos **E (B)** pelo menos uma categoria: dado sensível; **dado de criança ou adolescente**; financeiro; autenticação (senha, token); sigilo legal; larga escala.
- **Atenção:** quase todo dado desta plataforma é de criança ou adolescente. Basta o requisito A para o incidente ser notificável. Na dúvida, o encarregado e o jurídico decidem; **não decidir sozinho**.

### 4. Até 3 dias úteis: comunicar (⏸ checkpoint do jurídico)
- **ANPD:** usar [modelo-comunicacao-anpd.md](./modelo-comunicacao-anpd.md) (12 itens), pelo peticionamento eletrônico da ANPD.
- **Titulares** (ou responsáveis, no caso de menores): usar [modelo-comunicacao-titulares.md](./modelo-comunicacao-titulares.md) (7 itens), em linguagem simples, direto a cada pessoa; se inviável, divulgação pública.
- Não escrever conteúdo da exposição na comunicação.

### 5. Depois
- Investigar a causa raiz, complementar a comunicação (até 20 dias úteis), corrigir e registrar em `log.md` (**mesmo se não notificável**, com o motivo).
- Atualizar o RIPD e este plano com o que foi aprendido.

## Exercício de simulação (pelo menos 1 por ano)

Cronometrar o fluxo entre operadora, encarregado e escola em 4 cenários: (1) acesso a dados de outra escola por falha de autorização; (2) conta da direção invadida com leitura de fichas de saúde; (3) cópia do diretório de arquivos e do banco; (4) professor perde o celular com o modo offline ativo. Registrar o tempo e as falhas aqui. **Ainda não feito (T33).**
