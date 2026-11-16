/**
 * Gera os screenshots da documentação a partir da escola fictícia de demonstração.
 *
 * Pré-requisitos: `docker compose up -d` em infra/, `python -m app.seed` e `uvicorn` na API (porta 8000),
 * `npm run dev` aqui (porta 5173). Depois: `npm run screenshots` (ou `npm run screenshots -- m2` para um grupo).
 *
 * As contas e o segredo TOTP são os valores fictícios documentados em api/app/seed.py; só existem no ambiente local.
 */
import {createHmac} from 'node:crypto';
import {mkdirSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {dirname, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';

const BASE = process.env.BASE_URL ?? 'http://localhost:5173';
const OUT = join(dirname(fileURLToPath(import.meta.url)), '../../website/static/img/screenshots/');
const SENHA = 'caderneta-demo';
const TOTP = 'CADERNETADEMOTOTPSEGREDOXYZABCDE';
const D = '@demo.caderneta.dev';
const grupos = process.argv.slice(2);
const roda = (g) => grupos.length === 0 || grupos.includes(g);
mkdirSync(OUT, {recursive: true});

function totp(secret) {
  const alf = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  let bits = '';
  for (const c of secret.replace(/=+$/, '')) bits += alf.indexOf(c).toString(2).padStart(5, '0');
  const key = Buffer.from(bits.match(/.{8}/g).map((b) => parseInt(b, 2)));
  const buf = Buffer.alloc(8);
  buf.writeBigUInt64BE(BigInt(Math.floor(Date.now() / 30000)));
  const h = createHmac('sha1', key).update(buf).digest();
  const o = h[h.length - 1] & 15;
  return String((h.readUInt32BE(o) & 0x7fffffff) % 1e6).padStart(6, '0');
}

const erros = [];
const b = await chromium.launch();

async function sessao(email, {mobile = false, dark = false} = {}) {
  const ctx = await b.newContext(
    mobile
      ? {viewport: {width: 390, height: 844}, deviceScaleFactor: 2, isMobile: true, hasTouch: true, colorScheme: dark ? 'dark' : 'light', locale: 'pt-BR'}
      : {viewport: {width: 1280, height: 800}, colorScheme: dark ? 'dark' : 'light', locale: 'pt-BR'},
  );
  const p = await ctx.newPage();
  p.on('pageerror', (e) => erros.push(`${email}: ${e.message}`));
  p.on('console', (m) => m.type() === 'error' && !m.text().includes('401') && erros.push(`${email}: ${m.text()}`));
  await p.goto(BASE + '/entrar');
  await p.fill('input[type=email]', email + D);
  await p.fill('input[type=password]', SENHA);
  await p.click('button:has-text("Entrar")');
  await p.waitForLoadState('networkidle');
  const cod = p.locator('input[autocomplete=one-time-code]');
  if (await cod.isVisible()) {
    await cod.fill(totp(TOTP));
    await p.click('button:has-text("Confirmar")');
  }
  await p.waitForURL((u) => !u.pathname.startsWith('/entrar'));
  await p.waitForLoadState('networkidle');
  return p;
}

async function foto(p, nome, full = false) {
  await p.waitForLoadState('networkidle');
  await p.waitForTimeout(300);
  await p.screenshot({path: OUT + nome + '.png', fullPage: full});
  console.log('  ✓', nome);
}

if (roda('m1')) {
  console.log('M1');
  const ctx = await b.newContext({viewport: {width: 1280, height: 800}, locale: 'pt-BR'});
  const p = await ctx.newPage();
  await p.goto(BASE + '/entrar');
  await foto(p, 'entrar');
  await ctx.close();

  const adm = await sessao('direcao');
  await foto(adm, 'admin-inicio');
  await adm.goto(BASE + '/turmas');
  await foto(adm, 'turmas');
  await adm.click('text=7º A');
  await adm.waitForURL(/\/turmas\//);
  await adm.click('role=tab[name="Professores"]');
  await foto(adm, 'turma-professores', true);
  await adm.goto(BASE + '/alunos');
  await foto(adm, 'alunos');
  await adm.fill('input[type=search]', 'Lucas Moreira');
  await adm.waitForTimeout(600);
  await adm.click('text=Lucas Moreira Lima');
  await adm.waitForURL(/\/alunos\//);
  await adm.click('role=tab[name="Dados"]');
  await foto(adm, 'aluno-dados');
  await adm.click('role=tab[name="Família"]');
  await foto(adm, 'aluno-familia');
  await adm.click('role=tab[name="Saúde"]');
  await foto(adm, 'aluno-saude', true);
  await adm.goto(BASE + '/equipe');
  await foto(adm, 'equipe', true);
  await adm.goto(BASE + '/importar');
  const csv =
    'nome;sobrenome;data_nascimento;ra;turma;responsavel1_nome;responsavel1_tipo;responsavel1_email;responsavel1_telefone\n' +
    'Clara;Mendes;12/03/2014;N001;6º A;Rita Mendes;mae;rita.mendes@example.com;(11) 97777-1111\n' +
    'Bruno;Alves;05/09/2013;N002;7º B;Jorge Alves;pai;jorge.alves@example.com;(11) 96666-2222\n' +
    'Iara;Campos;31/02/2013;N003;7º Z;Lia Campos;tia;lia@;\n';
  const arq = join(tmpdir(), 'caderneta-import-exemplo.csv');
  writeFileSync(arq, csv);
  await adm.setInputFiles('input[type=file]', arq);
  await adm.click('button:has-text("Pré-visualizar")');
  await adm.waitForSelector('text=problema(s) encontrados');
  await foto(adm, 'importar-erros', true);

  const prof = await sessao('ana.matematica');
  await foto(prof, 'professor-inicio');
  await prof.click('a:has-text("7º A")');
  await prof.waitForURL(/\/turmas\//);
  await prof.click('role=tab[name="Alertas de saúde"]');
  await foto(prof, 'professor-alertas');

  const fam = await sessao('familia', {mobile: true});
  await foto(fam, 'familia-inicio-celular');
  await fam.click('text=Lucas Moreira Lima');
  await fam.waitForURL(/\/alunos\//);
  await fam.click('role=tab[name="Saúde"]');
  await foto(fam, 'familia-saude-celular', true);

  const al = await sessao('aluno', {mobile: true, dark: true});
  await foto(al, 'aluno-inicio-celular-escuro');
}

if (roda('m2')) {
  console.log('M2');
  const prof = await sessao('ana.matematica');
  await prof.click('a:has-text("Notas") >> nth=2'); // 7º A
  await prof.waitForURL(/\/diario\//);
  await prof.selectOption('label:has-text("Período") select', {label: '3º bimestre'});
  await prof.waitForSelector('text=Prova 2');
  await foto(prof, 'diario-notas');
  // lança uma nota e mostra a célula salva
  const cel = prof.locator('input.celula').first();
  await cel.fill((await cel.inputValue()) === '6,75' ? '7,25' : '6,75');
  await cel.press('Enter');
  await prof.waitForSelector('input.celula.salvo');
  await foto(prof, 'diario-lancamento');
  await prof.click('button:has-text("+ Nova avaliação")');
  await prof.fill('.modal input >> nth=0', 'Trabalho em grupo');
  await prof.selectOption('.modal select', 'trabalho');
  await foto(prof, 'diario-nova-avaliacao');
  await prof.keyboard.press('Escape');
  await prof.selectOption('label:has-text("Período") select', {label: '2º bimestre (fechado)'});
  await prof.waitForSelector('text=está fechado');
  await foto(prof, 'diario-fechado');
  await prof.selectOption('label:has-text("Período") select', {label: '4º bimestre'});
  await prof.click('role=tab[name="Chamada"]');
  await foto(prof, 'chamada-lista');
  await prof.click('button:has-text("+ Registrar chamada")');
  const linhas = prof.locator('.linha-chamada');
  await linhas.nth(2).locator('button[title="Falta"]').click();
  await linhas.nth(5).locator('button[title="Atraso"]').click();
  await prof.fill('input[placeholder="Frações equivalentes"]', 'Frações equivalentes');
  await foto(prof, 'chamada-registro', true);

  const profCel = await sessao('ana.matematica', {mobile: true});
  await profCel.goto(BASE + '/');
  await profCel.click('a:has-text("Chamada") >> nth=2');
  await profCel.waitForURL(/aba=chamada/);
  await profCel.click('button:has-text("+ Registrar chamada")');
  await profCel.locator('.linha-chamada').nth(1).locator('button[title="Falta"]').click();
  await foto(profCel, 'chamada-celular');

  const fam = await sessao('familia', {mobile: true});
  await fam.click('text=Lucas Moreira Lima');
  await fam.waitForURL(/\/alunos\//);
  await foto(fam, 'boletim-celular', true);

  const adm = await sessao('direcao');
  await adm.goto(BASE + '/alunos');
  await adm.fill('input[type=search]', 'Lucas Moreira');
  await adm.waitForTimeout(600);
  await adm.click('text=Lucas Moreira Lima');
  await adm.waitForURL(/\/alunos\//);
  await adm.click('tr.clicavel >> nth=0');
  await foto(adm, 'boletim', true);
  await adm.emulateMedia({media: 'print'});
  await foto(adm, 'boletim-impressao', true);
  await adm.emulateMedia({media: 'screen'});
  await adm.goto(BASE + '/escola');
  await foto(adm, 'escola', true);
  await adm.click('button:has-text("Pendências") >> nth=3');
  await adm.waitForSelector('text=diários');
  await foto(adm, 'pendencias');
  await adm.keyboard.press('Escape');
  await adm.click('button:has-text("Alterar regra")');
  await foto(adm, 'regra-media', true);
}

if (roda('m3')) {
  console.log('M3');
  const adm = await sessao('direcao');
  await adm.goto(BASE + '/avisos');
  await adm.click('button:has-text("+ Novo aviso")');
  await adm.fill('.modal input >> nth=0', 'Reunião de pais do 3º bimestre');
  await adm.fill('.modal textarea', 'A reunião será na sexta-feira, às 19h, no pátio coberto. Contamos com a presença de todos.');
  await adm.check('.modal input[type=checkbox]');
  await foto(adm, 'aviso-novo');
  await adm.click('.modal button:has-text("Publicar")');
  await adm.waitForSelector('text=Reunião de pais do 3º bimestre');
  await foto(adm, 'avisos-equipe');

  const fam = await sessao('familia', {mobile: true});
  await fam.goto(BASE + '/avisos');
  await fam.waitForSelector('text=Reunião de pais do 3º bimestre');
  await foto(fam, 'avisos-familia-celular', true);
  await fam.click('button:has-text("Estou ciente")');
  await fam.waitForSelector('text=Ciente');

  await adm.click('button:has-text("Quem leu") >> nth=0');
  await adm.waitForSelector('text=leram');
  await foto(adm, 'aviso-painel');
}

await b.close();
if (erros.length) {
  console.error('Erros no navegador:\n' + erros.join('\n'));
  process.exit(1);
}
