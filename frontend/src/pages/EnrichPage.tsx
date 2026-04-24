import { useState, useEffect, useCallback } from 'react';
import { useDiagnosis } from '@/store/DiagnosisContext';
import { enrichProfile, diagnoseStation } from '@/lib/api';
import type { NextQuestion, StationProfile } from '@/types/diagnosis';

// 与后端 stub.py 默认值保持一致，跳过问题时用这些值填充
const SKIP_DEFAULTS: Record<string, unknown> = {
  region: '未知',
  business_type: [],
  total_installed_power: 100,
  pile_count: 10,
  monthly_rent: 50000,
  staff_count: 3,
  avg_price: 0.6,
};

export default function EnrichPage() {
  const { profile, updateProfileField, setDiagnoseResult, setCurrentPage, setError, setIsDiagnosing } = useDiagnosis();
  const [question, setQuestion] = useState<NextQuestion | null>(null);
  const [missingCount, setMissingCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [diagnoseLoading, setDiagnoseLoading] = useState(false);
  const [inputValue, setInputValue] = useState<string | string[]>('');
  const [history, setHistory] = useState<{ q: NextQuestion; a: string | string[] }[]>([]);

  // fetchNextQuestion 接受可选的 currentProfile，避免闭包 stale profile 问题
  const fetchNextQuestion = useCallback(async (currentProfile?: StationProfile) => {
    const p = currentProfile || profile;
    if (!p) return;
    setLoading(true);
    try {
      const { data } = await enrichProfile(p);
      if (data.complete) {
        setQuestion(null);
        setMissingCount(0);
        await runDiagnose(p);
      } else {
        setQuestion(data.next_question || null);
        setMissingCount(data.missing_count);
        setInputValue(data.next_question?.type === 'multiselect' ? [] : '');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取问题失败');
    } finally {
      setLoading(false);
    }
  }, [profile, setError]);

  const runDiagnose = useCallback(async (currentProfile?: StationProfile) => {
    const p = currentProfile || profile;
    if (!p) return;
    setDiagnoseLoading(true);
    setIsDiagnosing(true);
    setCurrentPage('report');
    try {
      const { data } = await diagnoseStation(p);
      setDiagnoseResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '诊断失败');
      setCurrentPage('enrich');
    } finally {
      setDiagnoseLoading(false);
      setIsDiagnosing(false);
    }
  }, [profile, setDiagnoseResult, setCurrentPage, setError, setIsDiagnosing]);

  // 组件挂载时，如果 profile 存在但没有问题，自动获取第一个问题
  useEffect(() => {
    if (profile && !question && !diagnoseLoading && !loading) {
      fetchNextQuestion();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!question || !profile) return;

    let val: unknown = inputValue;
    if (question.type === 'number') {
      const num = Number(inputValue);
      val = isNaN(num) ? undefined : num;
    }

    // 空值视为跳过，使用默认值
    if (val === undefined || val === '' || val === null || (Array.isArray(val) && val.length === 0)) {
      val = SKIP_DEFAULTS[question.key];
    }

    // 构造更新后的 profile（同步，不依赖 Context state 延迟）
    const updatedProfile: StationProfile = { ...profile, [question.key]: val };

    updateProfileField(question.key, val);
    setHistory((prev) => [...prev, { q: question, a: inputValue }]);
    await fetchNextQuestion(updatedProfile);
  }, [question, inputValue, profile, updateProfileField, fetchNextQuestion]);

  const handleSkip = useCallback(async () => {
    if (!question || !profile) return;

    const defaultVal = SKIP_DEFAULTS[question.key];
    const updatedProfile: StationProfile = { ...profile, [question.key]: defaultVal };

    updateProfileField(question.key, defaultVal);
    setHistory((prev) => [...prev, { q: question, a: '跳过' }]);
    await fetchNextQuestion(updatedProfile);
  }, [question, profile, updateProfileField, fetchNextQuestion]);

  const answeredCount = history.length;
  const totalSteps = answeredCount + missingCount;
  const progress = totalSteps > 0 ? Math.round((answeredCount / totalSteps) * 100) : 0;

  if (diagnoseLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-4">
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10">
            <svg className="animate-spin h-8 w-8 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>
          </div>
          <h2 className="text-xl font-semibold">正在启动双引擎诊断...</h2>
          <p className="text-muted-foreground">算法预测 × 知识库类比并行计算中</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-xl space-y-6">
        {/* Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">补充关键信息</span>
            <span className="text-muted-foreground">{answeredCount} / {totalSteps || '?'}</span>
          </div>
          <div className="h-2 rounded-full bg-secondary overflow-hidden">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Question Card */}
        {question && (
          <div className="bg-card rounded-2xl border border-border p-8 shadow-lg space-y-6">
            <div className="space-y-2">
              <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
                问题 {answeredCount + 1}
              </span>
              <h2 className="text-xl font-semibold text-foreground">{question.question}</h2>
            </div>

            {/* Input by type */}
            {question.type === 'select' && question.options && (
              <div className="grid grid-cols-2 gap-3">
                {question.options.map((opt) => (
                  <button
                    key={opt}
                    onClick={() => setInputValue(opt)}
                    className={`rounded-xl border px-4 py-3 text-sm font-medium transition-all text-left ${
                      inputValue === opt
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-border bg-input text-foreground hover:border-muted-foreground'
                    }`}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            )}

            {question.type === 'multiselect' && question.options && (
              <div className="grid grid-cols-2 gap-3">
                {question.options.map((opt) => {
                  const selected = Array.isArray(inputValue) && inputValue.includes(opt);
                  return (
                    <button
                      key={opt}
                      onClick={() => {
                        const arr = Array.isArray(inputValue) ? [...inputValue] : [];
                        if (selected) {
                          setInputValue(arr.filter((x) => x !== opt));
                        } else {
                          setInputValue([...arr, opt]);
                        }
                      }}
                      className={`rounded-xl border px-4 py-3 text-sm font-medium transition-all text-left ${
                        selected
                          ? 'border-primary bg-primary/10 text-primary'
                          : 'border-border bg-input text-foreground hover:border-muted-foreground'
                      }`}
                    >
                      {selected ? '✓ ' : ''}{opt}
                    </button>
                  );
                })}
              </div>
            )}

            {(question.type === 'text' || question.type === 'number') && (
              <input
                type={question.type === 'number' ? 'number' : 'text'}
                value={inputValue as string}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                placeholder="请输入..."
                className="w-full rounded-xl border border-border bg-input px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-all"
                autoFocus
              />
            )}

            <div className="flex items-center justify-between pt-2">
              <button
                onClick={handleSkip}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                跳过此题
              </button>
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-all"
              >
                {loading ? '加载中...' : '下一步 →'}
              </button>
            </div>
          </div>
        )}

        {/* History */}
        {history.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-muted-foreground">已回答</h3>
            <div className="space-y-2">
              {history.map((h, i) => (
                <div key={i} className="flex items-center justify-between rounded-xl bg-secondary/50 px-4 py-2.5 text-sm">
                  <span className="text-muted-foreground">{h.q.question}</span>
                  <span className="font-medium text-foreground">
                    {Array.isArray(h.a) ? h.a.join('、') : h.a}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
