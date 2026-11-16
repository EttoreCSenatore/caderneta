import type {Papel} from './tipos';

export const NOME_PAPEL: Record<Papel, string> = {
  admin: 'Direção / Secretaria',
  coordenacao: 'Coordenação',
  professor: 'Professor(a)',
  responsavel: 'Responsável',
  aluno: 'Aluno(a)',
};

export const NOME_VINCULO: Record<string, string> = {mae: 'Mãe', pai: 'Pai', tutor: 'Tutor(a)', avo: 'Avó/Avô', outro: 'Outro'};

/** Datas da API vêm como AAAA-MM-DD; trata como data local, sem fuso. */
export function dataBR(iso: string | null | undefined): string {
  if (!iso) return '';
  const [a, m, d] = iso.slice(0, 10).split('-');
  return `${d}/${m}/${a}`;
}

export function idade(nascimento: string, hoje = new Date()): number {
  const [a, m, d] = nascimento.split('-').map(Number);
  let anos = hoje.getFullYear() - a;
  if (hoje.getMonth() + 1 < m || (hoje.getMonth() + 1 === m && hoje.getDate() < d)) anos--;
  return anos;
}

export function nomeExibicao(a: {nome: string; sobrenome: string; nome_social?: string | null}): string {
  return `${a.nome_social || a.nome} ${a.sobrenome}`;
}

export function iniciais(nome: string): string {
  const p = nome.trim().split(/\s+/);
  return ((p[0]?.[0] ?? '') + (p.length > 1 ? p[p.length - 1][0] : '')).toUpperCase();
}

/** Período em andamento (ou o próximo) para uma data. */
export function periodoAtual<T extends {inicio: string; fim: string}>(periodos: T[], hoje = new Date()): T | undefined {
  const h = hoje.toISOString().slice(0, 10);
  return periodos.find((p) => p.inicio <= h && h <= p.fim) ?? periodos.find((p) => p.inicio > h);
}

/** Número no formato brasileiro (vírgula decimal); vazio para null. */
export function numBR(v: number | null | undefined, casas = 1): string {
  if (v === null || v === undefined) return '';
  return v.toLocaleString('pt-BR', {minimumFractionDigits: casas, maximumFractionDigits: 2});
}

/** Interpreta o que o professor digita numa célula de nota. */
export function leNota(texto: string): {valor: number | null; status: 'normal' | 'dispensada' | 'falta_justificada'} | 'invalido' {
  const t = texto.trim().toLowerCase();
  if (t === '') return {valor: null, status: 'normal'};
  if (t === 'd') return {valor: null, status: 'dispensada'};
  if (t === 'j') return {valor: null, status: 'falta_justificada'};
  const n = Number(t.replace(',', '.'));
  if (!Number.isFinite(n) || n < 0) return 'invalido';
  return {valor: Math.round(n * 100) / 100, status: 'normal'};
}

export const NOME_SITUACAO: Record<string, string> = {
  cursando: 'Cursando',
  abaixo_da_media: 'Abaixo da média',
  aprovado: 'Aprovado',
  reprovado: 'Reprovado',
  reprovado_por_falta: 'Reprovado por falta',
};
