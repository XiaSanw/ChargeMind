import { useState, useCallback } from 'react';
import { useDiagnosis } from '@/store/DiagnosisContext';
import { extractProfile } from '@/lib/api';

const EXAMPLE_TEXT = '我在深圳南山区科技园附近建了一个充电站，有20个快充桩，总装机功率1200kW，周边主要是写字楼和商场，月租金大概6万元，有4个运维人员。';

export default function StationInputPage() {
  const { setProfile, setCurrentPage, setError } = useDiagnosis();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = useCallback(async () => {
    if (!input.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await extractProfile(input.trim());
      setProfile(data.profile);
      setCurrentPage('enrich');
    } catch (err) {
      setError(err instanceof Error ? err.message : '解析失败，请重试');
    } finally {
      setLoading(false);
    }
  }, [input, setProfile, setCurrentPage, setError]);

  const handleExample = useCallback(() => {
    setInput(EXAMPLE_TEXT);
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary/10 text-primary mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-foreground">
            ChargeMind
          </h1>
          <p className="text-lg text-muted-foreground">
            充电场站智能诊断平台 — 算法硬数据 × LLM 泛化直觉
          </p>
        </div>

        {/* Input Card */}
        <div className="bg-card rounded-2xl border border-border p-6 shadow-lg">
          <label className="block text-sm font-medium text-foreground mb-2">
            描述您的充电场站
          </label>
          <p className="text-sm text-muted-foreground mb-3">
            用自然语言描述场站位置、规模、周边业态等信息，AI 将自动提取关键参数。
          </p>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="例如：我在深圳宝安区某物流园旁有个充电站，15个桩，总功率900kW..."
            rows={5}
            className="w-full rounded-xl border border-border bg-input px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none transition-all"
          />
          <div className="flex items-center justify-between mt-4">
            <button
              onClick={handleExample}
              type="button"
              className="text-sm text-primary hover:text-primary/80 transition-colors"
            >
              👉 使用示例
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading || !input.trim()}
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>
                  解析中...
                </>
              ) : (
                <>开始诊断 →</>
              )}
            </button>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground">
          当前为 Demo 版本，算法预测为基于规则的 Stub，后续将替换为真实模型
        </p>
      </div>
    </div>
  );
}
