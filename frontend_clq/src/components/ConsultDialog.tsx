import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles, Send, Loader2 } from 'lucide-react';

interface ConsultDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ConsultDialog({ isOpen, onClose }: ConsultDialogProps) {
  const [input, setInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isOpen && textareaRef.current) {
      setTimeout(() => textareaRef.current?.focus(), 300);
    }
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  const handleSubmit = async () => {
    if (!input.trim()) return;
    setIsSubmitting(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsSubmitting(false);
    setInput('');
    onClose();
  };

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
            onClick={onClose}
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
                onClick={onClose}
                className="w-9 h-9 rounded-full bg-navy-light/80 flex items-center justify-center text-slate-400 hover:text-cream hover:bg-navy-light transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </motion.button>
            </div>

            {/* Body */}
            <div className="px-8 py-4">
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
              <span className="text-xs text-slate-500">
                支持自然语言描述，越详细诊断越精准
              </span>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSubmit}
                disabled={!input.trim() || isSubmitting}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-copper text-navy font-semibold text-sm tracking-wide transition-all duration-300 hover:bg-copper-light disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>分析中...</span>
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
