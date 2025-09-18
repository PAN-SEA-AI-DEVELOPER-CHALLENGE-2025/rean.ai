export default function DecorativeDoodles() {
  return (
    <>
      {/* Doodle icons (decorative) */}
      <svg
        className="pointer-events-none absolute left-10 top-16 text-sky-300"
        width="28"
        height="28"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          d="M3 7h18M3 12h18M3 17h18"
          stroke="currentColor"
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
        />
      </svg>
      <svg
        className="pointer-events-none absolute right-24 top-24 text-sky-200"
        width="36"
        height="36"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          d="M12 2v20M2 12h20"
          stroke="currentColor"
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
        />
      </svg>
    </>
  );
}
