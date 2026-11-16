export type Papel = 'admin' | 'coordenacao' | 'professor' | 'responsavel' | 'aluno';

export type Perfil = {id: string; papel: Papel; escola_id: string; escola: string};

export type Me = {
  status: 'ok' | 'codigo' | 'configurar_2fa';
  usuario: {id: string; nome: string; email: string; totp_ativo: boolean};
  perfis: Perfil[];
  perfil_ativo: string | null;
};

export type Periodo = {id: string; numero: number; nome: string; inicio: string; fim: string; fechado: boolean};
export type AnoLetivo = {id: string; ano: number; tipo_periodo: string; inicio: string; fim: string; aberto: boolean; periodos: Periodo[]};

export type Escola = {
  id: string;
  nome: string;
  cidade: string | null;
  uf: string | null;
  ano_atual: AnoLetivo | null;
  resumo?: {alunos: number; turmas: number; professores: number; convites_pendentes: number};
};

export type Atribuicao = {id: string; disciplina_id: string; disciplina: string; professor_id: string; professor: string};
export type TurmaResumo = {id: string; nome: string; serie: string; turno: string; alunos: number; atribuicoes: Atribuicao[]};
export type AlunoLinha = {id: string; nome: string; sobrenome: string; nome_social: string | null; ra: string | null};
export type Turma = Omit<TurmaResumo, 'alunos'> & {alunos: AlunoLinha[]};

export type Aluno = AlunoLinha & {
  data_nascimento: string;
  situacao: string;
  turma: {id: string; nome: string; serie: string} | null;
  cpf?: string | null;
  historico?: {ano_letivo_id: string; turma: string; serie: string; situacao: string}[];
  responsaveis?: Vinculo[];
  tem_alerta_saude: boolean;
  aluno_tem_conta: boolean;
};

export type Vinculo = {
  id: string;
  nome: string;
  tipo: string;
  telefone: string | null;
  email: string | null;
  pode_buscar: boolean;
  recebe_avisos: boolean;
  emergencia: boolean;
  restrito: boolean;
  tem_conta: boolean;
  convite_pendente: boolean;
};

export type Saude = {
  alergias?: string;
  medicamentos?: string;
  condicoes?: string;
  restricoes_alimentares?: string;
  necessidades_especificas?: string;
  plano_saude?: string;
  observacoes?: string;
  alerta: string;
  atualizado_em?: string | null;
};

export type Disciplina = {id: string; nome: string; ativo: boolean};
export type MembroEquipe = {perfil_id: string; usuario_id: string; nome: string; email: string; papel: Papel; ativo: boolean; totp_ativo: boolean};
export type ConvitePendente = {id: string; email: string; nome: string; papel: Papel; criado_em: string; expirado: boolean};

// --- M2 ---
export type StatusNota = 'normal' | 'dispensada' | 'falta_justificada';
export type StatusPresenca = 'presente' | 'falta' | 'justificada' | 'atraso';

export type Avaliacao = {
  id: string;
  periodo_id: string;
  nome: string;
  tipo: string;
  data: string | null;
  peso: number;
  nota_maxima: number;
  recuperacao: boolean;
  publicada: boolean;
};

export type MediaAluno = {media: number | null; media_antes_recuperacao: number | null; recuperacao_aplicada: boolean; pendentes: number};

export type Diario = {
  atribuicao: {id: string; disciplina: string; professor: string; turma: {id: string; nome: string; serie: string}};
  pode_editar: boolean;
  periodos: {id: string; nome: string; inicio: string; fim: string; fechado: boolean}[];
  periodo_id: string;
  regra: {nota_maxima: number; media_aprovacao: number};
  avaliacoes: Avaliacao[];
  alunos: {matricula_id: string; aluno_id: string; nome: string; faltas: number; frequencia: number | null}[];
  aulas_dadas: number;
  notas: Record<string, Record<string, {valor: number | null; status: StatusNota}>>;
  medias: Record<string, MediaAluno>;
};

export type Aula = {
  id: string;
  data: string;
  quantidade: number;
  conteudo: string | null;
  registros: {matricula_id: string; status: StatusPresenca; justificativa: string | null}[];
};

export type Regra = {
  tipo_media: 'aritmetica' | 'ponderada';
  pesos_periodos: number[] | null;
  recuperacao: 'nenhuma' | 'substitui_se_maior' | 'media';
  arredondamento: 'nenhum' | 'decimo' | 'meio';
  nota_maxima: number;
  media_aprovacao: number;
  frequencia_minima: number;
};

