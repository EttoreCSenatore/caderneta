import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import Translate, {translate} from '@docusaurus/Translate';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

type Feature = {title: string; body: string};

const features: Feature[] = [
  {
    title: translate({id: 'home.feature.0.title', message: 'Notas e médias automáticas'}),
    body: translate({id: 'home.feature.0.body', message: 'O professor lança as notas; a média é calculada com a regra da escola e aparece na hora para alunos e responsáveis.'}),
  },
  {
    title: translate({id: 'home.feature.1.title', message: 'Comunicação com a família'}),
    body: translate({id: 'home.feature.1.body', message: 'Avisos gerais, por turma ou para um aluno específico, com confirmação de leitura dos responsáveis.'}),
  },
  {
    title: translate({id: 'home.feature.2.title', message: 'Calendário escolar'}),
    body: translate({id: 'home.feature.2.body', message: 'Feriados, eventos e dias sem aula definidos pela escola; cada professor adiciona eventos só para as suas turmas.'}),
  },
  {
    title: translate({id: 'home.feature.3.title', message: 'Provas na fila de impressão'}),
    body: translate({id: 'home.feature.3.body', message: 'O professor envia a prova, a coordenação aprova e a secretaria imprime a quantidade certa de cópias.'}),
  },
  {
    title: translate({id: 'home.feature.4.title', message: 'Histórico que acompanha o aluno'}),
    body: translate({id: 'home.feature.4.body', message: 'Notas, frequência e anotações passam de um ano para o outro sem retrabalho na rematrícula.'}),
  },
  {
    title: translate({id: 'home.feature.5.title', message: 'Leve, no navegador e no celular'}),
    body: translate({id: 'home.feature.5.body', message: 'Um web app instalável (PWA) que funciona em celulares simples e conexões lentas.'}),
  },
];

const roles = [
  translate({id: 'home.role.school', message: 'Escola'}),
  translate({id: 'home.role.coord', message: 'Coordenação'}),
  translate({id: 'home.role.teachers', message: 'Professores'}),
  translate({id: 'home.role.guardians', message: 'Responsáveis'}),
  translate({id: 'home.role.students', message: 'Alunos'}),
];

export default function Home(): ReactNode {
  return (
    <Layout
      title={translate({id: 'home.title', message: 'Plataforma escolar simples'})}
      description={translate({
        id: 'home.description',
        message: 'Caderneta é uma plataforma leve para escolas, professores, responsáveis e alunos: notas, médias, avisos, calendário e provas.',
      })}>
      <header className={styles.hero}>
        <div className="container">
          <Heading as="h1" className={styles.title}>
            Caderneta
          </Heading>
          <p className={styles.tagline}>
            <Translate id="home.tagline">Notas, avisos e calendário da escola num só lugar, para quem ensina, quem aprende e quem acompanha.</Translate>
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
              <Translate id="home.docs">Ler a documentação</Translate>
            </Link>
            <Link className="button button--secondary button--lg" to="/docs/roadmap">
              <Translate id="home.roadmap">Roadmap</Translate>
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
