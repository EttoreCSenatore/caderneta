import {useQuery} from '@tanstack/react-query';
import {api} from '../lib/api';
import {NOME_SITUACAO, numBR} from '../lib/formato';
import type {LinhaTempo} from '../lib/tipos';
import {Carregando, Erro, Vazio} from './ui';

const COR: Record<string, string> = {aprovado: 'verde', cursando: '', retido: 'vermelho', transferido: 'laranja', concluido: 'verde'};
const num = (v: number | string | null | undefined) => (v === null || v === undefined ? '—' : numBR(Number(v)));

/** Um cartão por ano letivo: turma, resultado e, quando o perfil pode ver, médias finais e frequência. */
export function LinhaDoTempo({alunoId}: {alunoId: string}) {
  const q = useQuery({queryKey: ['linha-do-tempo', alunoId], queryFn: () => api<LinhaTempo>(`/alunos/${alunoId}/linha-do-tempo`)});
  if (q.isLoading) return <Carregando />;
  if (q.error) return <Erro erro={q.error} />;
  const t = q.data!;
  if (t.anos.length === 0) return <Vazio>Sem matrículas registradas.</Vazio>;
  return (
    <div className="pilha">
      {t.so_publicadas && <p className="suave pequeno" style={{margin: 0}}>Aparecem só as notas que os professores publicaram.</p>}
      {[...t.anos].reverse().map((a) => (
        <article key={a.ano_letivo_id} className="cartao">
          <div className="linha entre">
            <h2 style={{fontSize: '1.15rem', margin: 0}}>{a.ano} · {a.turma}</h2>
            <div className="linha">
              <span className={`selo ${COR[a.situacao] ?? ''}`}>{NOME_SITUACAO[a.situacao] ?? a.situacao}</span>
              {!a.encerrado && <span className="selo">Em andamento</span>}
            </div>
          </div>
          <div className="suave pequeno">{a.serie}{t.notas_visiveis && a.frequencia_geral != null && ` · frequência geral ${num(a.frequencia_geral)}%`}</div>
          {a.disciplinas && a.disciplinas.length > 0 && (
            <table style={{marginTop: '0.6rem'}}>
              <thead><tr><th>Disciplina</th><th>Média final</th><th>Frequência</th><th>Situação</th></tr></thead>
              <tbody>
                {a.disciplinas.map((d) => (
                  <tr key={d.disciplina}>
                    <td>{d.disciplina}</td><td>{num(d.media_anual)}</td><td>{d.frequencia == null ? '—' : `${num(d.frequencia)}%`}</td>
                    <td>{NOME_SITUACAO[d.situacao] ?? d.situacao}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </article>
      ))}
    </div>
  );
}
