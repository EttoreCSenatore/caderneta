import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {Abas, Carregando, Erro, Modal, Vazio} from '../components/ui';
import {api} from '../lib/api';
import {usePapel} from '../lib/auth';
import {dataBR} from '../lib/formato';
import type {FeriadoSugerido, ItemCalendario, TipoEvento, TurmaResumo} from '../lib/tipos';

type Visao = 'lista' | 'mes' | 'semana';
const NOME: Record<TipoEvento, string> = {feriado: 'Feriado', sem_aula: 'Sem aula', avaliacao: 'Avaliação', evento: 'Evento', prazo: 'Prazo'};
const COR: Record<TipoEvento, string> = {feriado: 'vermelho', sem_aula: 'laranja', avaliacao: '', evento: 'verde', prazo: 'laranja'};
const DIAS = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom'];
const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const soma = (d: Date, n: number) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
const segunda = (d: Date) => soma(d, -((d.getDay() + 6) % 7));
const VAZIO = {id: '', tipo: 'evento' as TipoEvento, titulo: '', descricao: '', inicio: '', fim: '', turma_id: ''};

function intervalo(visao: Visao, ref: Date): [Date, Date] {
  if (visao === 'semana') { const i = segunda(ref); return [i, soma(i, 6)]; }
  const primeiro = new Date(ref.getFullYear(), ref.getMonth(), 1);
  const ultimo = new Date(ref.getFullYear(), ref.getMonth() + 1, 0);
  return visao === 'mes' ? [segunda(primeiro), soma(segunda(ultimo), 6)] : [primeiro, ultimo];
}
const cobre = (i: ItemCalendario, dia: string) => i.inicio <= dia && i.fim >= dia;

function Chip({i, abre}: {i: ItemCalendario; abre: (i: ItemCalendario) => void}) {
  return (
    <button className={`selo ${COR[i.tipo]}`} style={{display: 'block', width: '100%', textAlign: 'left', overflow: 'hidden', textOverflow: 'ellipsis', border: 0, cursor: 'pointer', marginBottom: 2}} onClick={() => abre(i)} title={i.titulo}>
      {i.titulo}
    </button>
  );
}

function Mes({ref, itens, abre}: {ref: Date; itens: ItemCalendario[]; abre: (i: ItemCalendario) => void}) {
  const [ini, fim] = intervalo('mes', ref);
  const dias: Date[] = [];
  for (let d = ini; d <= fim; d = soma(d, 1)) dias.push(d);
  const hoje = iso(new Date());
  return (
    <div style={{display: 'grid', gridTemplateColumns: 'repeat(7, minmax(0, 1fr))', gap: 4}} role="grid" aria-label="Calendário do mês">
      {DIAS.map((d) => <div key={d} className="suave pequeno" style={{textAlign: 'center', fontWeight: 700}}>{d}</div>)}
      {dias.map((d) => {
        const k = iso(d);
        const fora = d.getMonth() !== ref.getMonth();
        return (
          <div key={k} className="cartao" style={{minHeight: 92, padding: '0.35rem', opacity: fora ? 0.45 : 1, outline: k === hoje ? '2px solid var(--azul)' : undefined}}>
            <div className="pequeno" style={{fontWeight: 700}}>{d.getDate()}</div>
            {itens.filter((i) => cobre(i, k)).map((i) => <Chip key={i.origem + i.id + k} i={i} abre={abre} />)}
          </div>
        );
      })}
    </div>
  );
}

function Semana({ref, itens, abre}: {ref: Date; itens: ItemCalendario[]; abre: (i: ItemCalendario) => void}) {
  const ini = segunda(ref);
  return (
    <div className="pilha">
      {DIAS.map((nome, n) => {
        const d = soma(ini, n);
        const k = iso(d);
        const dia = itens.filter((i) => cobre(i, k));
        return (
          <div key={k} className="cartao" style={{padding: '0.6rem 0.9rem'}}>
            <strong>{nome} {dataBR(k).slice(0, 5)}</strong>
            {dia.length === 0 ? <div className="suave pequeno">Sem eventos</div> : dia.map((i) => <Chip key={i.origem + i.id} i={i} abre={abre} />)}
          </div>
        );
      })}
    </div>
  );
}

