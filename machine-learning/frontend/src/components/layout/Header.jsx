import { Link, useLocation } from 'react-router-dom';

const navLinks = [
  { to: '/', label: 'Inicio' },
  { to: '/risk-map', label: 'Mapa de Riesgo' },
  { to: '/profile', label: 'Perfil Tactico' },
  { to: '/dashboard', label: 'Dashboard' },
];

export default function Header() {
  const { pathname } = useLocation();
  return (
    <header className="sticky top-0 z-50 bg-dark-bg/80 backdrop-blur border-b border-border-subtle">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="font-display text-2xl text-gold tracking-wider">
          FIFA TACTICA ML
        </Link>
        <nav className="flex gap-6">
          {navLinks.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={`text-sm font-medium transition-colors ${
                pathname === to ? 'text-gold' : 'text-gray-400 hover:text-white'
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
