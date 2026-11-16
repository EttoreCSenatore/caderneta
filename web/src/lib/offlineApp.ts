/** Liga o cofre offline ao app: estado para a tela, envio da fila, pré-carga das turmas e limpeza. */
import type {QueryClient} from '@tanstack/react-query';
import {useSyncExternalStore} from 'react';
import {api, ApiError} from './api';
import {armazemIndexedDB, Cofre, type ItemFila, sincronizar} from './offline';
import type {Aula, Diario, Me, TurmaResumo} from './tipos';

export const cofre = new Cofre(typeof indexedDB === 'undefined' ? ({} as never) : armazemIndexedDB());
const suportado = typeof indexedDB !== 'undefined' && typeof crypto !== 'undefined' && !!crypto.subtle;

export type EstadoOffline = {online: boolean; ativo: boolean; fila: ItemFila[]; diasRestantes: number | null; enviando: boolean};
let estado: EstadoOffline = {online: typeof navigator === 'undefined' ? true : navigator.onLine, ativo: false, fila: [], diasRestantes: null, enviando: false};
const ouvintes = new Set<() => void>();
const publica = (p: Partial<EstadoOffline>) => {
  estado = {...estado, ...p};
  ouvintes.forEach((f) => f());
};
export const useOffline = () =>
  useSyncExternalStore(
    (f) => (ouvintes.add(f), () => void ouvintes.delete(f)),
    () => estado,
  );

export async function atualizaEstado(): Promise<void> {
  if (!estado.ativo) return;
  publica({fila: await cofre.fila(), diasRestantes: await cofre.diasRestantes()});
}

/** Apaga tudo o que o modo offline guardou neste aparelho. */
export async function limparOffline(): Promise<void> {
  if (!suportado) return;
  await cofre.limpar().catch(() => undefined);
  ligado = null;
  publica({ativo: false, fila: [], diasRestantes: null});
}

/** Tela de entrada: se não há nada pendente de envio, não deixa dados de ninguém no aparelho. */
export async function limparSeSemPendencias(): Promise<void> {
  if (!suportado) return;
  if (!(await cofre.pendencias().catch(() => true))) await limparOffline();
}

export const chaveDiario = (atribuicao: string, periodo: string) => `diario:${atribuicao}:${periodo || '-'}`;
export const chaveAulas = (atribuicao: string, periodo: string) => `aulas:${atribuicao}:${periodo}`;

export async function guardaDiario(d: Diario, periodoPedido: string): Promise<void> {
  if (!estado.ativo) return;
  await cofre.guardar(chaveDiario(d.atribuicao.id, periodoPedido), d).catch(() => undefined);
  await cofre.guardar(chaveDiario(d.atribuicao.id, d.periodo_id), d).catch(() => undefined);
}

export async function lerDiario(atribuicao: string, periodo: string): Promise<Diario | null> {
  if (!estado.ativo) return null;
  const d = await cofre.ler<Diario>(chaveDiario(atribuicao, periodo));
  if (!d) return null;
  const copia = structuredClone(d);
  for (const f of await cofre.fila()) {
    if (f.tipo === 'nota' && f.atribuicaoId === atribuicao && !f.erro) {
      const b = f.corpo as {notas: {matricula_id: string; valor: number | null; status: never}[]};
      const av = f.caminho.split('/')[2];
      copia.notas[av] = {...copia.notas[av]};
      for (const n of b.notas) copia.notas[av][n.matricula_id] = {valor: n.valor, status: n.status};
    }
  }
  return copia;
}

export async function guardaAulas(atribuicao: string, periodo: string, aulas: Aula[]): Promise<void> {
  if (estado.ativo) await cofre.guardar(chaveAulas(atribuicao, periodo), aulas).catch(() => undefined);
}
export const lerAulas = (atribuicao: string, periodo: string) => (estado.ativo ? cofre.ler<Aula[]>(chaveAulas(atribuicao, periodo)) : Promise.resolve(null));

/** Registra no aparelho o que foi lançado sem internet. Só se o modo offline está ativo (professor). */
export async function enfileira(item: Omit<ItemFila, 'id' | 'criadoEm'>): Promise<boolean> {
  if (!estado.ativo) return false;
  await cofre.enfileirar(item);
  await atualizaEstado();
  return true;
}
export const offlineAtivo = () => estado.ativo;
export const semConexao = (e: unknown) => e instanceof ApiError && e.status === 0;

