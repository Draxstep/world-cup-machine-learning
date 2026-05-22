import { Link } from 'react-router-dom';

const cards = [
  {
    to: '/team',
    title: 'Analisis Tactico',
    desc: 'Selecciona un pais y ve su perfil tactico y mapa de riesgo en una sola vista.',
  },
  {
    to: '/dashboard',
    title: 'Dashboard',
    desc: 'Metricas del modelo y resumen del clustering K-Means.',
  },
];

export default function Home() {
  return (
    <main className="max-w-5xl mx-auto px-6 py-20">
      <h1 className="font-display text-5xl md:text-6xl text-content-main tracking-widest mb-4">
        SISTEMA INTELIGENCIA TACTICA
      </h1>
      <p className="text-content-muted text-lg max-w-2xl mb-14">
        Sistema de Machine Learning sobre el historico de goles del Mundial FIFA 1930-2022.
        Modelos de clasificacion supervisada y clustering para asistir la toma de
        decisiones de cuerpos tecnicos.
      </p>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards.map(({ to, title, desc }) => (
          <Link
            key={to}
            to={to}
            className="group bg-surface border border-border-subtle rounded-2xl p-6
                       hover:border-brand-primary hover:shadow-lg hover:shadow-brand-primary/10 transition-all"
          >
            <h2 className="font-display text-2xl text-content-main mt-3 mb-2 tracking-wide">
              {title}
            </h2>
            <p className="text-content-muted text-sm leading-relaxed">{desc}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}