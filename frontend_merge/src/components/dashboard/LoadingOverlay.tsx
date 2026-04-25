import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Props {
  forceComplete?: boolean;
  onDone?: () => void;
}

const PHASES = [
  { label: '正在解析场站画像...' },
  { label: '算法硬算分析中...' },
  { label: 'RAG 检索相似场站...' },
  { label: 'LLM 叙事包装中...' },
];

const TOTAL_FILL_MS = 30_000;        // 30 秒匀速填满
const FAST_FILL_MS = 350;            // 完成后快速填满耗时

export default function LoadingOverlay({ forceComplete, onDone }: Props) {
  const [fill, setFill] = useState(0);           // 0 ~ 100
  const [phaseIndex, setPhaseIndex] = useState(0);
  const [exiting, setExiting] = useState(false);
  const fillRef = useRef(0);
  const rafRef = useRef<number | null>(null);
  const startRef = useRef(Date.now());

  /* ── 匀速缓慢填充 ── */
  const tick = useCallback(() => {
    const elapsed = Date.now() - startRef.current;
    let nextFill = (elapsed / TOTAL_FILL_MS) * 100;
    if (nextFill > 100) nextFill = 100;

    fillRef.current = nextFill;
    setFill(nextFill);

    // 阶段切换（按时间均分）
    const nextPhase = Math.min(
      Math.floor((elapsed / TOTAL_FILL_MS) * PHASES.length),
      PHASES.length - 1
    );
    setPhaseIndex((prev) => (prev !== nextPhase ? nextPhase : prev));

    if (nextFill < 100 && !forceComplete) {
      rafRef.current = requestAnimationFrame(tick);
    }
  }, [forceComplete]);

  useEffect(() => {
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [tick]);

  /* ── 强制完成：快速填满 → 淡出 ── */
  useEffect(() => {
    if (forceComplete && !exiting) {
      setExiting(true);
      const startFast = fillRef.current;
      const fastStart = Date.now();

      const fastTick = () => {
        const p = Math.min((Date.now() - fastStart) / FAST_FILL_MS, 1);
        const eased = 1 - Math.pow(1 - p, 3); // easeOutCubic
        const next = startFast + (100 - startFast) * eased;
        setFill(next);

        if (p < 1) {
          requestAnimationFrame(fastTick);
        } else {
          setTimeout(() => onDone?.(), 400);
        }
      };
      requestAnimationFrame(fastTick);
    }
  }, [forceComplete, exiting, onDone]);

  const current = PHASES[phaseIndex];

  return (
    <motion.div
      className="fixed inset-0 z-50 flex flex-col items-center justify-center px-4 bg-background"
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* 背景网格 */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '40px 40px',
        }}
      />

      <div className="relative z-10 flex flex-col items-center gap-10">
        {/* ===== 电池 + 脉冲 ===== */}
        <div className="relative w-40 h-56 flex items-center justify-center">
          {/* 外圈脉冲轨道 */}
          {[0, 1, 2, 3].map((i) => (
            <motion.div
              key={i}
              className="absolute rounded-full border border-primary/10"
              style={{ width: 140 + i * 35, height: 140 + i * 35 }}
              animate={{
                opacity: [0.06, 0.18, 0.06],
                scale: [1, 1.04, 1],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                delay: i * 0.6,
                ease: 'easeInOut',
              }}
            />
          ))}

          {/* 电流粒子 */}
          {Array.from({ length: 8 }).map((_, i) => {
            const angle = (i / 8) * 360;
            const delay = i * 0.3;
            return (
              <motion.div
                key={i}
                className="absolute w-1 h-1 rounded-full bg-primary/60"
                style={{ originX: 0.5, originY: 0.5 }}
                animate={{
                  x: [0, Math.cos((angle * Math.PI) / 180) * 90],
                  y: [0, Math.sin((angle * Math.PI) / 180) * 90],
                  opacity: [0, 1, 0],
                  scale: [0.5, 1.2, 0.5],
                }}
                transition={{
                  duration: 2.5,
                  repeat: Infinity,
                  delay,
                  ease: 'easeInOut',
                }}
              />
            );
          })}

          {/* 电池 */}
          <div className="relative w-20 h-32">
            {/* 正极凸头 */}
            <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-8 h-3 rounded-t-md bg-border border border-border/60" />

            {/* 外壳 */}
            <div className="w-full h-full rounded-xl border-2 border-border/60 bg-card/40 backdrop-blur-sm overflow-hidden relative">
              {/* 液体填充 */}
              <div
                className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-primary/70 via-primary/50 to-primary/30 transition-none"
                style={{ height: `${fill}%` }}
              />

              {/* 闪电图标 */}
              <div className="absolute inset-0 flex items-center justify-center">
                <motion.svg
                  width="28"
                  height="28"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="text-foreground drop-shadow-[0_0_6px_rgba(255,255,255,0.3)]"
                  animate={{ opacity: [0.6, 1, 0.6] }}
                  transition={{ duration: 1.2, repeat: Infinity, ease: 'easeInOut' }}
                >
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                </motion.svg>
              </div>

              {/* 电量刻度 */}
              <div className="absolute right-1.5 top-3 bottom-3 flex flex-col justify-between">
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="w-1.5 h-px bg-border/40" />
                ))}
              </div>
            </div>
          </div>

          {/* 阶段指示灯（环绕） */}
          {PHASES.map((_p, i) => {
            const angle = -90 + i * (360 / PHASES.length);
            const rad = (angle * Math.PI) / 180;
            const x = Math.cos(rad) * 72;
            const y = Math.sin(rad) * 72;
            const isActive = i <= phaseIndex;
            return (
              <div
                key={i}
                className="absolute flex items-center justify-center"
                style={{ transform: `translate(${x}px, ${y}px)` }}
              >
                <motion.div
                  className={`w-2.5 h-2.5 rounded-full ${
                    isActive ? 'bg-primary' : 'bg-border/40'
                  }`}
                  animate={
                    isActive
                      ? {
                          boxShadow: [
                            '0 0 0px rgba(var(--primary),0)',
                            '0 0 10px rgba(var(--primary),0.5)',
                            '0 0 0px rgba(var(--primary),0)',
                          ],
                        }
                      : {}
                  }
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
              </div>
            );
          })}
        </div>

        {/* ===== 文字区域 ===== */}
        <div className="text-center space-y-3">
          <h2 className="text-xl font-semibold tracking-wide">双引擎诊断中</h2>
          <AnimatePresence mode="wait">
            <motion.p
              key={phaseIndex}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.35 }}
              className="text-sm text-muted-foreground"
            >
              {current.label}
            </motion.p>
          </AnimatePresence>
        </div>

        {/* ===== 进度条 ===== */}
        <div className="w-56 h-1.5 rounded-full bg-secondary overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-primary/60 to-primary transition-none"
            style={{ width: `${fill}%` }}
          />
        </div>
      </div>
    </motion.div>
  );
}


