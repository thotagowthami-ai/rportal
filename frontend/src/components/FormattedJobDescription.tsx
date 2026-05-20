type FormattedJobDescriptionProps = {
  content: string;
};

const SECTION_HEADERS = [
  "what you'll do",
  "requirements",
  "qualifications",
  "benefits",
  "responsibilities",
  "about us",
  "who we are",
  "how to apply",
];

function renderBold(text: string) {
  const parts = text.split(/\*\*([^*]+)\*\*/g);
  return parts.map((part, i) =>
    i % 2 === 1 ? <strong key={i} className="font-bold text-black">{part}</strong> : part
  );
}

export function FormattedJobDescription({ content }: FormattedJobDescriptionProps) {
  const lines = content.split("\n");

  return (
    <div className="space-y-3 text-sm text-slate-700 whitespace-pre-wrap">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <br key={idx} />;

        const lowerLine = trimmed.toLowerCase();

        // Clean line — remove raw ** for display
        const cleanLine = trimmed.replace(/\*\*/g, "");

        // Hashtags
        if (trimmed.startsWith("#")) {
          const hashtagParts = trimmed.split(/(#\w+)/g);
          return (
            <p key={idx}>
              {hashtagParts.map((part, partIdx) =>
                part.startsWith("#") ? (
                  <span key={partIdx} className="text-blue-600 font-medium">{part}</span>
                ) : part
              )}
            </p>
          );
        }

        // 🚀 Hiring line
        if (trimmed.startsWith("🚀")) {
          return <p key={idx} className="font-bold text-black text-base">{cleanLine}</p>;
        }

        // 📍 Location line
        if (trimmed.startsWith("📍")) {
          return <p key={idx}>{cleanLine}</p>;
        }

        // Tech stack line — bold header
        if (lowerLine.includes("tech stack")) {
          return (
            <p key={idx} className="font-bold text-black">
              {cleanLine}
            </p>
          );
        }

        // Section headers (✅ What you'll do etc)
        const isHeader = SECTION_HEADERS.some((header) => {
          const pattern = new RegExp(`^[#\\s]*[✅✔]?\\s*${header}[:\\-|]?`, "i");
          return pattern.test(trimmed);
        });

        if (isHeader) {
          return (
            <p key={idx} className="font-bold text-black text-base mt-4 first:mt-0">
              {cleanLine}
            </p>
          );
        }

        // Bullet points
        // Bullet points - make sure ** lines don't get caught here
if ((trimmed.startsWith("-") || trimmed.startsWith("•")) ) {
  return (
    <p key={idx} className="pl-4">
      • {trimmed.slice(1).trim()}
    </p>
  );
}

        // Any line with **bold** markers
        if (trimmed.includes("**")) {
          return <p key={idx} className="font-bold text-black">{renderBold(trimmed)}</p>;
        }

        return <p key={idx}>{trimmed}</p>;
      })}
    </div>
  );
}