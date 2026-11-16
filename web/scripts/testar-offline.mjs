/**
 * Teste de ponta a ponta do modo offline com um Chromium de verdade (service worker + internet cortada).
 * Precisa de: API em :8000 com o seed, e o build servido em :4173 (`npm run build && npx vite preview`).
 * Uso: node scripts/testar-offline.mjs   (conta fictícia de demonstração, só existe no ambiente local)
 */
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const b = await chromium.launch();
const ctx = await b.newContext({viewport: {width: 375, height: 812}, serviceWorkers: 'allow'});
const p = await ctx.newPage();
await p.goto('http://localhost:4173/entrar');
await p.getByRole('textbox').first().fill('ana.matematica@demo.caderneta.dev');
await p.locator('input[type=password]').fill('caderneta-demo');
await p.getByRole('button', {name: 'Entrar'}).click();
await p.waitForURL('http://localhost:4173/');
await p.waitForTimeout(7000); // pré-carga do diário
await p.reload();
await p.waitForTimeout(2000);
const controlado = await p.evaluate(() => !!navigator.serviceWorker.controller);
assert(controlado, 'o service worker deveria controlar a página');
await ctx.setOffline(true);
await p.goto('http://localhost:4173/');
await p.waitForTimeout(2500);
const inicio = await p.innerText('body');
assert(inicio.includes('Olá, Ana') && inicio.includes('Minhas turmas'), 'abrir o app sem internet deveria mostrar o início');
await p.locator('a', {hasText: 'Notas'}).first().click();
await p.waitForTimeout(2000);
const diario = await p.innerText('body');
assert(diario.includes('Matemática · 6º A') && diario.includes('Arthur'), 'o diário deveria abrir sem internet');
console.log('OK: o app abre sem internet e mostra o diário guardado');
await b.close();
