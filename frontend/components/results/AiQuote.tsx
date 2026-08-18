export function AiQuote({ text }: { text: string }) {
  if (!text.trim()) {
    return null;
  }
  return (
    <div className="border-l-2 border-gold py-xs pl-md">
      <p className="font-newsreader text-title-lg italic text-gold">
        &ldquo;{text.trim()}&rdquo;
      </p>
    </div>
  );
}
