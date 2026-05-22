import { Link, useLocation } from 'react-router-dom';

const navLinks = [
  { to: '/', label: 'Inicio' },
  { to: '/team', label: 'Analisis Tactico' },
  { to: '/dashboard', label: 'Dashboard' },
];

export default function Header() {
  const { pathname } = useLocation();
  const isTeamSection = pathname.startsWith('/team');
  return (
    <header className="sticky top-0 z-50 bg-brand-dark shadow-md">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="font-display text-2xl text-white tracking-wider">
          Sistema de inteligencia tactica
        </Link>
        <nav className="flex gap-6">
          {navLinks.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={`text-sm font-medium transition-colors ${
                (to === '/team' ? isTeamSection : pathname === to)
                  ? 'text-brand-accent'
                  : 'text-white/80 hover:text-brand-accent'
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}