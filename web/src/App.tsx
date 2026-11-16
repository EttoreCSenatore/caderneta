import {lazy, Suspense} from 'react';
import {Navigate, Route, Routes, useLocation} from 'react-router';
import {Layout} from './components/Layout';
import {Carregando, Erro} from './components/ui';
import {useMe} from './lib/auth';
import {Convite} from './pages/Convite';
import {Configurar2fa, EscolherPerfil} from './pages/Etapas';
import {Entrar, Esqueci, Redefinir} from './pages/Entrar';
import {Inicio} from './pages/Inicio';

const Turmas = lazy(() => import('./pages/Turmas'));
const Turma = lazy(() => import('./pages/Turma'));
const Alunos = lazy(() => import('./pages/Alunos'));
const Aluno = lazy(() => import('./pages/Aluno'));
const Equipe = lazy(() => import('./pages/Equipe'));
const Importar = lazy(() => import('./pages/Importar'));
const EscolaPage = lazy(() => import('./pages/Escola'));
const Avisos = lazy(() => import('./pages/Avisos'));
const Autorizacoes = lazy(() => import('./pages/Autorizacoes'));
const Mensagens = lazy(() => import('./pages/Mensagens'));
const Notificacoes = lazy(() => import('./pages/Notificacoes'));
const Calendario = lazy(() => import('./pages/Calendario'));
const Provas = lazy(() => import('./pages/Provas'));
const Virada = lazy(() => import('./pages/Virada'));
const Verificar = lazy(() => import('./pages/Verificar'));
const Diario = lazy(() => import('./pages/Diario'));

/** Guarda: leva o usuário à etapa pendente (entrar, código, 2FA, perfil) antes do app. */
function Protegido() {
  const {data: me, isLoading, error} = useMe();
  const local = useLocation();
  if (isLoading) return <Carregando />;
  if (error) return <div className="conteudo"><Erro erro={error} /></div>;
  if (!me || me.status === 'codigo') return <Navigate to="/entrar" replace state={{de: local.pathname}} />;
  if (me.status === 'configurar_2fa') return <Navigate to="/configurar-2fa" replace />;
  if (!me.perfil_ativo) return <Navigate to="/perfil" replace />;
  return <Layout />;
}

export function App() {
  return (
    <Suspense fallback={<Carregando />}>
      <Routes>
        <Route path="/entrar" element={<Entrar />} />
        <Route path="/esqueci-senha" element={<Esqueci />} />
        <Route path="/redefinir-senha" element={<Redefinir />} />
        <Route path="/convite/:token" element={<Convite />} />
        <Route path="/verificar" element={<Verificar />} />
        <Route path="/verificar/:codigo" element={<Verificar />} />
        <Route path="/configurar-2fa" element={<Configurar2fa />} />
        <Route path="/perfil" element={<EscolherPerfil />} />
        <Route element={<Protegido />}>
          <Route index element={<Inicio />} />
          <Route path="turmas" element={<Turmas />} />
          <Route path="turmas/:id" element={<Turma />} />
          <Route path="alunos" element={<Alunos />} />
          <Route path="alunos/:id" element={<Aluno />} />
          <Route path="equipe" element={<Equipe />} />
          <Route path="importar" element={<Importar />} />
          <Route path="escola" element={<EscolaPage />} />
          <Route path="avisos" element={<Avisos />} />
          <Route path="autorizacoes" element={<Autorizacoes />} />
          <Route path="mensagens" element={<Mensagens />} />
          <Route path="notificacoes" element={<Notificacoes />} />
          <Route path="calendario" element={<Calendario />} />
          <Route path="provas" element={<Provas />} />
          <Route path="virada" element={<Virada />} />
          <Route path="diario/:id" element={<Diario />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