function Lista({itens, abre}: {itens: ItemCalendario[]; abre: (i: ItemCalendario) => void}) {
  if (itens.length === 0) return <Vazio>Nenhum evento neste período.</Vazio>;
  return (
    <div className="pilha">
      {itens.map((i) => (
        <button key={i.origem + i.id} className="cartao" style={{textAlign: 'left', cursor: 'pointer'}} onClick={() => abre(i)}>
          <div className="linha entre">
            <strong>{i.titulo}</strong>
            <div className="linha"><span className={`selo ${COR[i.tipo]}`}>{NOME[i.tipo]}</span>{i.turma && <span className="selo">{i.turma}</span>}</div>
          </div>
          <div className="suave pequeno">{dataBR(i.inicio)}{i.fim !== i.inicio && ` a ${dataBR(i.fim)}`}</div>
        </button>
      ))}
    </div>
  );
}

function Feriados({aberto, fechar, ano}: {aberto: boolean; fechar: () => void; ano: number}) {
  const qc = useQueryClient();
  const q = useQuery({queryKey: ['feriados', ano], queryFn: () => api<FeriadoSugerido[]>(`/calendario/feriados-sugeridos?ano=${ano}`), enabled: aberto});
  const [marcados, setMarcados] = useState<Record<string, boolean> | null>(null);
  const sel = marcados ?? Object.fromEntries((q.data ?? []).map((f) => [f.data, f.nacional && !f.ja_cadastrado]));
  const importa = useMutation({
    mutationFn: () => api('/calendario/feriados', {body: {ano, datas: Object.keys(sel).filter((d) => sel[d])}}),
    onSuccess: () => { qc.invalidateQueries({queryKey: ['calendario']}); qc.invalidateQueries({queryKey: ['feriados']}); setMarcados(null); fechar(); },
  });
  return (
    <Modal titulo={`Feriados de ${ano}`} aberto={aberto} fechar={fechar} largo>
      <div className="pilha">
        <p className="suave pequeno" style={{margin: 0}}>Feriados nacionais vêm marcados. Os demais (Carnaval, Sexta-feira da Paixão, Corpus Christi) a escola decide. Feriados estaduais e municipais você cadastra como evento. Em feriado e dia sem aula a chamada fica bloqueada.</p>
        {q.isLoading && <Carregando />}
        <Erro erro={q.error} />
        {q.data?.map((f) => (
          <label key={f.data} className="linha">
            <input type="checkbox" disabled={f.ja_cadastrado} checked={f.ja_cadastrado || !!sel[f.data]} onChange={(e) => setMarcados({...sel, [f.data]: e.target.checked})} />
            <span>{dataBR(f.data)} · {f.nome} <span className="suave pequeno">({f.base})</span>{f.ja_cadastrado && ' · já no calendário'}</span>
          </label>
        ))}
        <Erro erro={importa.error} />
        <button className="botao" disabled={importa.isPending} onClick={() => importa.mutate()}>Adicionar ao calendário</button>
      </div>
    </Modal>
  );
}

function Assinatura({aberto, fechar}: {aberto: boolean; fechar: () => void}) {
  const qc = useQueryClient();
  const st = useQuery({queryKey: ['ical'], queryFn: () => api<{ativo: boolean}>('/calendario-ical'), enabled: aberto});
  const [url, setUrl] = useState('');
  const gera = useMutation({mutationFn: () => api<{url: string}>('/calendario-ical', {method: 'POST'}), onSuccess: (r) => { setUrl(r.url); qc.invalidateQueries({queryKey: ['ical']}); }});
  const revoga = useMutation({mutationFn: () => api('/calendario-ical', {method: 'DELETE'}), onSuccess: () => { setUrl(''); qc.invalidateQueries({queryKey: ['ical']}); }});
  return (
    <Modal titulo="Assinar no celular ou no Google Agenda" aberto={aberto} fechar={fechar} largo>
      <div className="pilha">
        <p style={{margin: 0}}>Gere um link e adicione em "Outras agendas, a partir do URL" (Google Agenda) ou "Assinar calendário" (iPhone). O calendário se atualiza sozinho.</p>
        <p className="suave pequeno" style={{margin: 0}}><strong>Quem tem o link vê o calendário.</strong> Não compartilhe. O link aparece só uma vez; gerar outro derruba o anterior.</p>
        {url && <input readOnly value={url} onFocus={(e) => e.currentTarget.select()} aria-label="Link do calendário" />}
        <Erro erro={gera.error || revoga.error} />
        <div className="linha">
          <button className="botao" disabled={gera.isPending} onClick={() => gera.mutate()}>{st.data?.ativo ? 'Gerar novo link' : 'Gerar link'}</button>
          {st.data?.ativo && <button className="botao secundario" disabled={revoga.isPending} onClick={() => revoga.mutate()}>Desativar</button>}
        </div>
      </div>
    </Modal>
  );
}

