/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Fondos (Backgrounds)
        "bg-base": "#ffffff",        // Blanco puro para el body, como pediste
        "bg-surface": "#f4f7f5",     // Un gris-verde muy sutil para tarjetas o modales (crea profundidad)

        // Brand / UI Colors
        "brand-dark": "#0A472E",     // Verde oscuro profundo y elegante para el Header
        "brand-primary": "#199165",  // Tu verde original, perfecto para botones primarios o enlaces
        "brand-accent": "#b8e986",   // Lime accent original, ideal para badges o notificaciones de éxito
        
        // Texto y Bordes
        "text-main": "#1e293b",      // Un slate-800 para texto. Nunca uses negro puro (#000), cansa la vista.
        "text-muted": "#64748b",     // Slate-500 para texto secundario o descripciones
        "border-subtle": "#d8e7dc",  // Mantenemos tu borde suave
        
        // Alertas / Estados
        "status-gold": "#F5A623",    // Reemplacé tu 'gold' duplicado por un amarillo real para warnings/estrellas
      },
      fontFamily: {
        display: ["'Bebas Neue'", "sans-serif"],
        body: ["'DM Sans'", "sans-serif"],
      },
    },
  },
  plugins: [],
};