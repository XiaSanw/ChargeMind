import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles, Send, Loader2, Lightbulb } from 'lucide-react';
import { useDiagnosis } from '@/store/DiagnosisContext';
import { extractProfile } from '@/lib/api';

interface ConsultDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

const EXAMPLE_TEXTS = [
  '我在深圳福田区啤酒小镇核心商圈建了一个大型超充站，紧邻深业上城购物中心，有32个快充桩，总装机功率2400kW，周边主要是商业综合体、餐饮街和写字楼，夜间客流也很大，月租金大概12万元，有6个运维人员，平均电价加服务费约0.9元每度。',
  '我在深圳福田区啤酒小镇旁边的一个住宅小区门口建了一个社区充电站，主要服务周边居民，有8个慢充桩和4个快充桩，总装机功率360kW，周边主要是住宅区和底商便利店，晚上充电需求比较集中，月租金大概2.8万元，有2个兼职运维人员。',
  '我在深圳福田区啤酒小镇附近的写字楼地下停车场建了一个办公配套充电站，主要服务上班白领，有15个快充桩，总装机功率900kW，周边全是甲级写字楼和商务酒店，工作日白天是充电高峰，月租金大概4.5万元，有2个专职运维人员。',
  '我在深圳福田区啤酒小镇对面的文旅街区建了一个特色充电站，靠近网红打卡点和精品酒店，有12个快充桩，总装机功率720kW，周边主要是酒店、民宿、咖啡馆和文创小店，周末和节假日客流爆满，月租金大概5万元，有3个运维人员。',
];

export default function ConsultDialog({ isOpen, onClose }: ConsultDialogProps) {
  const { setProfile, setCurrentPage, setError, landingInput, setLandingInput } = useDiagnosis();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const inputRef = useRef(input);
  inputRef.current = input;

  // 打开时恢复未提交的输入，并聚焦
  useEffect(() => {
    if (isOpen) {
      setInput(landingInput || '');
      setLocalError(null);
      setTimeout(() => textareaRef.current?.focus(), 300);
    }
  }, [isOpen, landingInput]);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const handleClose = useCallback(() => {
    // 保存未提交内容到 context，下次打开可恢复
    setLandingInput(inputRef.current.trim() || null);
    setLocalError(null);
    onClose();
  }, [setLandingInput, onClose]);

  const handleSubmit = useCallback(async () => {
    if (!input.trim() || loading) return;
    setLoading(true);
    setLocalError(null);
    setError(null);
    try {
      const { data } = await extractProfile(input.trim());
      setProfile(data.profile);
      setLandingInput(null);
      onClose();
      // 延迟跳转，让弹窗退场动画先完成
      setTimeout(() => setCurrentPage('enrich'), 400);
    } catch (err) {
      const msg = err instanceof Error ? err.message : '解析失败，请重试';
      setLocalError(msg);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [input, loading, setProfile, setCurrentPage, setError, setLandingInput, onClose]);

  const handleExample = useCallback(() => {
    const idx = Math.floor(Math.random() * EXAMPLE_TEXTS.length);
    setInput(EXAMPLE_TEXTS[idx]);
  }, []);

  const placeholderText = `例如：我在深圳南山区科技园附近有一个充电站，有 10 个 120kW 快充桩，周边主要是写字楼和住宅小区，目前日均充电量约 800 度，利用率 6% 左右……`;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
          {/* Backdrop with subtle glass blur */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="absolute inset-0 bg-navy/40"
            style={{
              backdropFilter: 'blur(8px)',
              WebkitBackdropFilter: 'blur(8px)',
            }}
            onClick={handleClose}
          />

          {/* Dialog */}
          <motion.div
            initial={{ opacity: 0, scale: 0.92, y: 30 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 20 }}
            transition={{
              duration: 0.5,
              ease: [0.16, 1, 0.3, 1],
            }}
            className="relative w-full max-w-2xl glass-dialog rounded-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-8 pt-8 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-copper/10 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-copper" />
                </div>
                <div>
                  <h2
                    className="text-xl font-semibold text-cream"
                    style={{ fontFamily: 'var(--font-heading)' }}
                  >
                    开始诊断
                  </h2>
                  <p className="text-sm text-slate-400 mt-0.5">
                    描述您的充电场站情况，AI 将为您生成诊断报告
                  </p>
                </div>
              </div>
              <motion.button
                whileHover={{ scale: 1.1, rotate: 90 }}
                whileTap={{ scale: 0.9 }}
                onClick={handleClose}
                className="w-9 h-9 rounded-full bg-navy-light/80 flex items-center justify-center text-slate-400 hover:text-cream hover:bg-navy-light transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </motion.button>
            </div>

            {/* Body */}
            <div className="px-8 py-4">
              {/* Error */}
              <AnimatePresence>
                {localError && (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    className="mb-4 rounded-xl px-4 py-3 text-sm font-medium bg-red-500/10 text-red-400 border border-red-500/20"
                  >
                    {localError}
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="relative">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={placeholderText}
                  rows={6}
                  className="w-full px-5 py-4 rounded-xl bg-navy-light/60 border border-copper/10 text-cream placeholder:text-slate-500 text-base leading-relaxed resize-none focus:outline-none focus:border-copper/40 focus:ring-1 focus:ring-copper/20 transition-all duration-300"
                />
                <div className="absolute bottom-3 right-3 text-xs text-slate-500">
                  {input.length} 字
                </div>
              </div>

              {/* Quick tags */}
              <div className="flex flex-wrap gap-2 mt-4">
                {['深圳南山区快充站', '工业园充电站', '商场地下充电桩'].map((tag) => (
                  <button
                    key={tag}
                    onClick={() => setInput((prev) => (prev ? prev + '，' : '') + tag)}
                    className="px-3 py-1.5 rounded-lg text-sm text-slate-400 bg-navy-light/40 border border-copper/5 hover:border-copper/20 hover:text-cream transition-all duration-200 cursor-pointer"
                  >
                    + {tag}
                  </button>
                ))}
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-8 pb-8 pt-2">
              <button
                onClick={handleExample}
                type="button"
                className="inline-flex items-center gap-1.5 text-xs text-copper hover:text-copper-light transition-colors cursor-pointer"
              >
                <Lightbulb className="w-3.5 h-3.5" />
                使用示例
              </button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSubmit}
                disabled={!input.trim() || loading}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-copper text-navy font-semibold text-sm tracking-wide transition-all duration-300 hover:bg-copper-light disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>解析中...</span>
                  </>
                ) : (
                  <>
                    <span>提交诊断</span>
                    <Send className="w-4 h-4" />
                  </>
                )}
              </motion.button>
            </div>

            {/* Decorative glow */}
            <div className="absolute -top-20 -right-20 w-40 h-40 rounded-full bg-copper/5 blur-3xl pointer-events-none" />
            <div className="absolute -bottom-20 -left-20 w-40 h-40 rounded-full bg-teal/5 blur-3xl pointer-events-none" />
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
