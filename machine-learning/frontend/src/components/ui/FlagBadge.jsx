function getInitials(name = '') {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('');
}

export default function FlagBadge({ src, name, size = 28 }) {
  const initials = getInitials(name);

  if (src) {
    return (
      <img
        src={src}
        alt={name}
        width={size}
        height={size}
        className="rounded-full border border-border-subtle object-cover"
        loading="lazy"
      />
    );
  }

  return (
    <div
      className="rounded-full border border-border-subtle bg-dark-bg text-gray-200
                 flex items-center justify-center text-[10px] font-semibold"
      style={{ width: size, height: size }}
      aria-label={name}
    >
      {initials || '--'}
    </div>
  );
}
