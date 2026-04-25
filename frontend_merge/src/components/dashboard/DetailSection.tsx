import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface Props {
  content: string;
}

export default function DetailSection({ content }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-2xl border border-border bg-card overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-6 text-left hover:bg-secondary/30 transition-colors"
      >
        <h3 className="text-lg font-semibold">📝 详细分析</h3>
        <span className="text-muted-foreground">
          {open ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </span>
      </button>
      {open && (
        <div className="px-6 pb-6 border-t border-border">
          <div className="prose prose-invert prose-sm max-w-none pt-4">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
