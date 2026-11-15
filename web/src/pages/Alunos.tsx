import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useDeferredValue, useState} from 'react';
import {useNavigate} from 'react-router';
import {Avatar, Carregando, Erro, Modal, Vazio} from '../components/ui';
import {api} from '../lib/api';
import {usePapel} from '../lib/auth';
import {dataBR, nomeExibicao} from '../lib/formato';
import type {Aluno, TurmaResumo} from '../lib/tipos';

const VAZIO = {nome: '', sobrenome: '', nome_social: '', data_nascimento: '', ra: '', turma_id: ''};

export default function Alunos() {
  const papel = usePapel();
  const nav = useNavigate();
  const qc = useQueryClient();
  const [busca, setBusca] = useState('');
  const [turma, setTurma] = useState('');
  const q = useDeferredValue(busca);
  const params = new URLSearchParams();
  if (q) params.set('q', q);
  if (turma) params.set('turma_id', turma);
  const alunos = useQuery({queryKey: ['alunos', params.toString()], queryFn: () => api<Aluno[]>(`/alunos?${params}`), placeholderData: (p) => p});
  const turmas = useQuery({queryKey: ['turmas'], queryFn: () => api<TurmaResumo[]>('/turmas')});
  const [aberto, setAberto] = useState(false);
  const [form, setForm] = useState(VAZIO);
  const criar = useMutation({
    mutationFn: () =>
      api<Aluno>('/alunos', {
        body: {...form, nome_social: form.nome_social || null, ra: form.ra || null, turma_id: form.turma_id || null},
      }),
    onSuccess: (a) => {
      qc.invalidateQueries({queryKey: ['alunos']});
      nav(`/alunos/${a.id}`);
    },
  });
  const set = (k: keyof typeof VAZIO) => (e: {target: {value: string}}) => setForm({...form, [k]: e.target.value});

  return (
    <>
      <div className="topo">
        <h1>Alunos</h1>
        {papel === 'admin' && <button className="botao" onClick={() => setAberto(true)}>+ Novo aluno</button>}
      </div>
      <div className="cartao">
        <div className="form-grade" style={{marginBottom: '1rem'}}>
          <label className="campo">
            Buscar
            <input type="search" placeholder="Nome ou RA" value={busca} onChange={(e) => setBusca(e.target.value)} />
          </label>
          <label className="campo">
            Turma
            <select value={turma} onChange={(e) => setTurma(e.target.value)}>
              <option value="">Todas</option>
              {turmas.data?.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}
            </select>
          </label>
        </div>
        {alunos.isLoading && <Carregando />}
        <Erro erro={alunos.error} />
        {alunos.data?.length === 0 && <Vazio>Nenhum aluno encontrado.</Vazio>}
        {!!alunos.data?.length && (
          <div className="tabela-rolagem">
            <table>
              <thead>
                <tr><th>Aluno</th><th>Turma</th><th className="so-desktop">Nascimento</th><th className="so-desktop">RA</th></tr>
              </thead>
              <tbody>
                {alunos.data.map((a) => (
                  <tr key={a.id} className="clicavel" onClick={() => nav(`/alunos/${a.id}`)}>
                    <td><div className="linha" style={{flexWrap: 'nowrap'}}><Avatar nome={nomeExibicao(a)} /> <a href={`/alunos/${a.id}`} onClick={(e) => e.preventDefault()}>{nomeExibicao(a)}</a></div></td>
                    <td>{a.turma?.nome ?? <span className="selo laranja">sem turma</span>}</td>
                    <td className="so-desktop suave">{dataBR(a.data_nascimento)}</td>
                    <td className="so-desktop suave">{a.ra}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="suave pequeno" style={{marginTop: '0.75rem'}}>{alunos.data.length} aluno(s)</p>
          </div>
        )}
      </div>
      <Modal titulo="Novo aluno" aberto={aberto} fechar={() => setAberto(false)}>
        <form
          className="pilha"
          onSubmit={(e) => {
            e.preventDefault();
            criar.mutate();
          }}>
          <div className="form-grade">
            <label className="campo">Nome<input required value={form.nome} onChange={set('nome')} /></label>
            <label className="campo">Sobrenome<input required value={form.sobrenome} onChange={set('sobrenome')} /></label>
            <label className="campo">Nome social <span className="dica">(opcional)</span><input value={form.nome_social} onChange={set('nome_social')} /></label>
            <label className="campo">Nascimento<input type="date" required value={form.data_nascimento} onChange={set('data_nascimento')} /></label>
            <label className="campo">RA / matrícula<input value={form.ra} onChange={set('ra')} /></label>
            <label className="campo">
              Turma
              <select value={form.turma_id} onChange={set('turma_id')}>
                <option value="">Sem turma</option>
                {turmas.data?.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}
              </select>
            </label>
          </div>
          <Erro erro={criar.error} />
          <button className="botao" disabled={criar.isPending}>Cadastrar</button>
        </form>
      </Modal>
    </>
  );
}
