import { Link } from 'react-router-dom';

const cards = [
  {
    to: '/risk-map',
    title: 'Mapa de Riesgo',
    desc: 'Probabilidad de gol por intervalo de 15 minutos para cualquier seleccion.',
  },
  {
    to: '/profile',
    title: 'Perfil Tactico',
    desc: 'Cluster historico y equipos con estilo ofensivo similar.',
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
      <h1 className="font-display text-6xl text-gold tracking-widest mb-4">
        INTELIGENCIA TACTICA FIFA
      </h1>
      <p className="text-gray-300 text-lg max-w-2xl mb-14">
        Sistema de Machine Learning sobre el historico de goles del Mundial FIFA 1930-2022.
        Modelos de clasificacion supervisada y clustering para asistir la toma de
        decisiones de cuerpos tecnicos.
      </p>
      <div className="grid md:grid-cols-3 gap-6">
        {cards.map(({ to, title, desc }) => (
          <Link
            key={to}
            to={to}
            className="group bg-card-bg border border-border-subtle rounded-2xl p-6
                       hover:border-gold hover:shadow-lg hover:shadow-gold/10 transition-all"
          >
            <h2 className="font-display text-2xl text-white mt-3 mb-2 tracking-wide">
              {title}
            </h2>
            <p className="text-gray-400 text-sm leading-relaxed">{desc}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}
