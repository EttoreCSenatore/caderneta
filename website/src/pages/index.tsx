import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

type Feature = {title: string; body: string};

const features: Feature[] = [
  {
    title: 'Notas e médias automáticas',
    body: 'O professor lança as notas; a média é calculada com a regra da escola e aparece na hora para alunos e responsáveis.',
  },
  {
    title: 'Comunicação com a família',
    body: 'Avisos gerais, por turma ou para um aluno específico, com confirmação de leitura dos responsáveis.',
  },
  {
    title: 'Calendário escolar',
    body: 'Feriados, eventos e dias sem aula definidos pela escola; cada professor adiciona eventos só para as suas turmas.',
  },
  {
    title: 'Provas na fila de impressão',
    body: 'O professor envia a prova, a coordenação aprova e a secretaria imprime a quantidade certa de cópias.',
  },
  {
    title: 'Histórico que acompanha o aluno',
    body: 'Notas, frequência e anotações passam de um ano para o outro sem retrabalho na rematrícula.',
  },
  {
    title: 'Leve, no navegador e no celular',
    body: 'Um web app instalável (PWA) que funciona em celulares simples e conexões lentas.',
  },
];

const roles = ['Escola', 'Coordenação', 'Professores', 'Responsáveis', 'Alunos'];

export default function Home(): ReactNode {
  return (
    <Layout
      title="Plataforma escolar simples"
      description="Caderneta é uma plataforma leve para escolas, professores, responsáveis e alunos: notas, médias, avisos, calendário e provas.">
      <header className={styles.hero}>
        <div className="container">
          <Heading as="h1" className={styles.title}>
            Caderneta
          </Heading>
          <p className={styles.tagline}>
            Notas, avisos e calendário da escola num só lugar, para quem ensina, quem aprende e quem acompanha.
          </p>
          <div className={styles.roles}>
            {roles.map((r) => (
              <span key={r} className={styles.role}>
                {r}
              </span>
            ))}
          </div>
          <div className={styles.buttons}>
            <Link className="button button--primary button--lg" to="/docs/intro">
              Ler a documentação
            </Link>
            <Link className="button button--secondary button--lg" to="/docs/roadmap">
              Roadmap
            </Link>
          </div>
        </div>
      </header>
      <main className="container">
        <section className={styles.features}>
          {features.map((f) => (
            <div key={f.title} className={styles.card}>
              <Heading as="h3">{f.title}</Heading>
              <p>{f.body}</p>
            </div>
          ))}
        </section>
      </main>
    </Layout>
  );
}
