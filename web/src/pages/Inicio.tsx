import {useQuery} from '@tanstack/react-query';
import {Link} from 'react-router';
import {Carregando, Erro, Vazio, Avatar} from '../components/ui';
import {api} from '../lib/api';
import {comCache} from '../lib/offlineApp';
import {useMe, usePapel} from '../lib/auth';
import {dataBR, idade, nomeExibicao, periodoAtual} from '../lib/formato';
import type {Aluno, Escola, TurmaResumo} from '../lib/tipos';

function Periodos({escola}: {escola: Escola}) {
  const ano = escola.ano_atual;
  if (!ano) return <div className="aviso atencao">Nenhum ano letivo aberto. {''}<Link to="/escola">Criar ano letivo</Link></div>;
  const atual = periodoAtual(ano.periodos);
  return (
    <div className="cartao">
      <div className="linha entre">
        <h2>Ano letivo {ano.ano}</h2>
        <span className="suave pequeno">{dataBR(ano.inicio)} a {dataBR(ano.fim)}</span>
      </div>
      <div className="linha-tempo">
        {ano.periodos.map((p) => (
          <div key={p.id} className={p.id === atual?.id ? 'atual' : ''}>
            <strong>{p.nome}</strong>
            <div className="suave pequeno">{dataBR(p.inicio)} – {dataBR(p.fim)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function InicioEquipe({escola}: {escola: Escola}) {
  const r = escola.resumo!;
  const kpis: [number, string, string][] = [
    [r.alunos, 'alunos ativos', '/alunos'],
    [r.turmas, 'turmas', '/turmas'],
    [r.professores, 'professores', '/equipe'],
    [r.convites_pendentes, 'convites pendentes', '/equipe'],
  ];
  return (
    <>
      <div className="kpis">
        {kpis.map(([v, rot, to]) => (
          <Link key={rot} to={to} className="cartao kpi" style={{color: 'inherit', textDecoration: 'none'}}>
            <div className="valor">{v}</div>
            <div className="rotulo">{rot}</div>
          </Link>
        ))}
      </div>
      <Periodos escola={escola} />
    </>
  );
}

function InicioProfessor() {
  const turmas = useQuery({queryKey: ['turmas'], queryFn: () => comCache('turmas', () => api<TurmaResumo[]>('/turmas'))});
  if (turmas.isLoading) return <Carregando />;
  if (!turmas.data?.length) return <Vazio>Você ainda não tem turmas atribuídas. A escola faz isso em Turmas → Professores.</Vazio>;
  return (
    <>
      <h2>Minhas turmas</h2>
      <div className="grade">
        {turmas.data.map((t) => (
          <div key={t.id} className="cartao">
            <div className="linha entre">
              <Link to={`/turmas/${t.id}`}><h3 style={{fontSize: '1.3rem', margin: 0}}>{t.nome}</h3></Link>
              <span className="selo">{t.alunos} alunos</span>
            </div>
            <div className="suave pequeno">{t.serie} · {t.turno}</div>
            <div className="pilha" style={{marginTop: '0.75rem'}}>
              {t.atribuicoes.map((a) => (
                <div key={a.id} className="linha entre">
                  <strong>{a.disciplina}</strong>
                  <span className="linha" style={{gap: '0.35rem'}}>
                    <Link className="botao pequeno" to={`/diario/${a.id}`}>Notas</Link>
                    <Link className="botao secundario pequeno" to={`/diario/${a.id}?aba=chamada`}>Chamada</Link>
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

function InicioFamilia({proprio}: {proprio: boolean}) {
  const alunos = useQuery({queryKey: ['alunos', ''], queryFn: () => api<Aluno[]>('/alunos')});
  if (alunos.isLoading) return <Carregando />;
  if (!alunos.data?.length) return <Vazio>Nenhum aluno vinculado à sua conta. Fale com a secretaria da escola.</Vazio>;
  return (
    <>
      <h2>{proprio ? 'Meus dados' : alunos.data.length > 1 ? 'Meus filhos' : 'Meu filho(a)'}</h2>
      <div className="grade">
        {alunos.data.map((a) => (
          <Link key={a.id} to={`/alunos/${a.id}`} className="cartao" style={{color: 'inherit', textDecoration: 'none'}}>
            <div className="linha" style={{flexWrap: 'nowrap'}}>
              <Avatar nome={nomeExibicao(a)} grande />
              <div>
                <h3 style={{fontSize: '1.15rem', margin: 0}}>{nomeExibicao(a)}</h3>
                <div className="suave">{a.turma ? `${a.turma.nome} · ${a.turma.serie}` : 'Sem turma'}</div>
                <div className="suave pequeno">{idade(a.data_nascimento)} anos · RA {a.ra ?? '—'}</div>
              </div>
            </div>
          </Link>
        ))}
      </div>
      <div className="cartao" style={{marginTop: '1rem'}}>
        <h3>Em breve por aqui</h3>
        <p className="suave" style={{margin: 0}}>Avisos da escola e o calendário aparecerão nesta tela. Notas e faltas já estão no boletim de cada aluno.</p>
      </div>
    </>
  );
}

export function Inicio() {
  const {data: me} = useMe();
  const papel = usePapel();
  const escola = useQuery({queryKey: ['escola'], queryFn: () => comCache('escola', () => api<Escola>('/escola'))});
  if (escola.isLoading) return <Carregando />;
  if (escola.error) return <Erro erro={escola.error} />;
  const e = escola.data!;
  return (
    <>
      <div className="topo">
        <div>
          <h1>Olá, {me?.usuario.nome.split(' ')[0]}</h1>
          <div className="suave">{e.nome}</div>
        </div>
      </div>
      {papel === 'admin' || papel === 'coordenacao' ? (
        <InicioEquipe escola={e} />
      ) : papel === 'professor' ? (
        <InicioProfessor />
      ) : (
        <InicioFamilia proprio={papel === 'aluno'} />
      )}
    </>
  );
}
