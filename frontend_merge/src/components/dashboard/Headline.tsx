interface Props {
  text: string;
}

export default function Headline({ text }: Props) {
  return (
    <div className="rounded-2xl border border-border bg-card p-6 md:p-8">
      <p className="text-lg md:text-xl leading-relaxed font-medium text-foreground">
        {text}
      </p>
    </div>
  );
}
