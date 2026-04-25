import { useState, useEffect, useCallback } from 'react';
import { useDiagnosis } from '@/store/DiagnosisContext';
import { enrichProfile, diagnoseStation } from '@/lib/api';
import type { NextQuestion, StationProfile } from '@/types/diagnosis';

// 每个问题的示例回答（显示在问题下方引导用户）
const QUESTION_EXAMPLES: Record<string, string> = {
  region: '例如：福田区',
  business_type: '可多选，例如：商业区 + 餐饮区',
  total_installed_power: '例如：1080（单位：kW）',
  pile_count: '例如：18（个）',
  monthly_rent: '例如：55000（元/月）',
  staff_count: '例如：3（人）',
  avg_price: '例如：0.85（元/度，含电价+服务费）',
  pile_breakdown: '请分别填写三种功率等级的桩数量',
};

// multi-number 的默认值
const createMultiNumberDefault = (q: NextQuestion): Record<string, number | ''> => {
  const defaults: Record<string, number | ''> = {};
  q.subfields?.forEach((sf) => {
    // brand_piles 默认填 0，用户只需改自己有的品牌
    defaults[sf.key] = q.key === 'brand_piles' ? 0 : '';
  });
  return defaults;
};

export default function EnrichPage() {
  const { profile, updateProfileField, setDiagnoseResult, setCurrentPage, setError, setIsDiagnosing } = useDiagnosis();
  const [question, setQuestion] = useState<NextQuestion | null>(null);
  const [missingCount, setMissingCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [diagnoseLoading, setDiagnoseLoading] = useState(false);
  const [inputValue, setInputValue] = useState<string | string[] | Record<string, number | ''>>('');
  const [history, setHistory] = useState<{ q: NextQuestion; a: string | string[] | Record<string, number | ''> }[]>([]);

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
        const nextType = data.next_question?.type;
        if (nextType === 'multiselect') {
          setInputValue([]);
        } else if (nextType === 'multi-number') {
          setInputValue(createMultiNumberDefault(data.next_question!));
        } else {
          setInputValue('');
        }
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
    } else if (question.type === 'multi-number') {
      const obj = inputValue as Record<string, number | ''>;
      const result: Record<string, number> = {};
      let hasEmpty = false;
      for (const [k, v] of Object.entries(obj)) {
        // brand_piles：没填默认转 0
        if (question.key === 'brand_piles' && (v === '' || v === null || v === undefined)) {
          result[k] = 0;
          continue;
        }
        const num = Number(v);
        if (v === '' || isNaN(num)) {
          hasEmpty = true;
          break;
        }
        result[k] = num;
      }
      if (hasEmpty) return;
      val = result;
    }

    // 构造更新后的 profile（同步，不依赖 Context state 延迟）
    const updatedProfile: StationProfile = { ...profile, [question.key]: val };

    updateProfileField(question.key, val);
    setHistory((prev) => [...prev, { q: question, a: inputValue }]);
    await fetchNextQuestion(updatedProfile);
  }, [question, inputValue, profile, updateProfileField, fetchNextQuestion]);



  const answeredCount = history.length;
  const totalSteps = answeredCount + missingCount;
  const progress = totalSteps > 0 ? Math.round((answeredCount / totalSteps) * 100) : 0;

  // 判断当前是否可提交
  const isSubmitDisabled = (() => {
    if (loading) return true;
    if (question?.type === 'multiselect') {
      return !Array.isArray(inputValue) || inputValue.length === 0;
    }
    if (question?.type === 'multi-number') {
      const obj = inputValue as Record<string, number | ''>;
      // brand_piles 默认都是 0，允许空值（提交时会转为 0）
      if (question.key === 'brand_piles') return false;
      return Object.values(obj).some((v) => v === '' || v === null || v === undefined);
    }
    return inputValue === '' || inputValue === null;
  })();

  // 格式化历史记录中的答案用于展示
  const formatAnswer = (a: string | string[] | Record<string, number | ''>): string => {
    if (Array.isArray(a)) return a.join('、');
    if (typeof a === 'object') {
      return Object.entries(a)
        .map(([k, v]) => {
          const labelMap: Record<string, string> = {
            slow: '慢充',
            fast: '快充',
            super: '超充',
          };
          return `${labelMap[k] || k}: ${v}台`;
        })
        .join('，');
    }
    return String(a);
  };

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
              {QUESTION_EXAMPLES[question.key] && (
                <p className="text-sm text-muted-foreground">💡 {QUESTION_EXAMPLES[question.key]}</p>
              )}
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

            {question.type === 'multi-number' && question.subfields && (
              <div className="space-y-4">
                {question.subfields.map((sf) => {
                  const obj = inputValue as Record<string, number | ''>;
                  return (
                    <div key={sf.key}>
                      <label className="block text-sm font-medium text-foreground mb-1.5">
                        {sf.label}
                      </label>
                      <input
                        type="number"
                        min={0}
                        value={obj[sf.key] ?? ''}
                        onChange={(e) => {
                          const val = e.target.value;
                          setInputValue((prev) => ({
                            ...(prev as Record<string, number | ''>),
                            [sf.key]: val === '' ? '' : Number(val),
                          }));
                        }}
                        placeholder={sf.placeholder || '请输入数量'}
                        className="w-full rounded-xl border border-border bg-input px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-all"
                        autoFocus={sf.key === question.subfields![0].key}
                      />
                    </div>
                  );
                })}
              </div>
            )}

            <div className="flex items-center justify-end pt-2">
              <button
                onClick={handleSubmit}
                disabled={isSubmitDisabled}
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
                  <span className="font-medium text-foreground">{formatAnswer(h.a)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
