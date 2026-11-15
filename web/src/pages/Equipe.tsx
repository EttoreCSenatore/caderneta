import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {Avatar, Carregando, Erro, LinkConvite, Modal, Vazio} from '../components/ui';
import {api} from '../lib/api';
import {usePapel} from '../lib/auth';
import {dataBR, NOME_PAPEL} from '../lib/formato';
import type {ConvitePendente, MembroEquipe, Papel} from '../lib/tipos';

export default function Equipe() {
  const papel = usePapel();
  const qc = useQueryClient();
  const equipe = useQuery({queryKey: ['equipe'], queryFn: () => api<MembroEquipe[]>('/equipe')});
  const convites = useQuery({queryKey: ['convites'], queryFn: () => api<ConvitePendente[]>('/convites')});
  const [aberto, setAberto] = useState(false);
  const [f, setF] = useState({nome: '', email: '', papel: 'professor' as Papel});
  const [link, setLink] = useState<string | null>(null);
  const convidar = useMutation({
    mutationFn: () => api<{link: string}>('/convites', {body: f}),
    onSuccess: (r) => {
      setLink(r.link);
      setAberto(false);
      setF({nome: '', email: '', papel: 'professor'});
      qc.invalidateQueries({queryKey: ['convites']});
    },
  });
  const revogar = useMutation({
    mutationFn: (id: string) => api(`/convites/${id}`, {method: 'DELETE'}),
    onSuccess: () => qc.invalidateQueries({queryKey: ['convites']}),
  });
  const ativa = useMutation({
    mutationFn: ({id, ativo}: {id: string; ativo: boolean}) => api(`/equipe/${id}`, {method: 'PATCH', body: {ativo}}),
    onSuccess: () => qc.invalidateQueries({queryKey: ['equipe']}),
  });
  const admin = papel === 'admin';
  const pendEquipe = convites.data?.filter((c) => c.papel !== 'responsavel' && c.papel !== 'aluno') ?? [];
  const pendFamilia = (convites.data?.length ?? 0) - pendEquipe.length;
  return (
    <>
      <div className="topo">
        <h1>Equipe</h1>
        {admin && <button className="botao" onClick={() => setAberto(true)}>+ Convidar</button>}
      </div>
      {link && <div style={{marginBottom: '1rem'}}><LinkConvite link={link} /></div>}
      <div className="cartao lista">
        {equipe.isLoading && <Carregando />}
        <Erro erro={equipe.error} />
        {equipe.data?.map((m) => (
          <div key={m.perfil_id} className="item">
            <Avatar nome={m.nome} />
            <div style={{flex: 1, minWidth: 0}}>
              <strong>{m.nome}</strong>
              <div className="suave pequeno" style={{overflow: 'hidden', textOverflow: 'ellipsis'}}>{m.email}</div>
            </div>
            <span className="selo">{NOME_PAPEL[m.papel]}</span>
            {m.totp_ativo && <span className="selo verde so-desktop">2FA</span>}
            {!m.ativo && <span className="selo vermelho">Inativo</span>}
            {admin && (
              <button className="botao secundario pequeno so-desktop" onClick={() => ativa.mutate({id: m.perfil_id, ativo: !m.ativo})}>
                {m.ativo ? 'Desativar' : 'Reativar'}
              </button>
            )}
          </div>
        ))}
      </div>
      <Erro erro={ativa.error} />
      <h2 style={{marginTop: '1.5rem'}}>Convites pendentes</h2>
      <div className="cartao lista">
        {pendEquipe.length === 0 && <Vazio>Nenhum convite da equipe pendente.</Vazio>}
        {pendEquipe.map((c) => (
          <div key={c.id} className="item">
            <div style={{flex: 1}}>
              <strong>{c.nome}</strong>
              <div className="suave pequeno">{c.email} · enviado em {dataBR(c.criado_em)}</div>
            </div>
            <span className="selo">{NOME_PAPEL[c.papel]}</span>
            {c.expirado && <span className="selo vermelho">Expirado</span>}
            {admin && <button className="botao perigo pequeno" onClick={() => revogar.mutate(c.id)}>Cancelar</button>}
          </div>
        ))}
      </div>
      {pendFamilia > 0 && <p className="suave pequeno">Mais {pendFamilia} convite(s) de famílias aguardando resposta (veja na ficha de cada aluno).</p>}
      <Modal titulo="Convidar para a equipe" aberto={aberto} fechar={() => setAberto(false)}>
        <form className="pilha" onSubmit={(e) => { e.preventDefault(); convidar.mutate(); }}>
          <label className="campo">Nome<input required value={f.nome} onChange={(e) => setF({...f, nome: e.target.value})} /></label>
          <label className="campo">E-mail<input type="email" required value={f.email} onChange={(e) => setF({...f, email: e.target.value})} /></label>
          <label className="campo">
            Função
            <select value={f.papel} onChange={(e) => setF({...f, papel: e.target.value as Papel})}>
              <option value="professor">Professor(a)</option>
              <option value="coordenacao">Coordenação</option>
              <option value="admin">Direção / Secretaria</option>
            </select>
          </label>
          <p className="suave pequeno">A pessoa recebe um link por e-mail, válido por 7 dias e de uso único. Direção e coordenação configuram a verificação em duas etapas no primeiro acesso.</p>
          <Erro erro={convidar.error} />
          <button className="botao" disabled={convidar.isPending}>Enviar convite</button>
        </form>
      </Modal>
    </>
  );
}
