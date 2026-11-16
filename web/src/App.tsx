import {useQuery} from '@tanstack/react-query';
import {lazy, Suspense} from 'react';
import {Navigate, Route, Routes, useLocation} from 'react-router';
import {Layout} from './components/Layout';
import {Carregando, Erro} from './components/ui';
import {useMe} from './lib/auth';
import type {LegalPendente} from './lib/tipos';
import {Convite} from './pages/Convite';
import {Configurar2fa, EscolherPerfil} from './pages/Etapas';
import {Entrar, Esqueci, Redefinir} from './pages/Entrar';
import {Inicio} from './pages/Inicio';
import Aceitar from './pages/Aceitar';
import {api, ApiError} from './lib/api';

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
const Desligados = lazy(() => import('./pages/Desligados'));
const MeusDados = lazy(() => import('./pages/MeusDados'));
const PedidosTitulares = lazy(() => import('./pages/PedidosTitulares'));
const Legal = lazy(() => import('./pages/Legal'));
const Conta = lazy(() => import('./pages/Conta'));
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
  return <ConfirmaTextos />;
}

/** Antes do app: confirmar a política de privacidade e os termos (de novo, se o texto mudou de versão). */
function ConfirmaTextos() {
  const local = useLocation();
  const q = useQuery({
    queryKey: ['legal-pendentes'],
    queryFn: async () => {
      try {
        return await api<LegalPendente[]>('/legal/pendentes');
      } catch (e) {
        if (e instanceof ApiError && e.status === 0) return []; // sem internet (modo offline): confirma na próxima vez
        throw e;
      }
    },
  });
  if (q.isLoading) return <Carregando />;
  if (q.data?.length) return local.pathname === '/aceitar' ? <Aceitar pendentes={q.data} /> : <Navigate to="/aceitar" replace />;
  if (local.pathname === '/aceitar') return <Navigate to="/" replace />;
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
        <Route path="/privacidade" element={<Legal />} />
        <Route path="/termos" element={<Legal />} />
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
          <Route path="desligados" element={<Desligados />} />
          <Route path="diario/:id" element={<Diario />} />
          <Route path="aceitar" element={null} />
          <Route path="conta" element={<Conta />} />
          <Route path="meus-dados" element={<MeusDados />} />
          <Route path="pedidos-titulares" element={<PedidosTitulares />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
