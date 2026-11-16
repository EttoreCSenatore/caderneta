import {NavLink, Outlet} from 'react-router';
import {useQuery} from '@tanstack/react-query';
import {api} from '../lib/api';
import {useMe, usePapel, useSair, useTrocaPerfil} from '../lib/auth';
import {NOME_PAPEL} from '../lib/formato';
import type {Papel} from '../lib/tipos';
import {Icone} from './icones';
import {Avatar} from './ui';

type Item = {to: string; rotulo: string; icone: keyof typeof Icone};

const MENU: Record<Papel, Item[]> = {
  admin: [
    {to: '/', rotulo: 'Início', icone: 'inicio'},
    {to: '/notificacoes', rotulo: 'Notificações', icone: 'notificacoes'},
    {to: '/calendario', rotulo: 'Calendário', icone: 'calendario'},
    {to: '/avisos', rotulo: 'Avisos', icone: 'avisos'},
    {to: '/autorizacoes', rotulo: 'Autorizações', icone: 'autorizacoes'},
    {to: '/mensagens', rotulo: 'Mensagens', icone: 'mensagens'},
    {to: '/turmas', rotulo: 'Turmas', icone: 'turmas'},
    {to: '/provas', rotulo: 'Provas', icone: 'provas'},
    {to: '/alunos', rotulo: 'Alunos', icone: 'alunos'},
    {to: '/equipe', rotulo: 'Equipe', icone: 'equipe'},
    {to: '/importar', rotulo: 'Importar', icone: 'importar'},
    {to: '/virada', rotulo: 'Virada de ano', icone: 'turmas'},
    {to: '/escola', rotulo: 'Escola', icone: 'escola'},
  ],
  coordenacao: [
    {to: '/', rotulo: 'Início', icone: 'inicio'},
    {to: '/notificacoes', rotulo: 'Notificações', icone: 'notificacoes'},
    {to: '/calendario', rotulo: 'Calendário', icone: 'calendario'},
    {to: '/avisos', rotulo: 'Avisos', icone: 'avisos'},
    {to: '/autorizacoes', rotulo: 'Autorizações', icone: 'autorizacoes'},
    {to: '/mensagens', rotulo: 'Mensagens', icone: 'mensagens'},
    {to: '/turmas', rotulo: 'Turmas', icone: 'turmas'},
    {to: '/provas', rotulo: 'Provas', icone: 'provas'},
    {to: '/alunos', rotulo: 'Alunos', icone: 'alunos'},
    {to: '/equipe', rotulo: 'Equipe', icone: 'equipe'},
    {to: '/virada', rotulo: 'Virada de ano', icone: 'turmas'},
    {to: '/escola', rotulo: 'Escola', icone: 'escola'},
  ],
  professor: [
    {to: '/', rotulo: 'Início', icone: 'inicio'},
    {to: '/notificacoes', rotulo: 'Notificações', icone: 'notificacoes'},
    {to: '/calendario', rotulo: 'Calendário', icone: 'calendario'},
    {to: '/avisos', rotulo: 'Avisos', icone: 'avisos'},
    {to: '/autorizacoes', rotulo: 'Autorizações', icone: 'autorizacoes'},
    {to: '/mensagens', rotulo: 'Mensagens', icone: 'mensagens'},
    {to: '/turmas', rotulo: 'Minhas turmas', icone: 'turmas'},
    {to: '/provas', rotulo: 'Provas', icone: 'provas'},
    {to: '/alunos', rotulo: 'Alunos', icone: 'alunos'},
  ],
  responsavel: [
    {to: '/', rotulo: 'Início', icone: 'inicio'},
    {to: '/notificacoes', rotulo: 'Notificações', icone: 'notificacoes'},
    {to: '/calendario', rotulo: 'Calendário', icone: 'calendario'},
    {to: '/avisos', rotulo: 'Avisos', icone: 'avisos'},
    {to: '/autorizacoes', rotulo: 'Autorizações', icone: 'autorizacoes'},
    {to: '/mensagens', rotulo: 'Mensagens', icone: 'mensagens'},
    {to: '/provas', rotulo: 'Materiais', icone: 'provas'},
  ],
  aluno: [
    {to: '/', rotulo: 'Início', icone: 'inicio'},
    {to: '/notificacoes', rotulo: 'Notificações', icone: 'notificacoes'},
    {to: '/calendario', rotulo: 'Calendário', icone: 'calendario'},
    {to: '/avisos', rotulo: 'Avisos', icone: 'avisos'},
    {to: '/provas', rotulo: 'Materiais', icone: 'provas'},
  ],
};

// Ordem de importância no menu do celular (cabem cinco itens)
const PRIORIDADE_ESCOLA = ['/', '/turmas', '/provas', '/calendario', '/avisos', '/mensagens', '/autorizacoes', '/alunos', '/equipe', '/importar', '/virada', '/escola'];
const PRIORIDADE_FAMILIA = ['/', '/calendario', '/avisos', '/autorizacoes', '/mensagens', '/provas'];

