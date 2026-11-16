/**
 * Modo offline do diário (M7): só para professores, só notas e chamada das turmas deles.
 *
 * O que fica no aparelho: o diário das turmas (nomes e números dos alunos, notas, chamadas) e a fila do que o
 * professor lançou sem internet. Nada de saúde, anotações, mensagens, CPF ou contatos. Tudo é cifrado (AES-GCM) com
 * uma chave que o navegador guarda sem permitir exportá-la, e apagado ao sair, ao trocar de usuário ou de perfil, ao
 * abrir a tela de entrada sem pendências e após 7 dias sem falar com o servidor.
 *
 * Limite honesto: a cifra protege contra quem copia os arquivos do navegador, não contra quem usa o navegador já
 * desbloqueado. Por isso também vale o bloqueio de tela do celular.
 */

export const VALIDADE_DIAS = 7;
const DIA = 86_400_000;

/** Armazém chave→valor. Em produção é o IndexedDB; nos testes, a memória. */
export interface Armazem {
  get(k: string): Promise<unknown>;
  put(k: string, v: unknown): Promise<void>;
  del(k: string): Promise<void>;
  chaves(): Promise<string[]>;
  limpar(): Promise<void>;
}

export function armazemMemoria(): Armazem {
  const m = new Map<string, unknown>();
  return {
    get: async (k) => m.get(k),
    put: async (k, v) => void m.set(k, v),
    del: async (k) => void m.delete(k),
    chaves: async () => [...m.keys()],
    limpar: async () => m.clear(),
  };
}

export function armazemIndexedDB(): Armazem {
  let abrindo: Promise<IDBDatabase> | null = null;
  const abre = () =>
    (abrindo ??= new Promise((ok, falha) => {
      const r = indexedDB.open('caderneta-offline', 1);
      r.onupgradeneeded = () => r.result.createObjectStore('kv');
      r.onsuccess = () => ok(r.result);
      r.onerror = () => falha(r.error);
    }));
  const pede = async <T>(modo: IDBTransactionMode, f: (s: IDBObjectStore) => IDBRequest<T>) => {
    const db = await abre();
    return new Promise<T>((ok, falha) => {
      const r = f(db.transaction('kv', modo).objectStore('kv'));
      r.onsuccess = () => ok(r.result);
      r.onerror = () => falha(r.error);
    });
  };
  return {
    get: (k) => pede('readonly', (s) => s.get(k)),
    put: async (k, v) => void (await pede('readwrite', (s) => s.put(v, k))),
    del: async (k) => void (await pede('readwrite', (s) => s.delete(k))),
    chaves: async () => (await pede('readonly', (s) => s.getAllKeys())).map(String),
    limpar: async () => void (await pede('readwrite', (s) => s.clear())),
  };
}

export type ItemFila = {
  id: string;
  tipo: 'nota' | 'aula';
  metodo: 'PUT' | 'POST';
  caminho: string;
  corpo: unknown;
  rotulo: string;
  atribuicaoId: string;
  periodoId: string;
  /** só para nota: identifica a célula e permite trocar o lançamento anterior */
  celula?: string;
  criadoEm: number;
  erro?: string;
};

type Cifrado = {iv: Uint8Array; ct: ArrayBuffer};
type Meta = {usuario: string; ultimaSync: number};

const enc = new TextEncoder();
const dec = new TextDecoder();

export class Cofre {
  private chave: CryptoKey | null = null;
  private seq = 0;
  constructor(
    private a: Armazem,
    private agora: () => number = Date.now,
  ) {}

  private async meta(): Promise<Meta | null> {
    return ((await this.a.get('meta')) as Meta | undefined) ?? null;
  }

  /** Abre o cofre do usuário. Dados de outro usuário são apagados. */
  async abrir(usuario: string): Promise<void> {
    const m = await this.meta();
    if (m && m.usuario !== usuario) await this.limpar();
    if (m && m.usuario === usuario && this.agora() - m.ultimaSync > VALIDADE_DIAS * DIA) await this.limpar();
    let k = (await this.a.get('chave')) as CryptoKey | undefined;
    if (!k) {
      k = await crypto.subtle.generateKey({name: 'AES-GCM', length: 256}, false, ['encrypt', 'decrypt']);
      await this.a.put('chave', k);
      await this.a.put('meta', {usuario, ultimaSync: this.agora()} satisfies Meta);
    }
    this.chave = k;
  }

  /** Reabre o cofre existente sem saber quem é o usuário (app aberto sem internet). false se não há ou venceu. */
  async reabrir(): Promise<boolean> {
    const m = await this.meta();
    if (!m) return false;
    if (this.agora() - m.ultimaSync > VALIDADE_DIAS * DIA) {
      await this.limpar();
      return false;
    }
    const k = (await this.a.get('chave')) as CryptoKey | undefined;
    if (!k) return false;
    this.chave = k;
    return true;
  }

