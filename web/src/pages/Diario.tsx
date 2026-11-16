import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {type KeyboardEvent, useEffect, useRef, useState} from 'react';
import {Link, useParams, useSearchParams} from 'react-router';
import {Abas, Carregando, Erro, Modal, Vazio} from '../components/ui';
import {api} from '../lib/api';
import {enfileira, guardaAulas, guardaDiario, lerAulas, lerDiario, offlineAtivo, semConexao, useOffline} from '../lib/offlineApp';
import {usePapel} from '../lib/auth';
import {dataBR, leNota, numBR} from '../lib/formato';
import type {Aula, Avaliacao, Diario as TDiario, MediaAluno, StatusNota, StatusPresenca} from '../lib/tipos';

type Aba = 'notas' | 'chamada';
type EstadoCelula = 'salvando' | 'salvo' | 'erro' | 'fila' | undefined;

function textoNota(n?: {valor: number | null; status: StatusNota}): string {
  if (!n) return '';
  if (n.status === 'dispensada') return 'D';
  if (n.status === 'falta_justificada') return 'J';
  return n.valor === null ? '' : numBR(n.valor, 0);
}

const AV_VAZIA = {nome: '', tipo: 'prova', data: '', peso: '1', nota_maxima: '10'};

function FormAvaliacao({d, editar, fechar, justificativa}: {d: TDiario; editar: Avaliacao | null; fechar: () => void; justificativa: string | null}) {
  const qc = useQueryClient();
  const [f, setF] = useState(
    editar
      ? {nome: editar.nome, tipo: editar.tipo, data: editar.data ?? '', peso: String(editar.peso), nota_maxima: String(editar.nota_maxima)}
      : AV_VAZIA,
  );
  const atualiza = () => qc.invalidateQueries({queryKey: ['diario', d.atribuicao.id]});
  const salvar = useMutation({
    mutationFn: () => {
      const body = {
        periodo_id: d.periodo_id,
        nome: f.nome,
        tipo: f.tipo,
        data: f.data || null,
        peso: Number(f.peso.replace(',', '.')),
        nota_maxima: Number(f.nota_maxima.replace(',', '.')),
        recuperacao: f.tipo === 'recuperacao',
        justificativa,
      };
      return editar ? api(`/avaliacoes/${editar.id}`, {method: 'PATCH', body}) : api(`/atribuicoes/${d.atribuicao.id}/avaliacoes`, {body});
    },
    onSuccess: () => {
      atualiza();
      fechar();
    },
  });
  const remover = useMutation({
    mutationFn: () => api(`/avaliacoes/${editar!.id}${justificativa ? `?justificativa=${encodeURIComponent(justificativa)}` : ''}`, {method: 'DELETE'}),
    onSuccess: () => {
      atualiza();
      fechar();
    },
  });
  const periodo = d.periodos.find((p) => p.id === d.periodo_id)!;
  const set = (k: keyof typeof f) => (e: {target: {value: string}}) => setF({...f, [k]: e.target.value});
  return (
    <form className="pilha" onSubmit={(e) => { e.preventDefault(); salvar.mutate(); }}>
      <div className="form-grade">
        <label className="campo">Nome<input required autoFocus placeholder="Prova 1" value={f.nome} onChange={set('nome')} /></label>
        <label className="campo">
          Tipo
          <select value={f.tipo} onChange={set('tipo')}>
            <option value="prova">Prova</option>
            <option value="trabalho">Trabalho</option>
            <option value="participacao">Participação</option>
            <option value="simulado">Simulado</option>
            <option value="recuperacao">Recuperação</option>
            <option value="outro">Outro</option>
          </select>
        </label>
        <label className="campo">Data <span className="dica">(opcional)</span><input type="date" min={periodo.inicio} max={periodo.fim} value={f.data} onChange={set('data')} /></label>
        <label className="campo">Peso<input inputMode="decimal" required value={f.peso} onChange={set('peso')} /></label>
        <label className="campo">Vale<input inputMode="decimal" required value={f.nota_maxima} onChange={set('nota_maxima')} /></label>
      </div>
      {f.tipo === 'recuperacao' && <p className="suave pequeno">A recuperação não entra na média comum: ela age conforme a regra da escola (ex.: substitui a média se for maior).</p>}
      <Erro erro={salvar.error ?? remover.error} />
      <div className="linha entre">
        <button className="botao" disabled={salvar.isPending}>{editar ? 'Salvar' : 'Criar avaliação'}</button>
        {editar && (
          <button type="button" className="botao perigo" onClick={() => confirm(`Remover "${editar.nome}" e as notas lançadas nela?`) && remover.mutate()}>
            Remover
          </button>
        )}
      </div>
    </form>
  );
}

