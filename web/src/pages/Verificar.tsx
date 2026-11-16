import {useQuery} from '@tanstack/react-query';
import {useState} from 'react';
import {useNavigate, useParams} from 'react-router';
import {Carregando} from '../components/ui';
import {api} from '../lib/api';

type Resp = {valido: boolean; escola: string; emitido_em: string; aluno: string};

/** Conferência pública do código de um histórico escolar. Mostra o mínimo: escola, data e iniciais do aluno. */
export default function Verificar() {
  const {codigo} = useParams();
  const nav = useNavigate();
  const [digitado, setDigitado] = useState(codigo ?? '');
  const q = useQuery({queryKey: ['verificar', codigo], queryFn: () => api<Resp>(`/historico/verificar/${codigo}`), enabled: !!codigo, retry: false});
  return (
    <main className="conteudo" style={{maxWidth: 560, margin: '3rem auto'}}>
      <div className="marca" style={{marginBottom: '1rem'}}><img src="/icon.svg" alt="" /> Caderneta</div>
      <h1>Conferir histórico escolar</h1>
      <form className="linha" onSubmit={(e) => { e.preventDefault(); if (digitado.trim()) nav(`/verificar/${encodeURIComponent(digitado.trim())}`); }}>
        <input value={digitado} onChange={(e) => setDigitado(e.target.value)} placeholder="Código, ex.: A1B2-C3D4-E5F6" aria-label="Código de verificação" style={{flex: 1, marginTop: 0}} />
        <button className="botao">Conferir</button>
      </form>
      {codigo && q.isLoading && <Carregando />}
      {q.data && (
        <div className="cartao pilha" role="status" style={{marginTop: '1rem'}}>
          <span className="selo verde">Código válido</span>
          <div>Histórico escolar emitido por <strong>{q.data.escola}</strong> em {new Date(q.data.emitido_em).toLocaleDateString('pt-BR')} para o(a) aluno(a) <strong>{q.data.aluno}</strong>.</div>
          <p className="suave pequeno" style={{margin: 0}}>Confira se as iniciais coincidem com o documento em mãos. Por privacidade, nenhum outro dado é mostrado. Este código não substitui a assinatura e o carimbo da secretaria.</p>
        </div>
      )}
      {codigo && q.error && <div className="cartao" role="alert" style={{marginTop: '1rem'}}><span className="selo vermelho">Código não encontrado</span><p style={{marginBottom: 0}}>Confira o código impresso no rodapé do documento.</p></div>}
    </main>
  );
}