  get aberto(): boolean {
    return this.chave !== null;
  }

  async limpar(): Promise<void> {
    this.chave = null;
    await this.a.limpar();
  }

  async registrarSync(): Promise<void> {
    const m = await this.meta();
    if (m) await this.a.put('meta', {...m, ultimaSync: this.agora()});
  }

  /** Dias que faltam para o aparelho apagar tudo por falta de contato com o servidor. */
  async diasRestantes(): Promise<number | null> {
    const m = await this.meta();
    if (!m) return null;
    return Math.max(0, Math.ceil((m.ultimaSync + VALIDADE_DIAS * DIA - this.agora()) / DIA));
  }

  private async cifra(chave: string, valor: unknown): Promise<Cifrado> {
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ct = await crypto.subtle.encrypt({name: 'AES-GCM', iv, additionalData: enc.encode(chave)}, this.chave!, enc.encode(JSON.stringify(valor)));
    return {iv, ct};
  }

  async guardar(chave: string, valor: unknown): Promise<void> {
    if (!this.chave) return;
    await this.a.put(`d:${chave}`, await this.cifra(chave, valor));
  }

  async ler<T>(chave: string): Promise<T | null> {
    if (!this.chave) return null;
    const c = (await this.a.get(`d:${chave}`)) as Cifrado | undefined;
    if (!c) return null;
    try {
      const claro = await crypto.subtle.decrypt({name: 'AES-GCM', iv: c.iv as BufferSource, additionalData: enc.encode(chave)}, this.chave, c.ct);
      return JSON.parse(dec.decode(claro)) as T;
    } catch {
      return null;
    }
  }

  // --- fila de envio ---

  async enfileirar(item: Omit<ItemFila, 'id' | 'criadoEm'>): Promise<void> {
    if (!this.chave) return;
    if (item.celula) {
      for (const f of await this.fila()) if (f.celula === item.celula) await this.remover(f.id); // vale o último lançamento
    }
    const id = `${this.agora()}-${String(this.seq++).padStart(4, '0')}`;
    await this.a.put(`f:${id}`, await this.cifra(`f:${id}`, {...item, id, criadoEm: this.agora()}));
  }

  async fila(): Promise<ItemFila[]> {
    if (!this.chave) return [];
    const itens: ItemFila[] = [];
    for (const k of (await this.a.chaves()).filter((x) => x.startsWith('f:'))) {
      const c = (await this.a.get(k)) as Cifrado | undefined;
      if (!c) continue;
      try {
        const claro = await crypto.subtle.decrypt({name: 'AES-GCM', iv: c.iv as BufferSource, additionalData: enc.encode(k)}, this.chave, c.ct);
        itens.push(JSON.parse(dec.decode(claro)) as ItemFila);
      } catch {
        await this.a.del(k);
      }
    }
    return itens.sort((x, y) => x.id.localeCompare(y.id));
  }

  /** Há algo na fila? Não precisa da chave: só olha se existem itens. */
  async pendencias(): Promise<boolean> {
    return (await this.a.chaves()).some((k) => k.startsWith('f:'));
  }

  async remover(id: string): Promise<void> {
    await this.a.del(`f:${id}`);
  }

  async marcarErro(item: ItemFila, erro: string): Promise<void> {
    await this.a.put(`f:${item.id}`, await this.cifra(`f:${item.id}`, {...item, erro}));
  }
}

export type ResultadoSync = {enviados: number; semConexao: boolean; erros: number};

/**
 * Envia a fila em ordem. `enviar` lança um objeto com `status` (0 = sem conexão, 401 = sessão expirada) em caso de
 * falha. Falhas de regra (409, 422...) ficam na fila marcadas com o motivo, para a pessoa decidir; não travam o resto.
 */
export async function sincronizar(cofre: Cofre, enviar: (i: ItemFila) => Promise<void>): Promise<ResultadoSync> {
  const r: ResultadoSync = {enviados: 0, semConexao: false, erros: 0};
  for (const item of await cofre.fila()) {
    if (item.erro) {
      r.erros++;
      continue;
    }
    try {
      await enviar(item);
      await cofre.remover(item.id);
      r.enviados++;
    } catch (e) {
      const status = (e as {status?: number}).status;
      if (status === 0 || status === 401) {
        r.semConexao = true;
        break;
      }
      await cofre.marcarErro(item, e instanceof Error ? e.message : 'Não foi possível enviar.');
      r.erros++;
    }
  }
  if (!r.semConexao) await cofre.registrarSync();
  return r;
}
