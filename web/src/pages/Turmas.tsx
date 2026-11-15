import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {Link} from 'react-router';
import {Carregando, Erro, Modal, Vazio} from '../components/ui';
import {api} from '../lib/api';
import {usePapel} from '../lib/auth';
import type {TurmaResumo} from '../lib/tipos';

export default function Turmas() {
  const papel = usePapel();
  const qc = useQueryClient();
  const turmas = useQuery({queryKey: ['turmas'], queryFn: () => api<TurmaResumo[]>('/turmas')});
  const [aberto, setAberto] = useState(false);
  const [form, setForm] = useState({nome: '', serie: '', turno: 'manhã'});
  const criar = useMutation({
    mutationFn: () => api('/turmas', {body: form}),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['turmas']});
      setAberto(false);
      setForm({nome: '', serie: '', turno: 'manhã'});
    },
  });

  return (
    <>
      <div className="topo">
        <h1>{papel === 'professor' ? 'Minhas turmas' : 'Turmas'}</h1>
        {papel === 'admin' && <button className="botao" onClick={() => setAberto(true)}>+ Nova turma</button>}
      </div>
      {turmas.isLoading && <Carregando />}
      <Erro erro={turmas.error} />
      {turmas.data?.length === 0 && <Vazio>Nenhuma turma no ano letivo atual.</Vazio>}
      <div className="grade">
        {turmas.data?.map((t) => {
          const profs = [...new Set(t.atribuicoes.map((a) => a.professor))];
          return (
            <Link key={t.id} to={`/turmas/${t.id}`} className="cartao" style={{color: 'inherit', textDecoration: 'none'}}>
              <div className="linha entre">
                <h2 style={{fontSize: '1.35rem', margin: 0}}>{t.nome}</h2>
                <span className="selo">{t.alunos} alunos</span>
              </div>
              <div className="suave pequeno">{t.serie} · {t.turno}</div>
              <div className="pequeno" style={{marginTop: '0.75rem'}}>
                {t.atribuicoes.length} disciplina(s) · {profs.length} professor(es)
              </div>
            </Link>
          );
        })}
      </div>
      <Modal titulo="Nova turma" aberto={aberto} fechar={() => setAberto(false)}>
        <form
          className="pilha"
          onSubmit={(e) => {
            e.preventDefault();
            criar.mutate();
          }}>
          <div className="form-grade">
            <label className="campo">Nome<input required placeholder="7º A" value={form.nome} onChange={(e) => setForm({...form, nome: e.target.value})} /></label>
            <label className="campo">Série<input required placeholder="7º ano" value={form.serie} onChange={(e) => setForm({...form, serie: e.target.value})} /></label>
            <label className="campo">
              Turno
              <select value={form.turno} onChange={(e) => setForm({...form, turno: e.target.value})}>
                <option>manhã</option>
                <option>tarde</option>
                <option>noite</option>
                <option>integral</option>
              </select>
            </label>
          </div>
          <Erro erro={criar.error} />
          <button className="botao" disabled={criar.isPending}>Criar turma</button>
        </form>
      </Modal>
    </>
  );
}
