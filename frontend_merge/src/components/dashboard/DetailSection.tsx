import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChevronDown, ChevronUp, Minus } from 'lucide-react';

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
        <div className="px-6 pb-8 border-t border-border/50">
          <div className="pt-5 max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h2: ({ children }) => (
                  <h2 className="relative text-lg font-bold text-foreground mt-8 mb-4 pl-3">
                    <span className="absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-full bg-primary/60" />
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-sm font-semibold text-primary uppercase tracking-wide mt-6 mb-3">
                    {children}
                  </h3>
                ),
                p: ({ children }) => (
                  <p className="text-sm text-[#c9cdd3] leading-7 mb-5 last:mb-0">
                    {children}
                  </p>
                ),
                ul: ({ children }) => (
                  <ul className="space-y-2.5 mb-5 list-none pl-0">
                    {children}
                  </ul>
                ),
                li: ({ children }) => (
                  <li className="flex items-start gap-2.5 text-sm text-[#c9cdd3] leading-7">
                    <Minus size={12} className="mt-2.5 shrink-0 text-primary/50" />
                    <span>{children}</span>
                  </li>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-2 border-primary/30 bg-primary/[0.04] pl-4 pr-4 py-3 rounded-r-lg mb-5">
                    <div className="text-sm text-muted-foreground italic leading-7">
                      {children}
                    </div>
                  </blockquote>
                ),
                table: ({ children }) => (
                  <div className="overflow-x-auto mb-5 rounded-lg border border-border/40">
                    <table className="w-full text-sm border-collapse">
                      {children}
                    </table>
                  </div>
                ),
                thead: ({ children }) => (
                  <thead className="bg-secondary/40">
                    {children}
                  </thead>
                ),
                th: ({ children }) => (
                  <th className="text-left text-xs font-semibold text-foreground uppercase tracking-wider px-3 py-2.5 border-b border-border/40">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="text-left text-sm text-[#c9cdd3] px-3 py-2.5 border-b border-border/30">
                    {children}
                  </td>
                ),
                tr: ({ children }) => (
                  <tr className="hover:bg-secondary/20 transition-colors">
                    {children}
                  </tr>
                ),
                hr: () => (
                  <hr className="border-border/30 my-6" />
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold text-foreground">
                    {children}
                  </strong>
                ),
                code: ({ children }) => (
                  <code className="text-xs bg-secondary/60 text-primary px-1.5 py-0.5 rounded font-mono">
                    {children}
                  </code>
                ),
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
