import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {Link} from 'react-router';
import {Carregando, Erro, Modal} from '../components/ui';
import {api} from '../lib/api';
import {usePapel} from '../lib/auth';
import {dataBR, numBR, periodoAtual} from '../lib/formato';
import type {Disciplina, Escola as TEscola, Periodo, Regra} from '../lib/tipos';

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

const NOMES = {
  tipo_media: {ponderada: 'Ponderada pelos pesos das avaliações', aritmetica: 'Aritmética (todas valem igual)'},
  recuperacao: {substitui_se_maior: 'Substitui a média, se for maior', media: 'Média entre média e recuperação (se aumentar)', nenhuma: 'Não há recuperação'},
  arredondamento: {decimo: 'Uma casa decimal (6,85 → 6,9)', meio: 'Para o 0,5 mais próximo (6,7 → 6,5)', nenhum: 'Sem arredondamento'},
};

function RegraMedia({periodos}: {periodos: Periodo[]}) {
  const papel = usePapel();
  const qc = useQueryClient();
  const q = useQuery({queryKey: ['regra'], queryFn: () => api<Regra>('/regra-media')});
  const [f, setF] = useState<Regra | null>(null);
  const salvar = useMutation({
    mutationFn: () => api<Regra>('/regra-media', {method: 'PUT', body: f}),
    onSuccess: () => { qc.invalidateQueries({queryKey: ['regra']}); setF(null); },
  });
  if (q.isLoading) return <Carregando />;
  const r = q.data!;
  if (!f) {
    const pesos = r.pesos_periodos ? r.pesos_periodos.map((p) => numBR(p, 0)).join(' · ') : 'todos iguais';
    return (
      <>
        <table><tbody>
          <tr><th style={{width: '45%'}}>Média do período</th><td>{NOMES.tipo_media[r.tipo_media]}</td></tr>
          <tr><th>Pesos dos períodos na média anual</th><td>{pesos}</td></tr>
          <tr><th>Recuperação</th><td>{NOMES.recuperacao[r.recuperacao]}</td></tr>
          <tr><th>Arredondamento</th><td>{NOMES.arredondamento[r.arredondamento]}</td></tr>
          <tr><th>Escala</th><td>0 a {numBR(r.nota_maxima, 0)}</td></tr>
          <tr><th>Média para aprovação</th><td>{numBR(r.media_aprovacao)}</td></tr>
          <tr><th>Frequência mínima</th><td>{r.frequencia_minima}%</td></tr>
        </tbody></table>
        {papel === 'admin' && <div style={{marginTop: '1rem'}}><button className="botao secundario" onClick={() => setF(r)}>Alterar regra</button></div>}
      </>
    );
  }
  const sel = <K extends 'tipo_media' | 'recuperacao' | 'arredondamento'>(k: K) => (
    <select value={f[k]} onChange={(e) => setF({...f, [k]: e.target.value})}>
      {Object.entries(NOMES[k]).map(([v, t]) => <option key={v} value={v}>{t}</option>)}
    </select>
  );
  const usaPesos = !!f.pesos_periodos;
  return (
    <form className="pilha" onSubmit={(e) => { e.preventDefault(); salvar.mutate(); }}>
      <div className="aviso atencao">Mudar a regra recalcula na hora todas as médias do ano, inclusive de períodos fechados. A alteração fica registrada.</div>
      <div className="form-grade">
        <label className="campo">Média do período{sel('tipo_media')}</label>
        <label className="campo">Recuperação{sel('recuperacao')}</label>
        <label className="campo">Arredondamento{sel('arredondamento')}</label>
        <label className="campo">Nota máxima<input type="number" min={1} step="any" value={f.nota_maxima} onChange={(e) => setF({...f, nota_maxima: Number(e.target.value)})} /></label>
        <label className="campo">Média para aprovação<input type="number" min={0} step="0.1" value={f.media_aprovacao} onChange={(e) => setF({...f, media_aprovacao: Number(e.target.value)})} /></label>
        <label className="campo">Frequência mínima (%)<input type="number" min={0} max={100} value={f.frequencia_minima} onChange={(e) => setF({...f, frequencia_minima: Number(e.target.value)})} /></label>
      </div>
      <label className="check"><input type="checkbox" checked={usaPesos} onChange={(e) => setF({...f, pesos_periodos: e.target.checked ? periodos.map(() => 1) : null})} /> Períodos com pesos diferentes na média anual</label>
      {usaPesos && (
        <div className="form-grade">
          {periodos.map((p, i) => (
            <label key={p.id} className="campo">Peso do {p.nome}
              <input type="number" min={0} step="any" value={f.pesos_periodos![i]} onChange={(e) => setF({...f, pesos_periodos: f.pesos_periodos!.map((x, j) => (j === i ? Number(e.target.value) : x))})} />
            </label>
          ))}
        </div>
      )}
      <Erro erro={salvar.error} />
      <div className="linha"><button className="botao" disabled={salvar.isPending}>Salvar regra</button><button type="button" className="botao secundario" onClick={() => setF(null)}>Cancelar</button></div>
    </form>
  );
}

