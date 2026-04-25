import { motion } from 'framer-motion';
import { Zap, ArrowRight, BatteryCharging } from 'lucide-react';
import ParticleBackground from './ParticleBackground';

interface HeroSectionProps {
  onStartConsult: () => void;
}

export default function HeroSection({ onStartConsult }: HeroSectionProps) {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden">
      {/* Particle background */}
      <ParticleBackground />

      {/* Background ambient glows */}
      <div className="absolute inset-0 pointer-events-none z-0">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-teal/5 blur-[100px]" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full bg-copper/5 blur-[80px]" />
        {/* Grid pattern */}
        <div
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `linear-gradient(rgba(45,212,191,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(45,212,191,0.5) 1px, transparent 1px)`,
            backgroundSize: '80px 80px',
          }}
        />
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-3xl mx-auto text-center">
        {/* Top badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card mb-10"
        >
          <BatteryCharging className="w-4 h-4 text-teal" />
          <span className="text-sm text-slate-400 tracking-wide">聚焦电力市场 · 充电场站智能诊断</span>
        </motion.div>

        {/* Main heading - ChargeMind */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
          className="text-6xl sm:text-7xl lg:text-8xl font-light text-cream leading-[1.05] tracking-tight mb-6"
          style={{ fontFamily: 'var(--font-heading)' }}
        >
          Charge
          <span className="text-teal">Mind</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="text-lg sm:text-xl text-slate-400 leading-relaxed max-w-2xl mx-auto mb-14"
        >
          算电协同时代，用
          <span className="text-teal">算法预测</span>
          与
          <span className="text-copper">知识库类比</span>
          双引擎，
          <br className="hidden sm:block" />
          为充电运营商破解选址失误、利用率低迷、收益错配三大困局
        </motion.p>

        {/* CTA Button */}
        <motion.button
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.45, ease: [0.16, 1, 0.3, 1] }}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.98 }}
          onClick={onStartConsult}
          className="group relative inline-flex items-center gap-3 px-10 py-4 rounded-full bg-copper text-navy font-semibold text-lg tracking-wide transition-all duration-300 hover:bg-copper-light hover:glow-copper cursor-pointer"
        >
          <Zap className="w-5 h-5" />
          <span>开始诊断</span>
          <ArrowRight className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1" />
        </motion.button>

        {/* Bottom hints */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.8 }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-8 text-sm text-slate-500"
        >
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-teal animate-pulse" />
            接入深圳 10,000+ 场站数据
          </span>
          <span className="hidden sm:inline text-slate-600">|</span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-copper animate-pulse" />
            30 秒生成诊断报告
          </span>
        </motion.div>
      </div>

      {/* Decorative bottom gradient */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-navy to-transparent pointer-events-none z-[2]" />
    </section>
  );
}
