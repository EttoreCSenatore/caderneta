import {describe, expect, it} from 'vitest';
import {armazemMemoria, Cofre, sincronizar, VALIDADE_DIAS} from './offline';

const DIA = 86_400_000;
const item = (o: object = {}) => ({tipo: 'nota' as const, metodo: 'PUT' as const, caminho: '/avaliacoes/a1/notas', corpo: {notas: []}, rotulo: 'Nota', atribuicaoId: 'x', periodoId: 'p', ...o});

async function novo(agora = {t: 1_000_000}) {
  const a = armazemMemoria();
  const c = new Cofre(a, () => agora.t);
  await c.abrir('u1');
  return {a, c, agora};
}

describe('cofre offline', () => {
  it('guarda cifrado: o armazém não contém o texto claro e a leitura devolve o original', async () => {
    const {a, c} = await novo();
    await c.guardar('diario:1', {alunos: ['Maria Souza']});
    const guardado = (await a.get('d:diario:1')) as {ct: ArrayBuffer};
    expect(new TextDecoder('latin1').decode(guardado.ct)).not.toContain('Maria');
    expect(await c.ler('diario:1')).toEqual({alunos: ['Maria Souza']});
  });

  it('não lê um registro movido para outra chave (dado autenticado pela chave)', async () => {
    const {a, c} = await novo();
    await c.guardar('a', {x: 1});
    await a.put('d:b', await a.get('d:a'));
    expect(await c.ler('b')).toBeNull();
  });

  it('outro usuário apaga os dados do anterior', async () => {
    const {a, c} = await novo();
    await c.guardar('a', {x: 1});
    const c2 = new Cofre(a);
    await c2.abrir('u2');
    expect(await c2.ler('a')).toBeNull();
  });

  it('apaga tudo depois de 7 dias sem falar com o servidor', async () => {
    const {a, c, agora} = await novo();
    await c.guardar('a', {x: 1});
    agora.t += (VALIDADE_DIAS + 1) * DIA;
    const c2 = new Cofre(a, () => agora.t);
    await c2.abrir('u1');
    expect(await c2.ler('a')).toBeNull();
  });

  it('sincronizar renova a validade e conta os dias restantes', async () => {
    const {c, agora} = await novo();
    agora.t += 5 * DIA;
    expect(await c.diasRestantes()).toBe(2);
    await sincronizar(c, async () => undefined);
    expect(await c.diasRestantes()).toBe(VALIDADE_DIAS);
  });

  it('limpar remove dados, fila e chave', async () => {
    const {a, c} = await novo();
    await c.guardar('a', {x: 1});
    await c.enfileirar(item());
    await c.limpar();
    expect(await a.chaves()).toEqual([]);
    expect(c.aberto).toBe(false);
    expect(await c.pendencias()).toBe(false);
  });
});

describe('fila de envio', () => {
  it('mantém só o último lançamento da mesma célula', async () => {
    const {c} = await novo();
    await c.enfileirar(item({celula: 'av:m', corpo: {v: 1}}));
    await c.enfileirar(item({celula: 'av:m', corpo: {v: 2}}));
    const f = await c.fila();
    expect(f).toHaveLength(1);
    expect(f[0].corpo).toEqual({v: 2});
  });

  it('envia em ordem e esvazia a fila', async () => {
    const {c} = await novo();
    await c.enfileirar(item({rotulo: 'um'}));
    await c.enfileirar(item({rotulo: 'dois'}));
    const vistos: string[] = [];
    const r = await sincronizar(c, async (i) => void vistos.push(i.rotulo));
    expect(vistos).toEqual(['um', 'dois']);
    expect(r).toEqual({enviados: 2, semConexao: false, erros: 0});
    expect(await c.fila()).toEqual([]);
  });

  it('sem conexão para e mantém tudo na fila', async () => {
    const {c} = await novo();
    await c.enfileirar(item({rotulo: 'um'}));
    await c.enfileirar(item({rotulo: 'dois'}));
    const r = await sincronizar(c, async () => Promise.reject({status: 0}));
    expect(r.semConexao).toBe(true);
    expect(await c.fila()).toHaveLength(2);
  });

  it('erro de regra marca o item e segue com os outros; não reenvia o que já falhou', async () => {
    const {c} = await novo();
    await c.enfileirar(item({rotulo: 'ruim'}));
    await c.enfileirar(item({rotulo: 'bom'}));
    const tentativas: string[] = [];
    const r = await sincronizar(c, async (i) => {
      tentativas.push(i.rotulo);
      if (i.rotulo === 'ruim') throw Object.assign(new Error('Período fechado.'), {status: 409});
    });
    expect(r).toEqual({enviados: 1, semConexao: false, erros: 1});
    const f = await c.fila();
    expect(f).toHaveLength(1);
    expect(f[0].erro).toBe('Período fechado.');
    await sincronizar(c, async (i) => void tentativas.push(i.rotulo));
    expect(tentativas).toEqual(['ruim', 'bom']);
  });
});
