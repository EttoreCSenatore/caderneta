import {useQuery} from '@tanstack/react-query';
import {Fragment, useState} from 'react';
import {api} from '../lib/api';
import {dataBR, NOME_SITUACAO, nomeExibicao, numBR} from '../lib/formato';
import type {Aluno, Boletim as TBoletim} from '../lib/tipos';
import {Carregando, Erro, Vazio} from './ui';

const COR_SITUACAO: Record<string, string> = {
  aprovado: 'verde',
  cursando: '',
  abaixo_da_media: 'laranja',
  reprovado: 'vermelho',
  reprovado_por_falta: 'vermelho',
};

export function Boletim({aluno, escola}: {aluno: Aluno; escola?: string}) {
  const q = useQuery({queryKey: ['boletim', aluno.id], queryFn: () => api<TBoletim>(`/alunos/${aluno.id}/boletim`)});
  const [aberta, setAberta] = useState<string | null>(null);
  if (q.isLoading) return <Carregando />;
  if (q.error) return <Erro erro={q.error} />;
  const b = q.data!;
  if (!b.turma || !b.regra) return <Vazio>O aluno não está matriculado no ano letivo atual.</Vazio>;
  const aprov = b.regra.media_aprovacao;
  const nota = (v: number | null) => <span className={v !== null && v < aprov ? 'nota-baixa' : ''}>{v === null ? '—' : numBR(v)}</span>;
  return (
    <div className="pilha boletim">
      <div className="so-impressao">
        <h1 style={{marginBottom: 0}}>Boletim {b.ano}</h1>
        <p>{escola} · {nomeExibicao(aluno)} · {b.turma.nome} ({b.turma.serie}) · RA {aluno.ra ?? '—'}</p>
      </div>
      <div className="linha entre nao-imprimir">
        <div className="linha" style={{gap: '0.5rem'}}>
          <span className="selo">Média para aprovação: {numBR(aprov)}</span>
          <span className="selo">Frequência mínima: {b.regra.frequencia_minima}%</span>
          {b.frequencia_geral != null && <span className={`selo ${b.frequencia_geral < b.regra.frequencia_minima ? 'vermelho' : 'verde'}`}>Frequência geral: {numBR(b.frequencia_geral)}%</span>}
        </div>
        <button className="botao secundario pequeno" onClick={() => window.print()}>Imprimir / salvar PDF</button>
      </div>
      {b.somente_publicadas && <p className="suave pequeno nao-imprimir" style={{margin: 0}}>Aparecem as avaliações que o professor já publicou. Toque numa disciplina para ver as notas.</p>}
      {b.disciplinas.length === 0 ? (
        <Vazio>Nenhuma disciplina com professor atribuído.</Vazio>
      ) : (
        <>
        <div className="boletim-cartoes nao-imprimir">
          {b.disciplinas.map((d) => (
            <div key={d.atribuicao_id} className="cartao">
              <div className="linha entre" style={{flexWrap: 'nowrap'}}>
                <div>
                  <strong>{d.disciplina}</strong>
                  <div className="suave pequeno">{d.professor}</div>
                </div>
                <div style={{textAlign: 'right'}}>
                  <div className="media-grande">{nota(d.media_anual)}</div>
                  <span className={`selo ${COR_SITUACAO[d.situacao]}`}>{NOME_SITUACAO[d.situacao]}</span>
                </div>
              </div>
              <div className="periodos-mini">
                {d.periodos.map((p, i) => (
                  <div key={p.periodo_id}>
                    <span className="suave">{i + 1}º</span>
                    <strong>{nota(p.media)}{p.recuperacao_aplicada && <sup> R</sup>}</strong>
                  </div>
                ))}
              </div>
              <div className="suave pequeno">
                {d.faltas} falta(s){d.faltas_justificadas > 0 && ` (${d.faltas_justificadas} justificadas)`} · frequência {d.frequencia === null ? '—' : `${numBR(d.frequencia)}%`}
              </div>
              {d.periodos.some((p) => p.avaliacoes.length) && (
                <details>
                  <summary className="pequeno">Ver notas</summary>
                  {d.periodos.filter((p) => p.avaliacoes.length).map((p) => (
                    <div key={p.periodo_id} style={{marginTop: '0.5rem'}}>
                      <strong className="pequeno">{b.periodos.find((x) => x.id === p.periodo_id)?.nome}</strong>
                      <ul className="lista-notas">
                        {p.avaliacoes.map((av) => (
                          <li key={av.id}>
                            <span>{av.nome}</span>
                            <strong>{av.status === 'dispensada' ? 'Dispensado' : av.status === 'falta_justificada' ? '2ª chamada' : av.valor === null ? '—' : `${numBR(av.valor)} / ${numBR(av.nota_maxima, 0)}`}</strong>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </details>
              )}
            </div>
          ))}
        </div>
        <div className="cartao tabela-rolagem boletim-tabela" style={{padding: 0}}>
          <table className="tabela-boletim">
            <thead>
              <tr>
                <th>Disciplina</th>
                {b.periodos.map((p) => <th key={p.id} className="num">{p.nome.replace(' bimestre', 'º bim').replace('ºº', 'º').replace(' trimestre', 'º tri').replace(' semestre', 'º sem')}</th>)}
                <th className="num">Média</th>
                <th className="num">Faltas</th>
                <th className="num">Freq.</th>
                <th>Situação</th>
              </tr>
            </thead>
            <tbody>
              {b.disciplinas.map((d) => (
                <Fragment key={d.atribuicao_id}>
                  <tr className="clicavel" onClick={() => setAberta(aberta === d.atribuicao_id ? null : d.atribuicao_id)} aria-expanded={aberta === d.atribuicao_id}>
                    <td><strong>{d.disciplina}</strong><div className="suave pequeno">{d.professor}</div></td>
                    {d.periodos.map((p) => <td key={p.periodo_id} className="num">{nota(p.media)}{p.recuperacao_aplicada && <sup title="Após recuperação"> R</sup>}</td>)}
                    <td className="num"><strong>{nota(d.media_anual)}</strong></td>
                    <td className="num">{d.faltas}{d.faltas_justificadas > 0 && <span className="suave pequeno"> ({d.faltas_justificadas} just.)</span>}</td>
                    <td className="num">{d.frequencia === null ? '—' : `${numBR(d.frequencia)}%`}</td>
                    <td><span className={`selo ${COR_SITUACAO[d.situacao]}`}>{NOME_SITUACAO[d.situacao]}</span></td>
                  </tr>
                  {aberta === d.atribuicao_id && (
                    <tr className="detalhe nao-imprimir">
                      <td colSpan={b.periodos.length + 5}>
                        {d.periodos.every((p) => p.avaliacoes.length === 0) ? (
                          <span className="suave">Nenhuma avaliação {b.somente_publicadas ? 'publicada' : 'lançada'} ainda.</span>
                        ) : (
                          <div className="form-grade">
                            {d.periodos.filter((p) => p.avaliacoes.length).map((p) => (
                              <div key={p.periodo_id}>
                                <strong>{b.periodos.find((x) => x.id === p.periodo_id)?.nome}</strong>
                                <ul className="lista-notas">
                                  {p.avaliacoes.map((av) => (
                                    <li key={av.id}>
                                      <span>{av.nome}{av.data && <span className="suave"> · {dataBR(av.data)}</span>}{!av.publicada && <span className="selo laranja pequeno"> não publicada</span>}</span>
                                      <strong>
                                        {av.status === 'dispensada' ? 'Dispensado' : av.status === 'falta_justificada' ? '2ª chamada' : av.valor === null ? '—' : `${numBR(av.valor)} / ${numBR(av.nota_maxima, 0)}`}
                                      </strong>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            ))}
                          </div>
                        )}
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
        </>
      )}
      <p className="suave pequeno so-impressao">Emitido pela Caderneta em {new Date().toLocaleDateString('pt-BR')}. Médias calculadas automaticamente pela regra da escola.</p>
    </div>
  );
}