function TrocaPerfil() {
  const {data: me} = useMe();
  const troca = useTrocaPerfil();
  if (!me || me.perfis.length < 2) return null;
  return (
    <select
      aria-label="Perfil ativo"
      value={me.perfil_ativo ?? ''}
      onChange={(e) => troca.mutate(e.target.value)}
      style={{marginTop: 0}}>
      {me.perfis.map((p) => (
        <option key={p.id} value={p.id}>
          {NOME_PAPEL[p.papel]} · {p.escola}
        </option>
      ))}
    </select>
  );
}

export function Layout() {
  const {data: me} = useMe();
  const papel = usePapel();
  const sair = useSair();
  if (!me || !papel) return null;
  const perfil = me.perfis.find((p) => p.id === me.perfil_ativo)!;
  const itens = MENU[papel];
  const ordem = papel === 'responsavel' || papel === 'aluno' ? PRIORIDADE_FAMILIA : PRIORIDADE_ESCOLA;
  const inferior = itens
    .filter((i) => i.to !== '/notificacoes')
    .sort((x, y) => ordem.indexOf(x.to) - ordem.indexOf(y.to))
    .slice(0, 5);
  const pendentes = useQuery({queryKey: ['avisos-pendentes'], queryFn: () => api<{nao_lidos: number}>('/avisos-pendentes'), refetchInterval: 60000});
  const naoLidos = pendentes.data?.nao_lidos ?? 0;
  const msgs = useQuery({queryKey: ['mensagens-pendentes'], queryFn: () => api<{nao_lidas: number}>('/mensagens-pendentes'), refetchInterval: 30000});
  const naoLidas = msgs.data?.nao_lidas ?? 0;
  const notifs = useQuery({queryKey: ['notificacoes-contagem'], queryFn: () => api<{nao_lidas: number}>('/notificacoes/contagem'), refetchInterval: 30000});
  const novas = notifs.data?.nao_lidas ?? 0;
  return (
    <div className="app">
      <aside className="lateral">
        <div className="marca">
          <img src="/icon.svg" alt="" /> Caderneta
        </div>
        <nav className="nav" aria-label="Menu principal">
          {itens.map((i) => (
            <NavLink key={i.to} to={i.to} end={i.to === '/'}>
              {Icone[i.icone]} {i.rotulo}
              {i.to === '/notificacoes' && novas > 0 && <span className="selo vermelho" aria-label={`${novas} notificações novas`}>{novas}</span>}
              {i.to === '/mensagens' && naoLidas > 0 && <span className="selo vermelho" aria-label={`${naoLidas} conversas novas`}>{naoLidas}</span>}
              {i.to === '/avisos' && naoLidos > 0 && <span className="selo vermelho" aria-label={`${naoLidos} não lidos`}>{naoLidos}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="rodape pilha">
          <div className="linha" style={{flexWrap: 'nowrap'}}>
            <Avatar nome={me.usuario.nome} />
            <div style={{minWidth: 0}}>
              <div style={{fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis'}}>{me.usuario.nome}</div>
              <div className="suave pequeno">{NOME_PAPEL[papel]}</div>
            </div>
          </div>
          <div className="suave pequeno">{perfil.escola}</div>
          <TrocaPerfil />
          <button className="botao secundario pequeno largo" onClick={() => sair.mutate()}>
            {Icone.sair} Sair
          </button>
        </div>
      </aside>
      <div>
        <header className="barra-movel">
          <div className="marca" style={{padding: 0}}>
            <img src="/icon.svg" alt="" /> Caderneta
          </div>
          <NavLink to="/notificacoes" className="botao secundario pequeno" aria-label="Notificações" style={{marginLeft: 'auto', marginRight: '0.5rem', position: 'relative'}}>
            {Icone.notificacoes}
            {novas > 0 && <span className="selo vermelho" style={{position: 'absolute', top: '-0.5rem', right: '-0.5rem'}}>{novas}</span>}
          </NavLink>
          <button className="botao secundario pequeno" onClick={() => sair.mutate()} aria-label="Sair">
            {Icone.sair}
          </button>
        </header>
        <main className="conteudo">
          <div className="so-movel" style={{marginBottom: '0.75rem'}}>
            <TrocaPerfil />
          </div>
          <Outlet />
        </main>
        {itens.length > 1 && (
          <nav className="inferior" aria-label="Menu">
            {inferior.map((i) => (
              <NavLink key={i.to} to={i.to} end={i.to === '/'}>
                {Icone[i.icone]}
                {i.rotulo.replace('Minhas turmas', 'Turmas')}
              </NavLink>
            ))}
          </nav>
        )}
      </div>
    </div>
  );
}