export type Boletim = {
  ano: number | null;
  turma: {id: string; nome: string; serie: string} | null;
  periodos: {id: string; nome: string; fechado: boolean}[];
  regra: Regra | null;
  somente_publicadas?: boolean;
  frequencia_geral?: number | null;
  disciplinas: {
    atribuicao_id: string;
    disciplina: string;
    professor: string;
    periodos: {
      periodo_id: string;
      media: number | null;
      recuperacao_aplicada: boolean;
      avaliacoes: (Avaliacao & {valor: number | null; status: StatusNota})[];
    }[];
    media_anual: number | null;
    media_completa: boolean;
    aulas_dadas: number;
    faltas: number;
    faltas_justificadas: number;
    frequencia: number | null;
    situacao: 'cursando' | 'abaixo_da_media' | 'aprovado' | 'reprovado' | 'reprovado_por_falta';
  }[];
};

export type Aviso = {
  id: string; titulo: string; corpo: string; escopo: 'escola' | 'turma'; turma_id: string | null; turma: string | null;
  autor: string | null; exige_ciente: boolean; publicar_em: string; arquivado: boolean; lido: boolean; ciente: boolean;
};
export type PainelAviso = {
  aviso: Aviso; total: number; lidos: number; cientes: number;
  destinatarios: {usuario_id: string; nome: string; lido_em: string | null; ciente_em: string | null}[];
};

export type Autorizacao = {
  id: string; titulo: string; descricao: string; turma: string | null; autor: string | null;
  data_evento: string | null; prazo: string | null; encerrada: boolean;
};
export type AutorizacaoEquipe = Autorizacao & {total: number; autorizados: number; negados: number; pendentes: number};
export type AutorizacaoFamilia = Autorizacao & {
  aluno_id: string; aluno: string; resposta: 'autorizo' | 'nao_autorizo' | null; observacao: string | null; respondido_em: string | null;
};
export type PainelAutorizacao = {
  autorizacao: Autorizacao; total: number; autorizado: number; negado: number; pendente: number;
  alunos: {aluno_id: string; aluno: string; situacao: 'autorizado' | 'negado' | 'pendente'; observacao: string | null; respondido_em: string | null}[];
};

export type Conversa = {id: string; assunto: string; aluno_id: string; aluno: string; escola_usuario: string; ultima_em: string; previa: string; nao_lida: boolean};
export type Anexo = {id: string; nome: string; tamanho: number; mime: string};
export type Mensagem = {id: string; autor: string | null; minha: boolean; corpo: string; criado_em: string; anexos: Anexo[]};
export type ConversaAberta = Conversa & {mensagens: Mensagem[]};

export type Notificacao = {id: string; tipo: string; titulo: string; corpo: string; url: string; criado_em: string; lida: boolean};
export type PreferenciasNotif = {email: boolean; silencio_inicio: string; silencio_fim: string};

export type TipoEvento = 'feriado' | 'sem_aula' | 'avaliacao' | 'evento' | 'prazo';
export type ItemCalendario = {
  id: string; origem: 'evento' | 'avaliacao'; tipo: TipoEvento; titulo: string; descricao: string | null;
  inicio: string; fim: string; turma_id: string | null; turma: string | null; autor: string | null; editavel: boolean;
};
export type FeriadoSugerido = {data: string; nome: string; nacional: boolean; base: string; ja_cadastrado: boolean};

export type StatusPedido = 'rascunho' | 'enviada' | 'ajustes' | 'aprovada' | 'impressa';
export type TipoPedido = 'prova' | 'trabalho' | 'lista';
export type Pedido = {
  id: string; tipo: TipoPedido; titulo: string; turma: string | null; turma_id: string; atribuicao_id: string; disciplina: string;
  professor: string; data_aplicacao: string; status: StatusPedido; publicado: boolean;
  arquivo: {nome: string; tamanho: number; mime: string};
  autor_id?: string; copias?: number; copias_calculadas?: number; copias_adaptadas?: number;
  frente_verso?: boolean; colorido?: boolean; grampear?: boolean; observacoes?: string | null;
  adaptado?: {nome: string; tamanho: number} | null; atrasado?: boolean;
  comentarios?: {id: string; autor: string | null; corpo: string; criado_em: string}[];
};
export type ConfigImpressao = {aprovacao: boolean; reserva_copias: number; antecedencia_dias: number};

export type AnoTempo = {
  ano: number; ano_letivo_id: string; encerrado: boolean; turma: string; serie: string; situacao: string;
  frequencia_geral?: number | string | null;
  disciplinas?: {disciplina: string; media_anual: number | string | null; frequencia: number | string | null; situacao: string}[];
};
export type LinhaTempo = {aluno: {id: string; nome: string; situacao: string}; anos: AnoTempo[]; notas_visiveis: boolean; so_publicadas: boolean; equipe: boolean};
export type PreviaRematricula = {
  turma: {id: string; nome: string; serie: string; ano: number}; ano_destino: {id: string; ano: number}; ultima_serie: boolean;
  turmas_destino: {id: string; nome: string; serie: string}[];
  alunos: {aluno_id: string; nome: string; situacao_aluno: string; matricula_situacao: string; sugestao: 'aprovado' | 'retido' | 'pendente'; motivo: string | null; turma_destino_sugerida: string | null; ja_rematriculado: boolean}[];
};
