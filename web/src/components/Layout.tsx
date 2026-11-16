import {NavLink, Outlet} from 'react-router';
import {useMe, usePapel, useSair, useTrocaPerfil} from '../lib/auth';
import {NOME_PAPEL} from '../lib/formato';
import type {Papel} from '../lib/tipos';
import {Icone} from './icones';
import {Avatar} from './ui';

type Item = {to: string; rotulo: string; icone: keyof typeof Icone};

const MENU: Record<Papel, Item[]> = {
  admin: [
    {to: '/', rotulo: 'Início', icone: 'inicio'},
    {to: '/turmas', rotulo: 'Turmas', icone: 'turmas'},
    {to: '/alunos', rotulo: 'Alunos', icone: 'alunos'},
    {to: '/equipe', rotulo: 'Equipe', icone: 'equipe'},
    {to: '/importar', rotulo: 'Importar', icone: 'importar'},
    {to: '/escola', rotulo: 'Escola', icone: 'escola'},
  ],
  coordenacao: [
    {to: '/', rotulo: 'Início', icone: 'inicio'},
    {to: '/turmas', rotulo: 'Turmas', icone: 'turmas'},
    {to: '/alunos', rotulo: 'Alunos', icone: 'alunos'},
    {to: '/equipe', rotulo: 'Equipe', icone: 'equipe'},
    {to: '/escola', rotulo: 'Escola', icone: 'escola'},
  ],
  professor: [
    {to: '/', rotulo: 'Início', icone: 'inicio'},
    {to: '/turmas', rotulo: 'Minhas turmas', icone: 'turmas'},
    {to: '/alunos', rotulo: 'Alunos', icone: 'alunos'},
  ],
  responsavel: [{to: '/', rotulo: 'Início', icone: 'inicio'}],
  aluno: [{to: '/', rotulo: 'Início', icone: 'inicio'}],
};

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
            {itens.slice(0, 5).map((i) => (
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