export default function Calendario() {
  const papel = usePapel();
  const qc = useQueryClient();
  const escreve = papel !== 'responsavel' && papel !== 'aluno';
  const geral = papel === 'admin' || papel === 'coordenacao';
  const [visao, setVisao] = useState<Visao>(() => (window.innerWidth < 700 ? 'lista' : 'mes'));
  const [ref, setRef] = useState(() => new Date());
  const [turma, setTurma] = useState('');
  const [form, setForm] = useState<typeof VAZIO | null>(null);
  const [detalhe, setDetalhe] = useState<ItemCalendario | null>(null);
  const [feriados, setFeriados] = useState(false);
  const [assina, setAssina] = useState(false);
  const [ini, fim] = intervalo(visao, ref);
  const turmas = useQuery({queryKey: ['turmas'], queryFn: () => api<TurmaResumo[]>('/turmas'), enabled: escreve});
  const cal = useQuery({
    queryKey: ['calendario', iso(ini), iso(fim), turma],
    queryFn: () => api<ItemCalendario[]>(`/calendario?inicio=${iso(ini)}&fim=${iso(fim)}${turma ? `&turma_id=${turma}` : ''}`),
  });
  const salva = useMutation({
    mutationFn: (f: typeof VAZIO) => {
      const body = {tipo: f.tipo, titulo: f.titulo, descricao: f.descricao || null, inicio: f.inicio, fim: f.fim || null, turma_id: f.turma_id || null};
      return f.id ? api(`/calendario/eventos/${f.id}`, {method: 'PATCH', body}) : api<{aulas_ja_registradas?: number}>('/calendario/eventos', {body});
    },
    onSuccess: () => { qc.invalidateQueries({queryKey: ['calendario']}); setForm(null); },
  });
  const remove = useMutation({
    mutationFn: (id: string) => api(`/calendario/eventos/${id}`, {method: 'DELETE'}),
    onSuccess: () => { qc.invalidateQueries({queryKey: ['calendario']}); setDetalhe(null); },
  });
  const passo = (n: number) => setRef(visao === 'semana' ? soma(ref, 7 * n) : new Date(ref.getFullYear(), ref.getMonth() + n, 1));
  const titulo = visao === 'semana' ? `${dataBR(iso(ini)).slice(0, 5)} a ${dataBR(iso(fim)).slice(0, 5)}` : ref.toLocaleDateString('pt-BR', {month: 'long', year: 'numeric'});
  const tipos: TipoEvento[] = geral ? ['evento', 'sem_aula', 'feriado', 'avaliacao', 'prazo'] : ['evento', 'avaliacao', 'prazo'];
  const edita = (i: ItemCalendario) => { setDetalhe(null); setForm({id: i.id, tipo: i.tipo, titulo: i.titulo, descricao: i.descricao ?? '', inicio: i.inicio, fim: i.fim, turma_id: i.turma_id ?? ''}); };

  return (
    <>
      <div className="topo">
        <h1>Calendário</h1>
        <div className="linha">
          {geral && <button className="botao secundario" onClick={() => setFeriados(true)}>Feriados</button>}
          <button className="botao secundario" onClick={() => setAssina(true)}>Assinar</button>
          {escreve && <button className="botao" onClick={() => setForm({...VAZIO, inicio: iso(new Date()), turma_id: geral ? '' : (turmas.data?.[0]?.id ?? '')})}>+ Novo evento</button>}
        </div>
      </div>
      <div className="linha entre" style={{marginBottom: '0.75rem'}}>
        <Abas abas={[['lista', 'Lista'], ['mes', 'Mês'], ['semana', 'Semana']]} ativa={visao} mudar={setVisao} />
        <div className="linha">
          {escreve && (
            <select aria-label="Filtrar por turma" value={turma} onChange={(e) => setTurma(e.target.value)} style={{marginTop: 0}}>
              <option value="">Todas as turmas</option>
              {turmas.data?.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}
            </select>
          )}
          <button className="botao secundario pequeno" onClick={() => passo(-1)} aria-label="Anterior">←</button>
          <strong style={{minWidth: '10rem', textAlign: 'center'}}>{titulo.charAt(0).toUpperCase() + titulo.slice(1)}</strong>
          <button className="botao secundario pequeno" onClick={() => passo(1)} aria-label="Próximo">→</button>
          <button className="botao secundario pequeno" onClick={() => setRef(new Date())}>Hoje</button>
        </div>
      </div>
      {cal.isLoading && <Carregando />}
      <Erro erro={cal.error} />
      {cal.data && (visao === 'mes' ? <Mes ref={ref} itens={cal.data} abre={setDetalhe} /> : visao === 'semana' ? <Semana ref={ref} itens={cal.data} abre={setDetalhe} /> : <Lista itens={cal.data} abre={setDetalhe} />)}

      <Modal titulo={detalhe?.titulo ?? ''} aberto={!!detalhe} fechar={() => setDetalhe(null)}>
        {detalhe && (
          <div className="pilha">
            <div className="linha"><span className={`selo ${COR[detalhe.tipo]}`}>{NOME[detalhe.tipo]}</span>{detalhe.turma ? <span className="selo">{detalhe.turma}</span> : <span className="selo">Escola toda</span>}</div>
            <div>{dataBR(detalhe.inicio)}{detalhe.fim !== detalhe.inicio && ` a ${dataBR(detalhe.fim)}`}</div>
            {detalhe.descricao && <p style={{whiteSpace: 'pre-wrap', margin: 0}}>{detalhe.descricao}</p>}
            {detalhe.autor && <div className="suave pequeno">{detalhe.autor}</div>}
            <Erro erro={remove.error} />
            {detalhe.editavel && (
              <div className="linha">
                <button className="botao secundario" onClick={() => edita(detalhe)}>Editar</button>
                <button className="botao secundario" disabled={remove.isPending} onClick={() => remove.mutate(detalhe.id)}>Excluir</button>
              </div>
            )}
          </div>
        )}
      </Modal>

      <Modal titulo={form?.id ? 'Editar evento' : 'Novo evento'} aberto={!!form} fechar={() => setForm(null)} largo>
        {form && (
          <form className="pilha" onSubmit={(e) => { e.preventDefault(); salva.mutate(form); }}>
            <label className="campo">Título<input required maxLength={200} value={form.titulo} onChange={(e) => setForm({...form, titulo: e.target.value})} /></label>
            <div className="form-grade">
              <label className="campo">Tipo
                <select value={form.tipo} onChange={(e) => setForm({...form, tipo: e.target.value as TipoEvento})}>
                  {tipos.map((t) => <option key={t} value={t}>{NOME[t]}</option>)}
                </select>
              </label>
              <label className="campo">Para
                <select value={form.turma_id} onChange={(e) => setForm({...form, turma_id: e.target.value})}>
                  {geral ? <option value="">Escola toda</option> : <option value="" disabled>Escolha a turma</option>}
                  {turmas.data?.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}
                </select>
              </label>
              <label className="campo">Início<input required type="date" value={form.inicio} onChange={(e) => setForm({...form, inicio: e.target.value})} /></label>
              <label className="campo">Fim (opcional)<input type="date" min={form.inicio} value={form.fim} onChange={(e) => setForm({...form, fim: e.target.value})} /></label>
            </div>
            <label className="campo">Detalhes (opcional)<textarea rows={3} maxLength={1000} value={form.descricao} onChange={(e) => setForm({...form, descricao: e.target.value})} /></label>
            {form.tipo === 'sem_aula' && <p className="suave pequeno" style={{margin: 0}}>A chamada fica bloqueada nessas datas e as famílias são avisadas.</p>}
            <Erro erro={salva.error} />
            <button className="botao" disabled={salva.isPending || (!geral && !form.turma_id)}>{form.id ? 'Salvar' : 'Criar'}</button>
          </form>
        )}
      </Modal>
      {geral && <Feriados aberto={feriados} fechar={() => setFeriados(false)} ano={ref.getFullYear()} />}
      <Assinatura aberto={assina} fechar={() => setAssina(false)} />
    </>
  );
}
