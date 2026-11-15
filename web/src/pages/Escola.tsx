import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {Carregando, Erro} from '../components/ui';
import {api} from '../lib/api';
import {dataBR, periodoAtual} from '../lib/formato';
import type {Disciplina, Escola as TEscola} from '../lib/tipos';

function NovoAno() {
  const qc = useQueryClient();
  const ano = new Date().getFullYear();
  const [f, setF] = useState({ano, tipo_periodo: 'bimestre', inicio: `${ano}-02-02`, fim: `${ano}-12-11`});
  const criar = useMutation({
    mutationFn: () => api('/anos-letivos', {body: f}),
    onSuccess: () => qc.invalidateQueries({queryKey: ['escola']}),
  });
  return (
    <form className="pilha" onSubmit={(e) => { e.preventDefault(); criar.mutate(); }}>
      <div className="form-grade">
        <label className="campo">Ano<input type="number" value={f.ano} onChange={(e) => setF({...f, ano: Number(e.target.value)})} /></label>
        <label className="campo">
          Divisão
          <select value={f.tipo_periodo} onChange={(e) => setF({...f, tipo_periodo: e.target.value})}>
            <option value="bimestre">Bimestres (4)</option>
            <option value="trimestre">Trimestres (3)</option>
            <option value="semestre">Semestres (2)</option>
          </select>
        </label>
        <label className="campo">Início<input type="date" value={f.inicio} onChange={(e) => setF({...f, inicio: e.target.value})} /></label>
        <label className="campo">Fim<input type="date" value={f.fim} onChange={(e) => setF({...f, fim: e.target.value})} /></label>
      </div>
      <Erro erro={criar.error} />
      <div><button className="botao" disabled={criar.isPending}>Criar ano letivo</button></div>
    </form>
  );
}

export default function Escola() {
  const qc = useQueryClient();
  const escola = useQuery({queryKey: ['escola'], queryFn: () => api<TEscola>('/escola')});
  const disc = useQuery({queryKey: ['disciplinas'], queryFn: () => api<Disciplina[]>('/disciplinas')});
  const [nova, setNova] = useState('');
  const addDisc = useMutation({
    mutationFn: () => api('/disciplinas', {body: {nome: nova}}),
    onSuccess: () => { setNova(''); qc.invalidateQueries({queryKey: ['disciplinas']}); },
  });
  if (escola.isLoading) return <Carregando />;
  if (escola.error) return <Erro erro={escola.error} />;
  const e = escola.data!;
  const ano = e.ano_atual;
  const atual = ano && periodoAtual(ano.periodos);
  return (
    <>
      <div className="topo">
        <div><h1>{e.nome}</h1><div className="suave">{[e.cidade, e.uf].filter(Boolean).join(' / ')}</div></div>
      </div>
      <div className="cartao">
        <h2>Ano letivo {ano?.ano ?? ''}</h2>
        {ano ? (
          <table>
            <thead><tr><th>Período</th><th>Início</th><th>Fim</th><th>Situação</th></tr></thead>
            <tbody>
              {ano.periodos.map((p) => (
                <tr key={p.id}>
                  <td><strong>{p.nome}</strong></td><td>{dataBR(p.inicio)}</td><td>{dataBR(p.fim)}</td>
                  <td>{p.fechado ? <span className="selo">Fechado</span> : p.id === atual?.id ? <span className="selo verde">Em andamento</span> : <span className="suave">Aberto</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <NovoAno />
        )}
      </div>
      <div className="cartao">
        <h2>Disciplinas</h2>
        <div className="linha" style={{gap: '0.4rem', marginBottom: '1rem'}}>
          {disc.data?.map((d) => <span key={d.id} className={`selo${d.ativo ? '' : ' laranja'}`}>{d.nome}</span>)}
        </div>
        <form className="linha" onSubmit={(ev) => { ev.preventDefault(); addDisc.mutate(); }}>
          <input aria-label="Nova disciplina" placeholder="Nova disciplina" required value={nova} onChange={(ev) => setNova(ev.target.value)} style={{flex: 1, marginTop: 0, minWidth: 180}} />
          <button className="botao">Adicionar</button>
        </form>
        <Erro erro={addDisc.error} />
      </div>
    </>
  );
}