type Pendencia = {atribuicao_id: string; turma: string; disciplina: string; professor: string; avaliacoes: number; notas_em_branco: number; nao_publicadas: number; aulas: number};

function Pendencias({periodo}: {periodo: Periodo}) {
  const q = useQuery({queryKey: ['pendencias', periodo.id], queryFn: () => api<Pendencia[]>(`/periodos/${periodo.id}/pendencias`)});
  if (q.isLoading) return <Carregando />;
  if (q.error) return <Erro erro={q.error} />;
  const ok = (p: Pendencia) => p.avaliacoes > 0 && p.notas_em_branco === 0 && p.nao_publicadas === 0 && p.aulas > 0;
  const comProblema = q.data!.filter((p) => !ok(p));
  return (
    <div className="pilha">
      <p className={comProblema.length ? 'aviso atencao' : 'aviso ok'} style={{margin: 0}}>
        {comProblema.length ? `${comProblema.length} de ${q.data!.length} diários com pendências.` : 'Todos os diários estão completos.'}
      </p>
      <div className="tabela-rolagem">
        <table>
          <thead><tr><th>Turma</th><th>Disciplina</th><th className="num">Avaliações</th><th className="num">Notas em branco</th><th className="num">Não publicadas</th><th className="num">Aulas</th></tr></thead>
          <tbody>
            {q.data!.map((p) => (
              <tr key={p.atribuicao_id}>
                <td>{p.turma}</td>
                <td><Link to={`/diario/${p.atribuicao_id}?periodo=${periodo.id}`}>{p.disciplina}</Link><div className="suave pequeno">{p.professor}</div></td>
                <td className="num">{p.avaliacoes === 0 ? <span className="selo vermelho">0</span> : p.avaliacoes}</td>
                <td className="num">{p.notas_em_branco > 0 ? <span className="selo laranja">{p.notas_em_branco}</span> : '0'}</td>
                <td className="num">{p.nao_publicadas > 0 ? <span className="selo laranja">{p.nao_publicadas}</span> : '0'}</td>
                <td className="num">{p.aulas === 0 ? <span className="selo vermelho">0</span> : p.aulas}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Encarregado() {
  const qc = useQueryClient();
  const q = useQuery({queryKey: ['escola'], queryFn: () => api<TEscola>('/escola')});
  const [f, setF] = useState<{nome: string; email: string} | null>(null);
  const salva = useMutation({
    mutationFn: () => api('/escola', {method: 'PATCH', body: {encarregado_nome: f!.nome || null, encarregado_email: f!.email || null}}),
    onSuccess: () => { qc.invalidateQueries({queryKey: ['escola']}); setF(null); },
  });
  const e = q.data?.encarregado;
  return (
    <div className="cartao pilha">
      <h2 style={{margin: 0}}>Encarregado de proteção de dados (DPO)</h2>
      <p className="suave" style={{margin: 0}}>Canal público para dúvidas e pedidos sobre dados pessoais (LGPD, art. 41). O contato aparece na política de privacidade e na página Meus dados.</p>
      {f ? (
        <form className="pilha" onSubmit={(ev) => { ev.preventDefault(); salva.mutate(); }}>
          <div className="form-grade">
            <label className="campo">Nome<input value={f.nome} maxLength={200} onChange={(ev) => setF({...f, nome: ev.target.value})} /></label>
            <label className="campo">E-mail de contato<input type="email" value={f.email} onChange={(ev) => setF({...f, email: ev.target.value})} /></label>
          </div>
          <Erro erro={salva.error} />
          <div className="linha"><button className="botao" disabled={salva.isPending}>Salvar</button><button type="button" className="botao secundario" onClick={() => setF(null)}>Cancelar</button></div>
        </form>
      ) : (
        <div className="linha entre">
          <span>{e?.nome || e?.email ? `${e.nome ?? ''}${e.nome && e.email ? ' · ' : ''}${e.email ?? ''}` : <span className="suave">Ainda não informado.</span>}</span>
          <button className="botao secundario pequeno" onClick={() => setF({nome: e?.nome ?? '', email: e?.email ?? ''})}>Editar</button>
        </div>
      )}
    </div>
  );
}

export default function Escola() {
  const papel = usePapel();
  const admin = papel === 'admin';
  const qc = useQueryClient();
  const escola = useQuery({queryKey: ['escola'], queryFn: () => api<TEscola>('/escola')});
  const disc = useQuery({queryKey: ['disciplinas'], queryFn: () => api<Disciplina[]>('/disciplinas')});
  const [nova, setNova] = useState('');
  const [pend, setPend] = useState<Periodo | null>(null);
  const addDisc = useMutation({
    mutationFn: () => api('/disciplinas', {body: {nome: nova}}),
    onSuccess: () => { setNova(''); qc.invalidateQueries({queryKey: ['disciplinas']}); },
  });
  const fechar = useMutation({
    mutationFn: ({id, fechado}: {id: string; fechado: boolean}) => api(`/periodos/${id}/fechamento`, {body: {fechado}}),
    onSuccess: () => qc.invalidateQueries({queryKey: ['escola']}),
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
      {admin && <Encarregado />}
      <div className="cartao">
        <h2>Ano letivo {ano?.ano ?? ''}</h2>
        {ano ? (
          <div className="tabela-rolagem">
            <table>
              <thead><tr><th>Período</th><th>Início</th><th>Fim</th><th>Situação</th><th></th></tr></thead>
              <tbody>
                {ano.periodos.map((p) => (
                  <tr key={p.id}>
                    <td><strong>{p.nome}</strong></td><td>{dataBR(p.inicio)}</td><td>{dataBR(p.fim)}</td>
                    <td>{p.fechado ? <span className="selo">Fechado</span> : p.id === atual?.id ? <span className="selo verde">Em andamento</span> : <span className="suave">Aberto</span>}</td>
                    <td>
                      <div className="linha" style={{gap: '0.4rem', justifyContent: 'flex-end'}}>
                        <button className="botao secundario pequeno" onClick={() => setPend(p)}>Pendências</button>
                        {!p.fechado && <button className="botao secundario pequeno" onClick={() => confirm(`Fechar o ${p.nome}? Os professores não poderão mais alterar notas e chamadas desse período.`) && fechar.mutate({id: p.id, fechado: true})}>Fechar</button>}
                        {p.fechado && admin && <button className="botao secundario pequeno" onClick={() => fechar.mutate({id: p.id, fechado: false})}>Reabrir</button>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <Erro erro={fechar.error} />
          </div>
        ) : admin ? (
          <NovoAno />
        ) : (
          <p className="suave">Nenhum ano letivo aberto.</p>
        )}
      </div>
      {ano && (
        <div className="cartao">
          <h2>Regra de cálculo da média</h2>
          <RegraMedia periodos={ano.periodos} />
        </div>
      )}
      <div className="cartao">
        <h2>Disciplinas</h2>
        <div className="linha" style={{gap: '0.4rem', marginBottom: admin ? '1rem' : 0}}>
          {disc.data?.map((d) => <span key={d.id} className={`selo${d.ativo ? '' : ' laranja'}`}>{d.nome}</span>)}
        </div>
        {admin && (
          <form className="linha" onSubmit={(ev) => { ev.preventDefault(); addDisc.mutate(); }}>
            <input aria-label="Nova disciplina" placeholder="Nova disciplina" required value={nova} onChange={(ev) => setNova(ev.target.value)} style={{flex: 1, marginTop: 0, minWidth: 180}} />
            <button className="botao">Adicionar</button>
          </form>
        )}
        <Erro erro={addDisc.error} />
      </div>
      <Modal largo titulo={`Pendências do ${pend?.nome ?? ''}`} aberto={!!pend} fechar={() => setPend(null)}>
        {pend && <Pendencias periodo={pend} />}
      </Modal>
    </>
  );
}
