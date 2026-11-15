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