const mesmaChamada = (a: Aula, c: {data: string; quantidade: number; conteudo: string | null; registros: {matricula_id: string; status: string}[]}) =>
  a.data === c.data &&
  a.quantidade === c.quantidade &&
  (a.conteudo ?? null) === c.conteudo &&
  a.registros.length === c.registros.length &&
  c.registros.every((r) => a.registros.some((x) => x.matricula_id === r.matricula_id && x.status === r.status));

async function enviarItem(i: ItemFila): Promise<void> {
  if (i.tipo === 'aula' && i.metodo === 'POST') {
    // Se a resposta se perdeu depois de o servidor gravar, a chamada já existe: não duplica.
    const c = i.corpo as Parameters<typeof mesmaChamada>[1];
    const aulas = await api<Aula[]>(`/atribuicoes/${i.atribuicaoId}/aulas?periodo_id=${i.periodoId}`);
    if (aulas.some((a) => mesmaChamada(a, c))) return;
  }
  await api(i.caminho, {method: i.metodo, body: i.corpo});
}

let emCurso = false;
export async function enviarFila(qc?: QueryClient): Promise<ResultadoEnvio | null> {
  if (!estado.ativo || emCurso || !estado.online) return null;
  emCurso = true;
  publica({enviando: true});
  try {
    const r = await sincronizar(cofre, enviarItem);
    if (r.enviados) await qc?.invalidateQueries({queryKey: ['diario']}).then(() => qc.invalidateQueries({queryKey: ['aulas']}));
    return r;
  } finally {
    emCurso = false;
    publica({enviando: false});
    await atualizaEstado();
  }
}
type ResultadoEnvio = Awaited<ReturnType<typeof sincronizar>>;

export async function descartar(id: string): Promise<void> {
  await cofre.remover(id);
  await atualizaEstado();
}

/** Guarda no aparelho o diário das turmas do professor, para funcionar mesmo se a internet cair. */
async function preCarregar(): Promise<void> {
  const turmas = await api<TurmaResumo[]>('/turmas');
  await cofre.guardar('turmas', turmas);
  await cofre.guardar('escola', await api('/escola'));
  for (const a of turmas.flatMap((t) => t.atribuicoes).slice(0, 15)) {
    const d = await api<Diario>(`/atribuicoes/${a.id}/diario`);
    await guardaDiario(d, '');
    await guardaAulas(a.id, d.periodo_id, await api<Aula[]>(`/atribuicoes/${a.id}/aulas?periodo_id=${d.periodo_id}`));
  }
}

let ligado: string | null = null;
let timer: ReturnType<typeof setInterval> | undefined;

/** Liga (professor) ou desliga e apaga (qualquer outro perfil) o modo offline. Chamado pelo Layout. */
export async function iniciarOffline(me: Me, professor: boolean, qc: QueryClient): Promise<void> {
  if (!suportado) return;
  const usuarioId = me.usuario.id;
  const chave = `${usuarioId}:${professor}`;
  if (ligado === chave) return;
  ligado = chave;
  if (!professor) {
    await cofre.abrir(usuarioId).catch(() => undefined);
    await limparOffline();
    return;
  }
  await cofre.abrir(usuarioId);
  await cofre.guardar('me', me); // para abrir o app sem internet
  publica({ativo: true});
  await atualizaEstado();
  const muda = () => {
    publica({online: navigator.onLine});
    if (navigator.onLine) void enviarFila(qc);
  };
  window.addEventListener('online', muda);
  window.addEventListener('offline', muda);
  clearInterval(timer);
  timer = setInterval(() => void (estado.fila.length && enviarFila(qc)), 60_000);
  if (navigator.onLine) {
    await enviarFila(qc);
    await preCarregar().catch(() => undefined);
    await cofre.registrarSync();
    await atualizaEstado();
  }
}

/** App aberto sem internet: quem é a pessoa e quais turmas, a partir do cofre (só professor, só se não venceu). */
export async function lerMeOffline(): Promise<Me | null> {
  if (!suportado || !(await cofre.reabrir().catch(() => false))) return null;
  return cofre.ler<Me>('me');
}

/** Busca na API; com o modo offline ativo, guarda o resultado e, sem internet, devolve o último guardado. */
export async function comCache<T>(chave: string, buscar: () => Promise<T>): Promise<T> {
  try {
    const v = await buscar();
    if (estado.ativo) void cofre.guardar(chave, v).catch(() => undefined);
    return v;
  } catch (e) {
    if (semConexao(e) && (estado.ativo || cofre.aberto)) {
      const guardado = await cofre.ler<T>(chave);
      if (guardado) return guardado;
    }
    throw e;
  }
}
