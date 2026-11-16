import {describe, expect, it} from 'vitest';
import {dataBR, idade, iniciais, nomeExibicao, periodoAtual} from './formato';

describe('formato', () => {
  it('formata datas sem deslocar o fuso', () => {
    expect(dataBR('2026-02-01')).toBe('01/02/2026');
    expect(dataBR(null)).toBe('');
  });
  it('calcula idade considerando o aniversário', () => {
    expect(idade('2013-05-10', new Date(2026, 4, 9))).toBe(12);
    expect(idade('2013-05-10', new Date(2026, 4, 10))).toBe(13);
  });
  it('usa o nome social quando existe', () => {
    expect(nomeExibicao({nome: 'Carlos', sobrenome: 'Lima', nome_social: 'Carla'})).toBe('Carla Lima');
  });
  it('gera iniciais', () => {
    expect(iniciais('Ana Maria Souza')).toBe('AS');
    expect(iniciais('Ana')).toBe('A');
  });
  it('acha o período atual ou o próximo', () => {
    const p = [
      {inicio: '2026-02-01', fim: '2026-04-30', n: 1},
      {inicio: '2026-05-01', fim: '2026-07-10', n: 2},
    ];
    expect(periodoAtual(p, new Date('2026-03-10T12:00:00Z'))?.n).toBe(1);
    expect(periodoAtual(p, new Date('2026-01-10T12:00:00Z'))?.n).toBe(1);
    expect(periodoAtual(p, new Date('2026-12-10T12:00:00Z'))).toBeUndefined();
  });
});

import {leNota, numBR} from './formato';

describe('notas', () => {
  it('lê o que o professor digita', () => {
    expect(leNota('7,5')).toEqual({valor: 7.5, status: 'normal'});
    expect(leNota(' 8 ')).toEqual({valor: 8, status: 'normal'});
    expect(leNota('')).toEqual({valor: null, status: 'normal'});
    expect(leNota('D')).toEqual({valor: null, status: 'dispensada'});
    expect(leNota('j')).toEqual({valor: null, status: 'falta_justificada'});
    expect(leNota('abc')).toBe('invalido');
    expect(leNota('-1')).toBe('invalido');
  });
  it('formata com vírgula', () => {
    expect(numBR(7.5)).toBe('7,5');
    expect(numBR(null)).toBe('');
  });
});
