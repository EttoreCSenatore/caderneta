import {NavLink, Outlet} from 'react-router';
import {useQuery, useQueryClient} from '@tanstack/react-query';
import {useEffect, useState} from 'react';
import {api} from '../lib/api';
import {useMe, usePapel, useSair, useTrocaPerfil} from '../lib/auth';
import {NOME_PAPEL} from '../lib/formato';
import {descartar, enviarFila, iniciarOffline, limparOffline, useOffline} from '../lib/offlineApp';
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
    {to: '/desligados', rotulo: 'Desligados', icone: 'equipe'},
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
    {to: '/desligados', rotulo: 'Desligados', icone: 'equipe'},
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
const PRIORIDADE_ESCOLA = ['/', '/turmas', '/provas', '/calendario', '/avisos', '/mensagens', '/autorizacoes', '/alunos', '/equipe', '/importar', '/virada', '/desligados', '/escola'];
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

type EventoInstalar = Event & {prompt: () => Promise<void>; userChoice: Promise<{outcome: string}>};
const lerDispensa = () => {
  try {
    return localStorage.getItem('caderneta-instalar') === 'nao';
  } catch {
    return false;
  }
};

/** Convite para instalar o app (Chrome/Edge/Android) ou instrução de "Adicionar à tela inicial" (iPhone). */
function InstalarApp() {
  const [evento, setEvento] = useState<EventoInstalar | null>(null);
  const [dispensado, setDispensado] = useState(lerDispensa);
  useEffect(() => {
    const pega = (e: Event) => {
      e.preventDefault();
      setEvento(e as EventoInstalar);
    };
    window.addEventListener('beforeinstallprompt', pega);
    return () => window.removeEventListener('beforeinstallprompt', pega);
  }, []);
  const instalado = window.matchMedia('(display-mode: standalone)').matches || (navigator as Navigator & {standalone?: boolean}).standalone === true;
  const ios = /iphone|ipad|ipod/i.test(navigator.userAgent);
  if (instalado || dispensado || (!evento && !ios)) return null;
  const dispensa = () => {
    setDispensado(true);
    try {
      localStorage.setItem('caderneta-instalar', 'nao');
    } catch {
      /* sem armazenamento: o convite volta na próxima visita */
    }
  };
  return (
    <div className="aviso" role="region" aria-label="Instalar o app" style={{marginBottom: '1rem', background: 'var(--azul-claro)', border: '1px solid var(--borda)'}}>
      <div style={{flex: 1}}>
        <strong>Instale a Caderneta no celular.</strong>{' '}
        {evento ? 'Abre como um app, direto da tela inicial.' : 'No Safari, toque em Compartilhar e depois em “Adicionar à Tela de Início”.'}
      </div>
      {evento && (
        <button
          className="botao pequeno"
          onClick={() => {
            void evento.prompt();
            setEvento(null);
          }}>
          Instalar
        </button>
      )}
      <button className="botao secundario pequeno" onClick={dispensa}>Agora não</button>
    </div>
  );
}

function FaixaOffline() {
  const o = useOffline();
  const qc = useQueryClient();
  if (!o.ativo) return null;
  const pendentes = o.fila.filter((f) => !f.erro);
  const problemas = o.fila.filter((f) => f.erro);
  const vencendo = o.diasRestantes !== null && o.diasRestantes <= 2 && o.fila.length > 0;
  if (o.online && !o.fila.length) return null;
  return (
    <div className="pilha" style={{marginBottom: '1rem'}} role="status">
      {!o.online && (
        <div className="aviso atencao">
          Sem conexão. O que você lançar fica guardado no aparelho (cifrado) e é enviado quando a internet voltar.
        </div>
      )}
      {pendentes.length > 0 && (
        <div className="aviso atencao">
          <div style={{flex: 1}}>{pendentes.length} alteração(ões) aguardando envio.</div>
          {o.online && (
            <button className="botao pequeno" disabled={o.enviando} onClick={() => void enviarFila(qc)}>
              {o.enviando ? 'Enviando…' : 'Enviar agora'}
            </button>
          )}
        </div>
      )}
      {vencendo && (
        <div className="aviso erro">
          Conecte-se à internet: em {o.diasRestantes} dia(s) os dados deste aparelho serão apagados, inclusive o que ainda não foi enviado.
        </div>
      )}
      {problemas.map((f) => (
        <div key={f.id} className="aviso erro">
          <div style={{flex: 1}}>
            <strong>{f.rotulo}</strong> não foi aceito: {f.erro}
          </div>
          <button className="botao secundario pequeno" onClick={() => void descartar(f.id)}>Descartar</button>
        </div>
      ))}
      <div>
        <button
          className="botao secundario pequeno"
          onClick={() => {
            if (!o.fila.length || confirm('Há alterações ainda não enviadas. Apagar mesmo assim os dados offline deste aparelho?')) void limparOffline();
          }}>
          Apagar dados offline deste aparelho
        </button>
      </div>
    </div>
  );
}

export function Layout() {
  const {data: me} = useMe();
  const papel = usePapel();
  const sair = useSair();
  const qc = useQueryClient();
  const usuarioId = me?.usuario.id;
  useEffect(() => {
    if (me && papel) void iniciarOffline(me, papel === 'professor', qc);
  }, [usuarioId, papel, qc]);
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
              <NavLink to="/conta" style={{fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', display: 'block', color: 'inherit'}} title="Minha conta">{me.usuario.nome}</NavLink>
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
          <div className="so-movel linha" style={{marginBottom: '0.75rem', justifyContent: 'space-between'}}>
            <TrocaPerfil />
            <NavLink to="/conta" className="botao secundario pequeno">Minha conta</NavLink>
          </div>
          <InstalarApp />
          <FaixaOffline />
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

