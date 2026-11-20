import {useEffect, useState} from 'react';
import {Carregando, Erro, Vazio} from '../components/ui';
import {dataBR} from '../lib/formato';
import {type TipoNovidade, useNovidades, useVersaoVista} from '../lib/novidades';

const TIPO: Record<TipoNovidade, {rotulo: string; classe: string}> = {
  novo: {rotulo: 'Novo', classe: 'selo verde'},
  melhoria: {rotulo: 'Melhoria', classe: 'selo'},
  correcao: {rotulo: 'Correção', classe: 'selo laranja'},
  seguranca: {rotulo: 'Segurança', classe: 'selo vermelho'},
};

/** O que mudou em cada versão, só com o que interessa ao público de quem está vendo (equipe ou família). */
export default function Novidades() {
  const q = useNovidades();
  const {marcar} = useVersaoVista();
  const [filtro, setFiltro] = useState<TipoNovidade | ''>('');
  const atual = q.data?.versao_atual;
  useEffect(() => {
    if (atual) marcar(atual);
  }, [atual, marcar]);
  const versoes = (q.data?.versoes ?? [])
    .map((v) => ({...v, itens: v.itens.filter((i) => !filtro || i.tipo === filtro)}))
    .filter((v) => v.itens.length);
  return (
    <>
      <div className="topo">
        <div>
          <h1>Novidades</h1>
          <div className="suave">O que mudou em cada versão da Caderneta{atual ? ` · versão atual ${atual}` : ''}</div>
        </div>
        <select aria-label="Filtrar por tipo" style={{width: 'auto'}} value={filtro} onChange={(e) => setFiltro(e.target.value as TipoNovidade | '')}>
          <option value="">Todos os tipos</option>
          {Object.entries(TIPO).map(([k, t]) => (
            <option key={k} value={k}>{t.rotulo}</option>
          ))}
        </select>
      </div>
      {q.isLoading && <Carregando />}
      {q.error && <Erro erro={q.error} />}
      {q.data && !versoes.length && <Vazio>Nada deste tipo por enquanto.</Vazio>}
      <div className="pilha">
        {versoes.map((v) => (
          <section key={v.versao} className="cartao" aria-labelledby={`v-${v.versao}`}>
            <h2 id={`v-${v.versao}`} style={{margin: 0}}>{v.titulo}</h2>
            <div className="suave pequeno" style={{marginBottom: '0.5rem'}}>Versão {v.versao} · {dataBR(v.data)}</div>
            <ul className="lista-novidades">
              {v.itens.map((i, n) => (
                <li key={n}>
                  <span className={TIPO[i.tipo].classe}>{TIPO[i.tipo].rotulo}</span> {i.texto}
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </>
  );
}
