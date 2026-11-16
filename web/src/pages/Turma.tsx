import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {Link, useNavigate, useParams} from 'react-router';
import {Abas, Avatar, Carregando, Erro, Vazio} from '../components/ui';
import {api} from '../lib/api';
import {useMe, usePapel} from '../lib/auth';
import {nomeExibicao} from '../lib/formato';
import type {Disciplina, MembroEquipe, Turma as TTurma} from '../lib/tipos';

type Aba = 'alunos' | 'professores' | 'saude';

function NovaAtribuicao({turmaId}: {turmaId: string}) {
  const qc = useQueryClient();
  const disc = useQuery({queryKey: ['disciplinas'], queryFn: () => api<Disciplina[]>('/disciplinas')});
  const equipe = useQuery({queryKey: ['equipe'], queryFn: () => api<MembroEquipe[]>('/equipe')});
  const [d, setD] = useState('');
  const [p, setP] = useState('');
  const add = useMutation({
    mutationFn: () => api(`/turmas/${turmaId}/atribuicoes`, {body: {disciplina_id: d, professor_id: p}}),
    onSuccess: () => qc.invalidateQueries({queryKey: ['turma', turmaId]}),
  });
  const profs = equipe.data?.filter((m) => m.papel === 'professor' && m.ativo) ?? [];
  return (
    <form
      className="cartao pilha"
      onSubmit={(e) => {
        e.preventDefault();
        add.mutate();
      }}>
      <h3>Atribuir professor</h3>
      <div className="form-grade">
        <label className="campo">
          Disciplina
          <select required value={d} onChange={(e) => setD(e.target.value)}>
            <option value="">Escolha…</option>
            {disc.data?.filter((x) => x.ativo).map((x) => <option key={x.id} value={x.id}>{x.nome}</option>)}
          </select>
        </label>
        <label className="campo">
          Professor(a)
          <select required value={p} onChange={(e) => setP(e.target.value)}>
            <option value="">Escolha…</option>
            {profs.map((x) => <option key={x.usuario_id} value={x.usuario_id}>{x.nome}</option>)}
          </select>
        </label>
      </div>
      <Erro erro={add.error} />
      <div><button className="botao" disabled={add.isPending}>Atribuir</button></div>
    </form>
  );
}

function Alertas({turmaId}: {turmaId: string}) {
  const q = useQuery({queryKey: ['alertas', turmaId], queryFn: () => api<{aluno_id: string; nome: string; alerta: string}[]>(`/turmas/${turmaId}/alertas-saude`)});
  if (q.isLoading) return <Carregando />;
  if (!q.data?.length) return <Vazio>Nenhum alerta de saúde nesta turma.</Vazio>;
  return (
    <div className="pilha">
      <p className="suave pequeno">Resumo definido pela escola para quem está em sala. Detalhes ficam com a secretaria e a família.</p>
      {q.data.map((a) => (
        <div key={a.aluno_id} className="aviso atencao">
          <div><strong>{a.nome}</strong><div>{a.alerta}</div></div>
        </div>
      ))}
    </div>
  );
}

export default function Turma() {
  const {id = ''} = useParams();
  const papel = usePapel();
  const {data: me} = useMe();
  const nav = useNavigate();
  const qc = useQueryClient();
  const [aba, setAba] = useState<Aba>('alunos');
  const t = useQuery({queryKey: ['turma', id], queryFn: () => api<TTurma>(`/turmas/${id}`)});
  const remover = useMutation({
    mutationFn: (aid: string) => api(`/atribuicoes/${aid}`, {method: 'DELETE'}),
    onSuccess: () => qc.invalidateQueries({queryKey: ['turma', id]}),
  });
  if (t.isLoading) return <Carregando />;
  if (t.error) return <Erro erro={t.error} />;
  const turma = t.data!;
  const abas: [Aba, string][] = [['alunos', `Alunos (${turma.alunos.length})`], ['professores', 'Professores']];
  if (papel === 'admin' || papel === 'coordenacao' || papel === 'professor') abas.push(['saude', 'Alertas de saúde']);
  return (
    <>
      <div className="topo">
        <div>
          <Link to="/turmas" className="pequeno">← Turmas</Link>
          <h1>{turma.nome}</h1>
          <div className="suave">{turma.serie} · {turma.turno}</div>
        </div>
      </div>
      <Abas abas={abas} ativa={aba} mudar={setAba} />
      {aba === 'alunos' && (
        <div className="cartao">
          {turma.alunos.length === 0 ? (
            <Vazio>Nenhum aluno matriculado.</Vazio>
          ) : (
            <div className="tabela-rolagem">
              <table>
                <thead><tr><th>#</th><th>Aluno</th><th>RA</th></tr></thead>
                <tbody>
                  {turma.alunos.map((a, i) => (
                    <tr key={a.id} className="clicavel" onClick={() => nav(`/alunos/${a.id}`)}>
                      <td className="suave">{i + 1}</td>
                      <td><div className="linha" style={{flexWrap: 'nowrap'}}><Avatar nome={nomeExibicao(a)} /> {nomeExibicao(a)}</div></td>
                      <td className="suave">{a.ra}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
      {aba === 'professores' && (
        <div className="pilha">
          <div className="cartao lista">
            {turma.atribuicoes.length === 0 && <Vazio>Nenhum professor atribuído.</Vazio>}
            {turma.atribuicoes.map((a) => (
              <div key={a.id} className="item">
                <Avatar nome={a.professor} />
                <div style={{flex: 1}}>
                  <strong>{a.disciplina}</strong>
                  <div className="suave pequeno">{a.professor}</div>
                </div>
                {(papel === 'admin' || papel === 'coordenacao' || a.professor_id === me?.usuario.id) && (
                  <Link className="botao secundario pequeno" to={`/diario/${a.id}`}>Abrir diário</Link>
                )}
                {papel === 'admin' && (
                  <button className="botao perigo pequeno" onClick={() => remover.mutate(a.id)}>Remover</button>
                )}
              </div>
            ))}
          </div>
          {papel === 'admin' && <NovaAtribuicao turmaId={turma.id} />}
        </div>
      )}
      {aba === 'saude' && <Alertas turmaId={turma.id} />}
    </>
  );
}
