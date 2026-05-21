export default function InfoTip({ text }) {
  if (!text) return null;
  return (
    <span
      className="inline-flex items-center justify-center w-4 h-4 rounded-full
                 border border-border-subtle text-[10px] font-bold text-content-muted 
                 bg-surface cursor-help hover:bg-border-subtle hover:text-content-main transition-colors"
      title={text}
      aria-label={text}
    >
      i
    </span>
  );
}