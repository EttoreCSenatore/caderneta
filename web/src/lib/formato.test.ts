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
