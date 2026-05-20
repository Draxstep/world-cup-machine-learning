export default function ErrorBanner({ message }) {
  if (!message) return null;
  return (
    <div className="bg-red-900/40 border border-red-600 text-red-300 rounded-lg px-4 py-3 text-sm">
      Warning: {message}
    </div>
  );
}