function GradeNotas({d, editavel, justificativa}: {d: TDiario; editavel: boolean; justificativa: string | null}) {
  const qc = useQueryClient();
  const [textos, setTextos] = useState<Record<string, string>>({});
  const [estado, setEstado] = useState<Record<string, EstadoCelula>>({});
  const [medias, setMedias] = useState<Record<string, MediaAluno>>(d.medias);
  const [modal, setModal] = useState<null | 'nova' | Avaliacao>(null);
  const refs = useRef<Record<string, HTMLInputElement | null>>({});
  useEffect(() => setMedias(d.medias), [d.medias]);

  const chave = (av: string, m: string) => `${av}:${m}`;
  const valorDe = (av: string, m: string) => textos[chave(av, m)] ?? textoNota(d.notas[av]?.[m]);

  async function salva(av: Avaliacao, mid: string) {
    const k = chave(av.id, mid);
    const t = textos[k];
    if (t === undefined || t === textoNota(d.notas[av.id]?.[mid])) return;
    const lido = leNota(t);
    if (lido === 'invalido' || (lido.valor !== null && lido.valor > av.nota_maxima)) {
      setEstado((s) => ({...s, [k]: 'erro'}));
      return;
    }
    setEstado((s) => ({...s, [k]: 'salvando'}));
    try {
      const r = await api<{medias: Record<string, MediaAluno>}>(`/avaliacoes/${av.id}/notas`, {
        method: 'PUT',
        body: {notas: [{matricula_id: mid, ...lido}], justificativa},
      });
      d.notas[av.id] = {...d.notas[av.id], [mid]: lido};
      setMedias((m) => ({...m, ...r.medias}));
      setEstado((s) => ({...s, [k]: 'salvo'}));
    } catch (e) {
      if (!justificativa && semConexao(e) && offlineAtivo()) {
        // sem internet: guarda cifrado no aparelho e envia quando voltar
        await enfileira({
          tipo: 'nota',
          metodo: 'PUT',
          caminho: `/avaliacoes/${av.id}/notas`,
          corpo: {notas: [{matricula_id: mid, ...lido}], justificativa: null},
          rotulo: `Nota em ${av.nome}`,
          atribuicaoId: d.atribuicao.id,
          periodoId: d.periodo_id,
          celula: k,
        });
        d.notas[av.id] = {...d.notas[av.id], [mid]: lido};
        setEstado((s) => ({...s, [k]: 'fila'}));
        return;
      }
      setEstado((s) => ({...s, [k]: 'erro'}));
    }
  }

  function tecla(e: KeyboardEvent<HTMLInputElement>, col: number, lin: number) {
    const mover = (l: number, c: number) => {
      const av = d.avaliacoes[c];
      const al = d.alunos[l];
      if (av && al) {
        const el = refs.current[chave(av.id, al.matricula_id)];
        el?.focus();
        el?.select();
      }
    };
    if (e.key === 'Enter' || e.key === 'ArrowDown') { e.preventDefault(); mover(lin + 1, col); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); mover(lin - 1, col); }
  }

  const publicar = useMutation({
    mutationFn: (av: Avaliacao) => api(`/avaliacoes/${av.id}/publicar`, {body: {publicada: !av.publicada}}),
    onSuccess: () => qc.invalidateQueries({queryKey: ['diario', d.atribuicao.id]}),
  });

  return (
    <div className="pilha">
      <div className="linha entre">
        <p className="suave pequeno" style={{margin: 0}}>
          Digite a nota e tecle Enter para descer. <strong>D</strong> = dispensado · <strong>J</strong> = falta justificada (fará 2ª chamada). Salva sozinho.
        </p>
        {editavel && <button className="botao" onClick={() => setModal('nova')}>+ Nova avaliação</button>}
      </div>
      {d.avaliacoes.length === 0 ? (
        <Vazio>Nenhuma avaliação neste período.{editavel && ' Crie a primeira para começar a lançar notas.'}</Vazio>
      ) : (
        <div className="cartao tabela-rolagem" style={{padding: 0}}>
          <table className="grade-notas">
            <thead>
              <tr>
                <th className="fixa">Aluno</th>
                {d.avaliacoes.map((av) => (
                  <th key={av.id} className="col-nota">
                    <button className="cab-avaliacao" disabled={!editavel} onClick={() => setModal(av)} title={editavel ? 'Editar avaliação' : undefined}>
                      <span>{av.nome}</span>
                      <span className="suave">{av.recuperacao ? 'recuperação' : `peso ${numBR(av.peso, 0)}`} · vale {numBR(av.nota_maxima, 0)}</span>
                    </button>
                    {(editavel || justificativa) && (
                      <button className={`selo ${av.publicada ? 'verde' : 'laranja'} publicar`} onClick={() => publicar.mutate(av)} title="Mostrar ou esconder para alunos e famílias">
                        {av.publicada ? 'Publicada' : 'Não publicada'}
                      </button>
                    )}
                    {!editavel && !justificativa && <span className={`selo ${av.publicada ? 'verde' : 'laranja'}`}>{av.publicada ? 'Publicada' : 'Não publicada'}</span>}
                  </th>
                ))}
                <th className="col-nota">Média</th>
                <th className="col-nota so-desktop">Freq.</th>
              </tr>
            </thead>
            <tbody>
              {d.alunos.map((al, lin) => {
                const m = medias[al.matricula_id];
                const abaixo = m?.media !== null && m?.media !== undefined && m.media < d.regra.media_aprovacao;
                return (
                  <tr key={al.matricula_id}>
                    <td className="fixa"><Link to={`/alunos/${al.aluno_id}`}>{al.nome}</Link></td>
                    {d.avaliacoes.map((av, col) => {
                      const k = chave(av.id, al.matricula_id);
                      return (
                        <td key={av.id} className="col-nota">
                          <input
                            ref={(el) => { refs.current[k] = el; }}
                            className={`celula ${estado[k] ?? ''}`}
                            aria-label={`${av.nome} de ${al.nome}`}
                            inputMode="decimal"
                            readOnly={!editavel && !justificativa}
                            value={valorDe(av.id, al.matricula_id)}
                            onChange={(e) => { setTextos((t) => ({...t, [k]: e.target.value})); setEstado((s) => ({...s, [k]: undefined})); }}
                            onBlur={() => salva(av, al.matricula_id)}
                            onKeyDown={(e) => tecla(e, col, lin)}
                            onFocus={(e) => e.target.select()}
                          />
                        </td>
                      );
                    })}
                    <td className="col-nota">
                      <strong className={abaixo ? 'nota-baixa' : ''}>{numBR(m?.media ?? null)}</strong>
                      {m?.recuperacao_aplicada && <span className="selo pequeno" title="Média após recuperação">rec</span>}
                    </td>
                    <td className="col-nota so-desktop suave">{al.frequencia === null ? '—' : `${numBR(al.frequencia)}%`}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <Modal titulo={modal === 'nova' ? 'Nova avaliação' : 'Editar avaliação'} aberto={modal !== null} fechar={() => setModal(null)}>
        {modal && <FormAvaliacao d={d} editar={modal === 'nova' ? null : modal} fechar={() => setModal(null)} justificativa={justificativa} />}
      </Modal>
    </div>
  );
}

const ROTULO_PRESENCA: [StatusPresenca, string, string][] = [
  ['presente', 'P', 'Presente'],
  ['falta', 'F', 'Falta'],
  ['justificada', 'J', 'Falta justificada'],
  ['atraso', 'A', 'Atraso'],
];

function hojeISO() {
  const h = new Date();
  return `${h.getFullYear()}-${String(h.getMonth() + 1).padStart(2, '0')}-${String(h.getDate()).padStart(2, '0')}`;
}

function Chamada({d, editavel, justificativa}: {d: TDiario; editavel: boolean; justificativa: string | null}) {
  const qc = useQueryClient();
  const periodo = d.periodos.find((p) => p.id === d.periodo_id)!;
  const aulas = useQuery({queryKey: ['aulas', d.atribuicao.id, d.periodo_id], queryFn: async () => {
    try {
      const l = await api<Aula[]>(`/atribuicoes/${d.atribuicao.id}/aulas?periodo_id=${d.periodo_id}`);
      void guardaAulas(d.atribuicao.id, d.periodo_id, l);
      return l;
    } catch (e) {
      const guardadas = semConexao(e) ? await lerAulas(d.atribuicao.id, d.periodo_id) : null;
      if (guardadas) return guardadas;
      throw e;
    }
  }});
  const pendentes = useOffline().fila.filter((f) => f.tipo === 'aula' && f.atribuicaoId === d.atribuicao.id && f.periodoId === d.periodo_id);
  const [edit, setEdit] = useState<null | {id?: string; data: string; quantidade: number; conteudo: string; status: Record<string, StatusPresenca>}>(null);
  const hoje = hojeISO();
  const maxData = periodo.fim < hoje ? periodo.fim : hoje;
  const abrirNova = () => setEdit({data: maxData, quantidade: 1, conteudo: '', status: {}});
  const abrir = (a: Aula) =>
    setEdit({id: a.id, data: a.data, quantidade: a.quantidade, conteudo: a.conteudo ?? '', status: Object.fromEntries(a.registros.map((r) => [r.matricula_id, r.status]))});
  const salvar = useMutation({
    mutationFn: () => {
      const body = {
        data: edit!.data,
        quantidade: edit!.quantidade,
        conteudo: edit!.conteudo || null,
        registros: Object.entries(edit!.status).filter(([, s]) => s !== 'presente').map(([matricula_id, status]) => ({matricula_id, status})),
        justificativa,
      };
      const metodo = edit!.id ? 'PUT' : 'POST';
      const caminho = edit!.id ? `/aulas/${edit!.id}` : `/atribuicoes/${d.atribuicao.id}/aulas`;
      return api(caminho, {method: metodo, body}).catch(async (e) => {
        if (justificativa || !semConexao(e) || !offlineAtivo()) throw e;
        // sem internet: guarda cifrado no aparelho e envia quando voltar
        await enfileira({tipo: 'aula', metodo, caminho, corpo: body, rotulo: `Chamada de ${dataBR(body.data)}`, atribuicaoId: d.atribuicao.id, periodoId: d.periodo_id});
      });
    },
    onSuccess: () => {
      setEdit(null);
      qc.invalidateQueries({queryKey: ['aulas', d.atribuicao.id]});
      qc.invalidateQueries({queryKey: ['diario', d.atribuicao.id]});
    },
  });
  const pode = editavel || !!justificativa;
  if (edit) {
    const ausentes = Object.values(edit.status).filter((s) => s === 'falta' || s === 'justificada').length;
    return (
      <form className="cartao pilha" onSubmit={(e) => { e.preventDefault(); salvar.mutate(); }}>
        <div className="form-grade">
          <label className="campo">Data<input type="date" required min={periodo.inicio} max={maxData} value={edit.data} onChange={(e) => setEdit({...edit, data: e.target.value})} /></label>
          <label className="campo">
            Aulas
            <select value={edit.quantidade} onChange={(e) => setEdit({...edit, quantidade: Number(e.target.value)})}>
              <option value={1}>1 aula</option><option value={2}>2 aulas (dupla)</option><option value={3}>3 aulas</option>
            </select>
          </label>
          <label className="campo">Conteúdo <span className="dica">(opcional)</span><input value={edit.conteudo} onChange={(e) => setEdit({...edit, conteudo: e.target.value})} placeholder="Frações equivalentes" /></label>
        </div>
        <p className="suave pequeno" style={{margin: 0}}>Todos começam presentes. Toque em F para falta. {ausentes > 0 && <strong>{ausentes} ausente(s).</strong>}</p>
        <div className="lista">
          {d.alunos.map((al) => {
            const atual = edit.status[al.matricula_id] ?? 'presente';
            return (
              <div key={al.matricula_id} className="item linha-chamada">
                <span style={{flex: 1}}>{al.nome}</span>
                <div className="segmentado" role="radiogroup" aria-label={`Presença de ${al.nome}`}>
                  {ROTULO_PRESENCA.map(([s, curto, longo]) => (
                    <button
                      type="button"
                      key={s}
                      role="radio"
                      aria-checked={atual === s}
                      title={longo}
                      className={atual === s ? `ativo ${s}` : ''}
                      onClick={() => setEdit({...edit, status: {...edit.status, [al.matricula_id]: s}})}>
                      {curto}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
        <Erro erro={salvar.error} />
        <div className="linha">
          <button className="botao" disabled={salvar.isPending}>Salvar chamada</button>
          <button type="button" className="botao secundario" onClick={() => setEdit(null)}>Cancelar</button>
        </div>
      </form>
    );
  }
  return (
    <div className="pilha">
      <div className="linha entre">
        <p className="suave" style={{margin: 0}}>{d.aulas_dadas} aula(s) dadas no {periodo.nome.toLowerCase()}.</p>
        {pode && <button className="botao" onClick={abrirNova}>+ Registrar chamada</button>}
      </div>
      {pendentes.map((f) => (
        <div key={f.id} className="item cartao">
          <strong>{f.rotulo}</strong>
          <span className="selo">{f.erro ? 'com problema' : 'aguardando envio'}</span>
        </div>
      ))}
      {aulas.isLoading && <Carregando />}
      {aulas.data?.length === 0 && <Vazio>Nenhuma aula registrada neste período.</Vazio>}
      {!!aulas.data?.length && (
        <div className="cartao lista">
          {aulas.data.map((a) => {
            const f = a.registros.filter((r) => r.status === 'falta' || r.status === 'justificada').length;
            return (
              <button key={a.id} className="item item-botao" onClick={() => abrir(a)} disabled={!pode}>
                <strong style={{minWidth: 96}}>{dataBR(a.data)}</strong>
                <span style={{flex: 1}} className="suave">{a.conteudo || 'Sem conteúdo registrado'}</span>
                <span className="selo">{a.quantidade} aula(s)</span>
                <span className={`selo ${f ? 'vermelho' : 'verde'}`}>{f ? `${f} falta(s)` : 'todos presentes'}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function Diario() {
  const {id = ''} = useParams();
  const papel = usePapel();
  const [busca, setBusca] = useSearchParams();
  const periodoId = busca.get('periodo') ?? '';
  const [aba, setAba] = useState<Aba>((busca.get('aba') as Aba) ?? 'notas');
  const [justificativa, setJustificativa] = useState<string | null>(null);
  const [pedeJust, setPedeJust] = useState(false);
  const [textoJust, setTextoJust] = useState('');
  const q = useQuery({
    queryKey: ['diario', id, periodoId],
    queryFn: async () => {
      try {
        const d = await api<TDiario>(`/atribuicoes/${id}/diario${periodoId ? `?periodo_id=${periodoId}` : ''}`);
        void guardaDiario(d, periodoId);
        return d;
      } catch (e) {
        const guardado = semConexao(e) ? await lerDiario(id, periodoId) : null;
        if (guardado) return guardado;
        throw e;
      }
    },
  });
  if (q.isLoading) return <Carregando />;
  if (q.error) return <Erro erro={q.error} />;
  const d = q.data!;
  const periodo = d.periodos.find((p) => p.id === d.periodo_id)!;
  return (
    <>
      <div className="topo">
        <div>
          <Link to={`/turmas/${d.atribuicao.turma.id}`} className="pequeno">← {d.atribuicao.turma.nome}</Link>
          <h1>{d.atribuicao.disciplina} · {d.atribuicao.turma.nome}</h1>
          <div className="suave">{d.atribuicao.professor} · média para aprovação {numBR(d.regra.media_aprovacao)}</div>
        </div>
        <label className="campo" style={{minWidth: 200}}>
          Período
          <select value={d.periodo_id} onChange={(e) => setBusca({periodo: e.target.value, aba})}>
            {d.periodos.map((p) => <option key={p.id} value={p.id}>{p.nome}{p.fechado ? ' (fechado)' : ''}</option>)}
          </select>
        </label>
      </div>
      {periodo.fechado && !justificativa && (
        <div className="aviso atencao" style={{marginBottom: '1rem'}}>
          <div>
            O {periodo.nome.toLowerCase()} está <strong>fechado</strong>. {papel === 'admin' ? 'Correções exigem justificativa e ficam registradas.' : 'Para corrigir, fale com a direção.'}
          </div>
        </div>
      )}
      {papel === 'admin' && !justificativa && (
        <div style={{marginBottom: '1rem'}}><button className="botao secundario pequeno" onClick={() => setPedeJust(true)}>Corrigir este diário</button></div>
      )}
      {justificativa && <div className="aviso atencao" style={{marginBottom: '1rem'}}>Modo correção: “{justificativa}”. Cada alteração fica registrada na auditoria.</div>}
      <Abas abas={[['notas', 'Notas'], ['chamada', 'Chamada']]} ativa={aba} mudar={(a) => { setAba(a); setBusca({periodo: d.periodo_id, aba: a}); }} />
      {aba === 'notas' ? <GradeNotas key={d.periodo_id} d={d} editavel={d.pode_editar} justificativa={justificativa} /> : <Chamada key={d.periodo_id} d={d} editavel={d.pode_editar} justificativa={justificativa} />}
      <Modal titulo="Corrigir diário" aberto={pedeJust} fechar={() => setPedeJust(false)}>
        <form className="pilha" onSubmit={(e) => { e.preventDefault(); setJustificativa(textoJust.trim()); setPedeJust(false); }}>
          <p className="suave">A direção pode corrigir notas e chamadas de qualquer diário, inclusive de períodos fechados. Informe o motivo: ele fica registrado junto com cada alteração.</p>
          <label className="campo">Justificativa<input required minLength={5} maxLength={300} value={textoJust} onChange={(e) => setTextoJust(e.target.value)} placeholder="Revisão de prova pedida pela família" /></label>
          <button className="botao">Entrar no modo correção</button>
        </form>
      </Modal>
    </>
  );
}
