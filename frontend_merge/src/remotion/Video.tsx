import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  spring,
  Sequence,
} from 'remotion';

/* ═══════════════════════════════════════════════════════
   ChargeMind 产品演示视频 (60s, 1920×1080, 30fps)
   展示网站全流程：输入 → 追问 → 诊断 → 报告
   ═══════════════════════════════════════════════════════ */

const BG = '#0B0F1A';
const CARD = '#1E293B';
const CARD_BORDER = '#334155';
const PRIMARY = '#3B82F6';
const PRIMARY_GLOW = '#3B82F680';
const TEXT = '#F8FAFC';
const MUTED = '#94A3B8';
const ACCENT = '#10B981';
const RED = '#EF4444';

/* ── 工具：淡入 ── */
const fadeIn = (frame: number, delay = 0, dur = 15) =>
  interpolate(frame, [delay, delay + dur], [0, 1], { extrapolateRight: 'clamp' });

const slideUp = (frame: number, delay = 0, dur = 20, dist = 30) =>
  interpolate(frame, [delay, delay + dur], [dist, 0], { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });

/* ═══════════════════════════════════════════════════════
   场景 1：开场 Logo (0-5s)
   ═══════════════════════════════════════════════════════ */
function SceneOpen() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, from: 0.7, to: 1, config: { damping: 14 } });
  const op = fadeIn(frame, 0, 20);
  return (
    <AbsoluteFill style={{ background: BG, justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ opacity: op, transform: `scale(${s})`, textAlign: 'center' }}>
        <div style={{ fontSize: 110, fontWeight: 800, color: TEXT, letterSpacing: 6 }}>ChargeMind</div>
        <div style={{ marginTop: 20, fontSize: 32, color: MUTED, letterSpacing: 10 }}>充电场站智能诊断平台</div>
      </div>
    </AbsoluteFill>
  );
}

/* ═══════════════════════════════════════════════════════
   场景 2：痛点引入 (5-12s)
   ═══════════════════════════════════════════════════════ */
function ScenePain() {
  const frame = useCurrentFrame();
  const pains = [
    { icon: '💸', text: '利用率低，回本遥遥无期', color: RED },
    { icon: '⚡', text: '桩配多了浪费，配少了流失', color: '#F59E0B' },
    { icon: '📉', text: '定价没谱，被竞品碾压', color: PRIMARY },
  ];
  return (
    <AbsoluteFill style={{ background: BG, justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ fontSize: 44, fontWeight: 700, color: TEXT, marginBottom: 60, opacity: fadeIn(frame, 0, 15) }}>
        你的充电站为什么不赚钱？
      </div>
      <div style={{ display: 'flex', gap: 40 }}>
        {pains.map((p, i) => {
          const d = i * 12;
          return (
            <div key={i} style={{
              opacity: fadeIn(frame, d, 18),
              transform: `translateY(${slideUp(frame, d, 18, 30)}px)`,
              width: 320,
              background: CARD,
              border: `1px solid ${CARD_BORDER}`,
              borderRadius: 16,
              padding: '32px 24px',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>{p.icon}</div>
              <div style={{ fontSize: 24, color: p.color, fontWeight: 600 }}>{p.text}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
}

/* ═══════════════════════════════════════════════════════
   场景 3：全流程概览 (12-18s)
   ═══════════════════════════════════════════════════════ */
function SceneFlow() {
  const frame = useCurrentFrame();
  const steps = [
    { num: '01', title: '自然语言输入', desc: '像聊天一样描述场站' },
    { num: '02', title: '智能追问', desc: 'AI 补齐关键信息' },
    { num: '03', title: '双引擎诊断', desc: '硬数据 × LLM 叙事' },
    { num: '04', title: '诊断报告', desc: '五维雷达 + 提升路径' },
  ];
  return (
    <AbsoluteFill style={{ background: BG, justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ fontSize: 40, fontWeight: 700, color: TEXT, marginBottom: 60, opacity: fadeIn(frame, 0, 15) }}>
        ChargeMind 诊断全流程
      </div>
      <div style={{ display: 'flex', gap: 28 }}>
        {steps.map((s, i) => {
          const d = i * 10;
          return (
            <div key={i} style={{
              opacity: fadeIn(frame, d, 15),
              transform: `translateY(${slideUp(frame, d, 15, 20)}px)`,
              width: 240,
              textAlign: 'center',
            }}>
              <div style={{
                width: 56, height: 56, borderRadius: '50%',
                background: `linear-gradient(135deg, ${PRIMARY}, ${ACCENT})`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                margin: '0 auto 16px', fontSize: 20, fontWeight: 700, color: '#fff',
              }}>{s.num}</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: TEXT, marginBottom: 8 }}>{s.title}</div>
              <div style={{ fontSize: 18, color: MUTED }}>{s.desc}</div>
              {i < steps.length - 1 && (
                <div style={{
                  position: 'absolute',
                  right: -22, top: 28,
                  fontSize: 24, color: PRIMARY,
                  opacity: fadeIn(frame, d + 10, 10),
                }}>→</div>
              )}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
}

/* ═══════════════════════════════════════════════════════
   场景 4：模块1 - 自然语言输入 (18-28s)
   模拟 ConsultDialog 界面：打字机输入 → 点击提交
   ═══════════════════════════════════════════════════════ */
function SceneInput() {
  const frame = useCurrentFrame();
  const text = '我在深圳福田区啤酒小镇核心商圈建了一个大型超充站，紧邻深业上城购物中心，有32个快充桩，总装机功率2400kW……';
  const typedLen = Math.min(Math.floor(frame / 1.32), text.length);
  const typed = text.slice(0, typedLen);
  const showBtnGlow = frame > 72 && frame < 96;
  const btnClicked = frame >= 96;

  // 对话框滑入
  const dialogOp = fadeIn(frame, 3, 11);
  const dialogY = slideUp(frame, 3, 11, 30);

  return (
    <AbsoluteFill style={{ background: BG }}>
      {/* 左侧标题 */}
      <div style={{ position: 'absolute', left: 100, top: '50%', transform: 'translateY(-50%)', width: 400 }}>
        <div style={{ fontSize: 18, color: '#c17f4e', fontWeight: 600, marginBottom: 12, opacity: fadeIn(frame, 0, 7), letterSpacing: 2 }}>
          STEP 01
        </div>
        <div style={{ fontSize: 48, fontWeight: 700, color: TEXT, marginBottom: 20, opacity: fadeIn(frame, 3, 9) }}>
          自然语言输入
        </div>
        <div style={{ fontSize: 24, color: MUTED, lineHeight: 1.6, opacity: fadeIn(frame, 9, 9) }}>
          描述您的充电场站情况，AI 自动解析画像，无需填写冗长表单
        </div>
      </div>

      {/* 右侧模拟 ConsultDialog */}
      <div style={{ position: 'absolute', right: 80, top: '50%', transform: 'translateY(-50%)', width: 640 }}>
        {/* Backdrop */}
        <div style={{
          position: 'absolute',
          inset: -200,
          background: 'rgba(11,15,26,0.5)',
          opacity: dialogOp,
        }} />

        {/* Dialog */}
        <div style={{
          opacity: dialogOp,
          transform: `translateY(${dialogY}px)`,
          position: 'relative',
          background: 'rgba(26,31,54,0.92)',
          border: '1px solid rgba(193,127,78,0.2)',
          borderRadius: 20,
          boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05)',
          overflow: 'hidden',
        }}>
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '32px 32px 16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 40, height: 40, borderRadius: 12, background: 'rgba(193,127,78,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#c17f4e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></svg>
              </div>
              <div>
                <div style={{ fontSize: 20, fontWeight: 600, color: '#fafaf8' }}>开始诊断</div>
                <div style={{ fontSize: 14, color: '#94a3b8', marginTop: 2 }}>描述您的充电场站情况，AI 将为您生成诊断报告</div>
              </div>
            </div>
            <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'rgba(35,40,66,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
            </div>
          </div>

          {/* Body */}
          <div style={{ padding: '16px 32px' }}>
            {/* Textarea */}
            <div style={{ position: 'relative' }}>
              <div style={{
                width: '100%',
                minHeight: 140,
                padding: '16px 20px',
                borderRadius: 12,
                background: 'rgba(35,40,66,0.6)',
                border: '1px solid rgba(193,127,78,0.1)',
                color: '#fafaf8',
                fontSize: 16,
                lineHeight: 1.6,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all',
              }}>
                {typed}
                {typedLen < text.length && (
                  <span style={{ display: 'inline-block', width: 2, height: 20, background: '#c17f4e', marginLeft: 2, verticalAlign: 'middle', animation: 'blink 1s step-end infinite' }} />
                )}
              </div>
              <div style={{ position: 'absolute', bottom: 12, right: 16, fontSize: 12, color: '#64748b' }}>
                {typed.length} 字
              </div>
            </div>

            {/* Quick tags */}
            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              {['深圳南山区快充站', '工业园充电站', '商场地下充电桩'].map((tag, i) => (
                <div key={tag} style={{
                  opacity: fadeIn(frame, 36 + i * 5, 6),
                  padding: '6px 12px',
                  borderRadius: 8,
                  fontSize: 14,
                  color: '#94a3b8',
                  background: 'rgba(35,40,66,0.4)',
                  border: '1px solid rgba(193,127,78,0.05)',
                }}>
                  + {tag}
                </div>
              ))}
            </div>
          </div>

          {/* Footer */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 32px 32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#c17f4e' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>
              使用示例
            </div>

            {/* 提交诊断按钮 */}
            <div style={{ position: 'relative' }}>
              {showBtnGlow && (
                <div style={{
                  position: 'absolute',
                  inset: -4,
                  borderRadius: 12,
                  background: `rgba(193,127,78,${0.3 + Math.sin(frame * 0.3) * 0.2})`,
                  filter: 'blur(8px)',
                }} />
              )}
              <div style={{
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '10px 24px',
                borderRadius: 12,
                background: btnClicked ? '#a06a3d' : '#c17f4e',
                color: '#1a1f36',
                fontSize: 14,
                fontWeight: 700,
                transform: btnClicked ? 'scale(0.96)' : 'scale(1)',
                transition: 'transform 0.15s',
              }}>
                <span>提交诊断</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z"/><path d="m21.854 2.147-10.94 10.939"/></svg>
              </div>
            </div>
          </div>

          {/* Decorative glow */}
          <div style={{ position: 'absolute', top: -80, right: -80, width: 160, height: 160, borderRadius: '50%', background: 'rgba(193,127,78,0.05)', filter: 'blur(40px)', pointerEvents: 'none' }} />
          <div style={{ position: 'absolute', bottom: -80, left: -80, width: 160, height: 160, borderRadius: '50%', background: 'rgba(45,212,191,0.05)', filter: 'blur(40px)', pointerEvents: 'none' }} />
        </div>
      </div>
    </AbsoluteFill>
  );
}

/* ═══════════════════════════════════════════════════════
   场景 5：模块2 - 智能追问 (28-38s)
   ═══════════════════════════════════════════════════════ */
function SceneEnrich() {
  const frame = useCurrentFrame();
  const questions = [
    { label: '装机总功率', value: '1080 kW', active: true },
    { label: '充电桩分布', value: '慢充3 / 快充8 / 超充1', active: false },
    { label: '品牌专用桩', value: '特斯拉3 / 蔚来2', active: false },
    { label: '平均电价', value: '0.85 元/度', active: false },
  ];

  return (
    <AbsoluteFill style={{ background: BG }}>
      {/* 左侧标题 */}
      <div style={{ position: 'absolute', left: 120, top: '50%', transform: 'translateY(-50%)', width: 420 }}>
        <div style={{ fontSize: 18, color: PRIMARY, fontWeight: 600, marginBottom: 12, opacity: fadeIn(frame, 0, 7), letterSpacing: 2 }}>
          STEP 02
        </div>
        <div style={{ fontSize: 48, fontWeight: 700, color: TEXT, marginBottom: 20, opacity: fadeIn(frame, 3, 9) }}>
          智能追问
        </div>
        <div style={{ fontSize: 24, color: MUTED, lineHeight: 1.6, opacity: fadeIn(frame, 9, 9) }}>
          AI 自动判断缺失信息，精准追问。只需回答关键问题，不用填写冗长表单
        </div>
      </div>

      {/* 右侧模拟问卷 */}
      <div style={{ position: 'absolute', right: 120, top: '50%', transform: 'translateY(-50%)', width: 560 }}>
        <div style={{
          opacity: fadeIn(frame, 5, 9),
          transform: `translateY(${slideUp(frame, 5, 9, 20)}px)`,
          background: CARD,
          border: `1px solid ${CARD_BORDER}`,
          borderRadius: 20,
          padding: '36px 32px',
        }}>
          <div style={{ fontSize: 20, fontWeight: 600, color: TEXT, marginBottom: 28 }}>
            补充场站信息 <span style={{ color: MUTED, fontWeight: 400 }}>(3/7)</span>
          </div>
          {questions.map((q, i) => {
            const d = i * 9;
            const isActive = frame > d && frame < d + 30;
            return (
              <div key={i} style={{
                opacity: fadeIn(frame, d, 7),
                transform: `translateX(${slideUp(frame, d, 7, 15)}px)`,
                marginBottom: 16,
                padding: '16px 20px',
                borderRadius: 12,
                border: `1px solid ${isActive ? PRIMARY + '60' : CARD_BORDER}`,
                background: isActive ? `${PRIMARY}10` : 'transparent',
                transition: 'all 0.3s',
              }}>
                <div style={{ fontSize: 16, color: MUTED, marginBottom: 6 }}>{q.label}</div>
                <div style={{ fontSize: 22, fontWeight: 600, color: isActive ? PRIMARY : TEXT }}>
                  {isActive ? <span>{q.value}<span style={{ animation: 'blink 1s infinite' }}>|</span></span> : q.value}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
}

/* ═══════════════════════════════════════════════════════
   场景 6：模块3 - 双引擎诊断 (38-48s)
   ═══════════════════════════════════════════════════════ */
function SceneDiagnose() {
  const frame = useCurrentFrame();
  const fill = interpolate(frame, [0, 105], [0, 100], { extrapolateRight: 'clamp' });

  const phases = [
    { label: '解析场站画像', at: 0 },
    { label: '算法硬算分析', at: 28 },
    { label: 'RAG 检索竞品', at: 56 },
    { label: 'LLM 叙事包装', at: 84 },
  ];

  return (
    <AbsoluteFill style={{ background: BG, justifyContent: 'center', alignItems: 'center' }}>
      {/* 标题 */}
      <div style={{ position: 'absolute', top: 120, left: '50%', transform: 'translateX(-50%)', textAlign: 'center' }}>
        <div style={{ fontSize: 18, color: PRIMARY, fontWeight: 600, marginBottom: 12, opacity: fadeIn(frame, 0, 5), letterSpacing: 2 }}>
          STEP 03
        </div>
        <div style={{ fontSize: 48, fontWeight: 700, color: TEXT, marginBottom: 16, opacity: fadeIn(frame, 2, 6) }}>
          双引擎诊断中
        </div>
        <div style={{ fontSize: 22, color: MUTED, opacity: fadeIn(frame, 5, 6) }}>
          硬数据硬算 + LLM 泛化直觉 · 交叉校验
        </div>
      </div>

      {/* 电池 */}
      <div style={{ marginTop: 40 }}>
        <div style={{ position: 'relative', width: 120, height: 180, margin: '0 auto' }}>
          <div style={{ position: 'absolute', top: -8, left: '50%', transform: 'translateX(-50%)', width: 44, height: 10, borderRadius: '6px 6px 0 0', background: CARD_BORDER }} />
          <div style={{ width: '100%', height: '100%', borderRadius: 16, border: `3px solid ${CARD_BORDER}`, background: `${CARD}80`, overflow: 'hidden', position: 'relative' }}>
            <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, background: `linear-gradient(to top, ${PRIMARY}, ${PRIMARY}60)`, height: `${fill}%` }} />
            <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ fontSize: 48 }}>⚡</div>
            </div>
          </div>
        </div>
      </div>

      {/* 阶段指示 */}
      <div style={{ display: 'flex', gap: 40, marginTop: 50 }}>
        {phases.map((p, i) => {
          const active = frame > p.at;
          return (
            <div key={i} style={{ textAlign: 'center', opacity: fadeIn(frame, p.at, 10) }}>
              <div style={{
                width: 12, height: 12, borderRadius: '50%',
                background: active ? PRIMARY : CARD_BORDER,
                margin: '0 auto 10px',
                boxShadow: active ? `0 0 12px ${PRIMARY_GLOW}` : 'none',
              }} />
              <div style={{ fontSize: 16, color: active ? TEXT : MUTED }}>{p.label}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
}

/* ═══════════════════════════════════════════════════════
   场景 7：模块4 - 诊断报告 (48-58s)
   4个子模块依次全屏滑动展示，模拟实际网页界面
   ═══════════════════════════════════════════════════════ */

/* ── 小工具：SVG 雷达图（手绘版）── */
function RadarMock() {
  const cx = 200, cy = 170, R = 130;
  const dims = ['地段禀赋', '硬件适配', '定价精准', '运营产出', '需求饱和度'];
  const scores = [82, 65, 55, 70, 78];
  const avg = [68, 62, 58, 65, 72];
  const n = 5;
  const pts = (vals: number[]) =>
    vals.map((v, i) => {
      const a = (-Math.PI / 2) + (i * 2 * Math.PI) / n;
      const r = (v / 100) * R;
      return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`;
    }).join(' ');
  const axisPts = Array.from({ length: n }, (_, i) => {
    const a = (-Math.PI / 2) + (i * 2 * Math.PI) / n;
    return { x: cx + R * Math.cos(a), y: cy + R * Math.sin(a), label: dims[i] };
  });
  const gridR = [25, 50, 75, 100];
  return (
    <svg width="100%" height="340" viewBox="0 0 400 340">
      {/* 网格多边形 */}
      {gridR.map((pct) => {
        const gPts = Array.from({ length: n }, (_, i) => {
          const a = (-Math.PI / 2) + (i * 2 * Math.PI) / n;
          const r = (pct / 100) * R;
          return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`;
        }).join(' ');
        return <polygon key={pct} points={gPts} fill="none" stroke="#334155" strokeWidth="1" />;
      })}
      {/* 轴线 */}
      {axisPts.map((p, i) => (
        <line key={i} x1={cx} y1={cy} x2={p.x} y2={p.y} stroke="#334155" strokeWidth="1" />
      ))}
      {/* 区域均值（虚线） */}
      <polygon points={pts(avg)} fill="#64748b" fillOpacity="0.05" stroke="#64748b" strokeWidth="1" strokeDasharray="4 4" />
      {/* 本场站 */}
      <polygon points={pts(scores)} fill="#3B82F6" fillOpacity="0.25" stroke="#3B82F6" strokeWidth="2" />
      {/* 标签 */}
      {axisPts.map((p, i) => (
        <text key={`l${i}`} x={p.x} y={p.y - 10} textAnchor="middle" fill="#94a3b8" fontSize="12">{p.label}</text>
      ))}
      {/* 中心评分 */}
      <text x={cx} y={cy - 4} textAnchor="middle" fill="#F8FAFC" fontSize="32" fontWeight="bold">70</text>
      <text x={cx} y={cy + 16} textAnchor="middle" fill="#94a3b8" fontSize="11">综合评分</text>
    </svg>
  );
}

/* ── 条形图小组件 ── */
function BarRow({ label, supply, demand, subFrame }: { label: string; supply: number; demand: number; subFrame: number }) {
  const wSupply = Math.min(supply, 100);
  const wDemand = Math.min(demand, 100);
  const barOp = fadeIn(subFrame, 14, 18);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
      <span style={{ width: 60, fontSize: 12, color: MUTED }}>{label}</span>
      <div style={{ flex: 1, height: 18, background: 'rgba(51,65,85,0.5)', borderRadius: 4, overflow: 'hidden', position: 'relative' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', background: 'rgba(59,130,246,0.6)', borderRadius: 4, width: `${wSupply * barOp}%`, transition: 'width 0.3s' }} />
        <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', background: 'rgba(16,185,129,0.4)', borderRadius: 4, width: `${wDemand * barOp}%` }} />
      </div>
      <span style={{ width: 90, fontSize: 11, textAlign: 'right' }}>
        <span style={{ color: '#60a5fa' }}>供{supply}%</span>
        <span style={{ color: '#64748b', margin: '0 3px' }}>/</span>
        <span style={{ color: '#34d399' }}>需{demand}%</span>
      </span>
    </div>
  );
}

/* ── 子模块1：五维雷达 + KPI ── */
function SubRadarKPI({ subFrame }: { subFrame: number }) {
  const kpis = [
    { label: '利用率', value: '31.2%', trend: '偏低', color: '#EF4444', trust: '⭐⭐⭐' },
    { label: '服务费', value: '¥0.85/度', trend: '适中', color: '#10B981', trust: '⭐⭐' },
    { label: '充电量', value: '1,560 kWh/日', trend: '良好', color: '#10B981', trust: '⭐⭐⭐' },
    { label: '高峰占比', value: '42%', trend: '集中', color: '#F59E0B', trust: '⭐⭐' },
  ];
  return (
    <div style={{
      opacity: fadeIn(subFrame, 0, 18),
      transform: `translateY(${slideUp(subFrame, 0, 22, 25)}px)`,
      display: 'flex', gap: 24, width: 1200, margin: '0 auto',
    }}>
      {/* 左侧：雷达图卡片 */}
      <div style={{
        flex: 1,
        background: CARD,
        border: `1px solid ${CARD_BORDER}`,
        borderRadius: 20,
        padding: '28px 24px',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 8 }}>
          <span style={{ display: 'inline-block', padding: '6px 16px', borderRadius: 20, background: 'rgba(59,130,246,0.1)', color: PRIMARY, fontSize: 15, fontWeight: 700 }}>
            黄金地段追赶者
          </span>
          <div style={{ fontSize: 13, color: MUTED, marginTop: 6 }}>地段优秀，硬件与定价仍有提升空间</div>
        </div>
        <RadarMock />
        <div style={{ fontSize: 11, color: MUTED, textAlign: 'center', marginTop: -8 }}>
          灰色虚线 = 同区域均值 · 蓝色实线 = 本场站
        </div>
      </div>
      {/* 右侧：KPI 卡片 */}
      <div style={{
        width: 420,
        background: CARD,
        border: `1px solid ${CARD_BORDER}`,
        borderRadius: 20,
        padding: '28px 24px',
      }}>
        <div style={{ fontSize: 18, fontWeight: 600, color: TEXT, marginBottom: 16 }}>关键指标</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {kpis.map((k, i) => (
            <div key={i} style={{
              opacity: fadeIn(subFrame, 10 + i * 8, 10),
              background: 'rgba(30,41,59,0.6)',
              border: `1px solid ${CARD_BORDER}`,
              borderRadius: 12,
              padding: '14px 16px',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontSize: 11, color: MUTED }}>{k.label}</span>
                <span style={{ fontSize: 10, color: MUTED }}>{k.trust}</span>
              </div>
              <div style={{ fontSize: 22, fontWeight: 700, color: TEXT, marginBottom: 6 }}>{k.value}</div>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, fontWeight: 600, color: k.color, background: `${k.color}15`, borderRadius: 6, padding: '3px 8px' }}>
                <span>{k.trend}</span>
              </div>
            </div>
          ))}
        </div>
        <div style={{
          marginTop: 16,
          background: 'rgba(59,130,246,0.05)',
          border: '1px solid rgba(59,130,246,0.1)',
          borderRadius: 10,
          padding: 12,
        }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: PRIMARY }}>💡 综合洞察：</span>
          <span style={{ fontSize: 13, color: TEXT, lineHeight: 1.6 }}>
            地段禀赋优秀但利用率仅31%，定价策略偏保守，建议适度提价并优化功率配比以提升收益。
          </span>
        </div>
      </div>
    </div>
  );
}

/* ── 子模块2：功率错配分析 ── */
function SubPowerMismatch({ subFrame }: { subFrame: number }) {
  const supplyDemand = [
    { label: '慢充', supply: 15, demand: 28 },
    { label: '快充', supply: 52, demand: 48 },
    { label: '超充', supply: 33, demand: 24 },
  ];
  return (
    <div style={{
      opacity: fadeIn(subFrame, 0, 18),
      transform: `translateY(${slideUp(subFrame, 0, 22, 25)}px)`,
      width: 800, margin: '0 auto',
      background: CARD,
      border: `1px solid ${CARD_BORDER}`,
      borderRadius: 20,
      padding: '32px 36px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div style={{ fontSize: 20, fontWeight: 700, color: TEXT }}>⚡ 功率错配分析</div>
        <span style={{ fontSize: 12, color: MUTED }}>⭐⭐⭐ 基于区域车流与桩功率分布</span>
      </div>

      {/* TVD 分数 */}
      <div style={{
        background: 'rgba(245,158,11,0.1)',
        borderRadius: 14,
        padding: '20px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 20,
        opacity: fadeIn(subFrame, 7, 15),
      }}>
        <div>
          <div style={{ fontSize: 12, color: MUTED, marginBottom: 4 }}>功率错配分数 (TVD)</div>
          <div style={{ fontSize: 36, fontWeight: 800, color: '#F59E0B' }}>0.38</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: '#F59E0B' }}>中等错配</div>
          <div style={{ fontSize: 12, color: MUTED }}>慢充供给不足，超充略有过剩</div>
        </div>
      </div>

      {/* 供需对比 */}
      <div style={{ marginBottom: 20, opacity: fadeIn(subFrame, 22, 15) }}>
        <div style={{ fontSize: 12, color: MUTED, marginBottom: 10 }}>功率档供需对比</div>
        {supplyDemand.map((s, i) => (
          <BarRow key={i} label={s.label} supply={s.supply} demand={s.demand} subFrame={subFrame - 15 - i * 5} />
        ))}
        <div style={{ display: 'flex', gap: 20, fontSize: 11, color: MUTED, marginTop: 6 }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: 'rgba(59,130,246,0.6)' }} />供给
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: 'rgba(16,185,129,0.4)' }} />需求
          </span>
        </div>
      </div>

      {/* 主导错配 */}
      <div style={{
        background: 'rgba(51,65,85,0.3)',
        borderRadius: 10,
        padding: '14px 16px',
        opacity: fadeIn(subFrame, 50, 15),
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <span style={{ fontSize: 14 }}>⚡</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: TEXT }}>主导错配</span>
        </div>
        <p style={{ fontSize: 13, color: MUTED, lineHeight: 1.6, margin: 0 }}>
          在当前区域下，慢充桩（0-30kW）<span style={{ color: '#EF4444' }}>供应不足 13%</span>，周边大量通勤车辆偏好低功率夜间充电，建议增配慢充桩或引入小功率分时策略。
        </p>
      </div>
    </div>
  );
}

/* ── 子模块3：品牌与车辆画像 ── */
function SubBrand({ subFrame }: { subFrame: number }) {
  const brands = [
    { name: '特斯拉', share: 32 },
    { name: '比亚迪', share: 28 },
    { name: '蔚来', share: 18 },
    { name: '小鹏', share: 12 },
    { name: '理想', share: 10 },
  ];
  const pileItems = [
    { brand: '特斯拉', count: 3, judgment: '✅ 匹配', reason: '需求32%，配置3台，供给充足' },
    { brand: '比亚迪', count: 0, judgment: '❌ 缺失', reason: '需求28%但无品牌专用桩，流失风险高' },
    { brand: '蔚来', count: 2, judgment: '✅ 匹配', reason: '需求18%，配置2台，覆盖合理' },
    { brand: '小鹏', count: 0, judgment: '— 无需配置', reason: '需求仅12%且低于5%阈值，通用桩即可覆盖' },
  ];
  return (
    <div style={{
      opacity: fadeIn(subFrame, 0, 18),
      transform: `translateY(${slideUp(subFrame, 0, 22, 25)}px)`,
      width: 800, margin: '0 auto',
      background: CARD,
      border: `1px solid ${CARD_BORDER}`,
      borderRadius: 20,
      padding: '32px 36px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div style={{ fontSize: 20, fontWeight: 700, color: TEXT }}>🚗 品牌与车辆画像</div>
        <span style={{ fontSize: 12, color: MUTED }}>⭐⭐⭐</span>
      </div>

      {/* 品牌构成条形图 */}
      <div style={{
        background: 'rgba(51,65,85,0.3)',
        borderRadius: 12,
        padding: '16px 18px',
        marginBottom: 16,
        opacity: fadeIn(subFrame, 7, 15),
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <span style={{ fontSize: 14 }}>🚙</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: TEXT }}>品牌构成</span>
        </div>
        {brands.map((b, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 7 }}>
            <span style={{ width: 50, fontSize: 12, color: MUTED }}>{b.name}</span>
            <div style={{ flex: 1, height: 14, background: 'rgba(51,65,85,0.5)', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{ height: '100%', background: 'rgba(59,130,246,0.6)', borderRadius: 4, width: `${b.share}%`, opacity: fadeIn(subFrame, 10 + i * 5, 8) }} />
            </div>
            <span style={{ width: 36, fontSize: 11, textAlign: 'right', color: TEXT }}>{b.share}%</span>
          </div>
        ))}
        <div style={{ display: 'flex', gap: 16, fontSize: 11, color: MUTED, borderTop: `1px solid ${CARD_BORDER}`, paddingTop: 10, marginTop: 6 }}>
          <span>CR3: 78%</span>
          <span>CR5: 100%</span>
          <span>格局: 寡头垄断</span>
        </div>
      </div>

      {/* 品牌专用桩诊断 */}
      <div style={{
        background: 'rgba(51,65,85,0.3)',
        borderRadius: 12,
        padding: '16px 18px',
        opacity: fadeIn(subFrame, 50, 15),
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
          <span style={{ fontSize: 14 }}>📍</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: TEXT }}>区域品牌画像与用户场站对比</span>
        </div>
        <p style={{ fontSize: 13, color: MUTED, lineHeight: 1.6, margin: '0 0 10px 0' }}>
          周边车流以特斯拉、比亚迪、蔚来三大品牌为主（合计78%），建议针对头部品牌配置专用超充桩。
        </p>
        <div style={{ fontSize: 12, fontWeight: 600, color: TEXT, marginBottom: 8 }}>您场站的品牌专用桩诊断：</div>
        {pileItems.map((item, i) => (
          <div key={i} style={{
            background: 'rgba(11,15,26,0.4)',
            border: `1px solid ${CARD_BORDER}`,
            borderRadius: 8,
            padding: '10px 12px',
            marginBottom: 6,
            opacity: fadeIn(subFrame, 65 + i * 9, 12),
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: TEXT }}>{item.brand}</span>
              <span style={{ fontSize: 12, fontWeight: 700, whiteSpace: 'nowrap' }}>
                {item.count} 台 · <span style={{ color: item.judgment.includes('❌') ? '#EF4444' : item.judgment.includes('✅') ? '#10B981' : MUTED }}>{item.judgment}</span>
              </span>
            </div>
            <p style={{ fontSize: 11, color: MUTED, margin: '4px 0 0 0' }}>{item.reason}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── 子模块4：竞争定位分析 ── */
function SubCompetitive({ subFrame }: { subFrame: number }) {
  return (
    <div style={{
      opacity: fadeIn(subFrame, 0, 18),
      transform: `translateY(${slideUp(subFrame, 0, 22, 25)}px)`,
      width: 900, margin: '0 auto',
      background: CARD,
      border: `1px solid ${CARD_BORDER}`,
      borderRadius: 20,
      padding: '32px 36px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div style={{ fontSize: 20, fontWeight: 700, color: TEXT }}>🎯 竞争定位分析</div>
        <span style={{ fontSize: 12, color: MUTED }}>⭐⭐⭐</span>
      </div>

      <p style={{ fontSize: 14, color: TEXT, lineHeight: 1.6, marginBottom: 16, opacity: fadeIn(subFrame, 5, 10) }}>
        您的场站处于「黄金地段追赶者」定位，容量份额大于实际份额，价格偏保守，存在提价空间。
      </p>

      {/* 容量 vs 实际 */}
      <div style={{
        background: 'rgba(51,65,85,0.3)',
        borderRadius: 12,
        padding: '14px 16px',
        marginBottom: 12,
        opacity: fadeIn(subFrame, 17, 15),
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
          <span style={{ fontSize: 14 }}>⚖️</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: TEXT }}>容量份额 vs 实际份额</span>
          <span style={{ fontSize: 11, color: MUTED, marginLeft: 'auto' }}>⭐⭐</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, textAlign: 'center' }}>
          {[
            { label: '容量份额', val: '18%', color: TEXT },
            { label: '实际份额', val: '14%', color: TEXT },
            { label: '偏差', val: '-4%', color: '#EF4444' },
          ].map((c, i) => (
            <div key={i}>
              <div style={{ fontSize: 11, color: MUTED, marginBottom: 4 }}>{c.label}</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: c.color }}>{c.val}</div>
            </div>
          ))}
        </div>
        <div style={{ fontSize: 12, color: MUTED, textAlign: 'center', marginTop: 8 }}>判断: 实际利用率低于容量预期，存在运营提升空间</div>
      </div>

      {/* 价格结构对比 */}
      <div style={{
        background: 'rgba(51,65,85,0.3)',
        borderRadius: 12,
        padding: '14px 16px',
        marginBottom: 12,
        opacity: fadeIn(subFrame, 36, 15),
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
          <span style={{ fontSize: 14 }}>💰</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: TEXT }}>价格结构对比</span>
          <span style={{ fontSize: 11, color: MUTED, marginLeft: 'auto' }}>⭐⭐⭐</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
          {[
            { label: '低谷', my: '¥0.62', bench: '¥0.68', gap: '-8.8%' },
            { label: '均价', my: '¥0.85', bench: '¥0.92', gap: '-7.6%' },
            { label: '高峰', my: '¥1.12', bench: '¥1.20', gap: '-6.7%' },
          ].map((p, i) => (
            <div key={i} style={{ background: 'rgba(11,15,26,0.4)', border: `1px solid ${CARD_BORDER}`, borderRadius: 8, padding: 10, textAlign: 'center' }}>
              <div style={{ fontSize: 11, color: MUTED, marginBottom: 6 }}>{p.label}</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: TEXT }}>{p.my}/度</div>
              <div style={{ fontSize: 11, color: MUTED, marginTop: 4 }}>竞品 {p.bench} <span style={{ color: '#10B981' }}>{p.gap}</span></div>
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: MUTED, marginTop: 8 }}>
          <span>本场站峰谷比: 1.81</span>
          <span>竞品峰谷比: 1.76</span>
        </div>
      </div>

      {/* 均衡利用率 */}
      <div style={{
        background: 'rgba(51,65,85,0.3)',
        borderRadius: 12,
        padding: '14px 16px',
        opacity: fadeIn(subFrame, 58, 15),
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
          <span style={{ fontSize: 14 }}>📈</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: TEXT }}>均衡利用率区间（推演）</span>
          <span style={{ fontSize: 11, color: MUTED, marginLeft: 'auto' }}>⭐⭐</span>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: TEXT }}>[28.5% — 35.2%]</div>
          <div style={{ fontSize: 11, color: MUTED, marginTop: 6 }}>弹性假设: 0.8-1.2 · 基于当前定价与容量结构推演</div>
        </div>
      </div>
    </div>
  );
}

/* ── 子模块5：详细分析报告 ── */
function SubDetail({ subFrame }: { subFrame: number }) {
  const sections = [
    { type: 'h2', text: '场站概况与核心诊断', delay: 2 },
    { type: 'p', text: '深圳福田啤酒小镇超充站位于福田区核心商圈，紧邻深业上城购物中心，区位优势明显。场站配置 32 台快充桩，总装机功率 2400kW，单桩平均功率 75kW，日均充电量约 1560kWh。', delay: 5 },
    { type: 'h3', text: '地段禀赋', delay: 11 },
    { type: 'p', text: '该场站地处甲级商圈辐射范围内，周边 3 公里覆盖写字楼、购物中心及高密度住宅，日间车流稳定，夜间有商业消费回流支撑。地段禀赋得分 82 分，显著高于同区域均值 68 分。', delay: 14 },
    { type: 'h3', text: '硬件适配', delay: 20 },
    { type: 'p', text: '当前功率配置以快充为主（52%），但区域需求中慢充占比 28%，存在明显的功率结构错配。TVD 错配分数 0.38，处于中等水平，建议评估夜间充电需求，优化功率配比。', delay: 23 },
    { type: 'h2', text: '品牌结构与专用桩配置', delay: 29 },
    { type: 'p', text: '周边车流品牌集中度较高（CR3=78%），特斯拉、比亚迪、蔚来三大品牌占据绝对主导。当前品牌专用桩配置如下：', delay: 32 },
    { type: 'li', text: '特斯拉专用桩 3 台，与 32% 的品牌需求基本匹配', delay: 36 },
    { type: 'li', text: '比亚迪专用桩缺失，28% 的品牌需求未被定向覆盖', delay: 39 },
    { type: 'li', text: '蔚来专用桩 2 台，覆盖 18% 需求，配置合理', delay: 42 },
    { type: 'quote', text: '建议：考虑引入比亚迪合作桩或品牌联名充电桩，以提升品牌车主的场站粘性与充电频次。', delay: 47 },
    { type: 'h2', text: '定价策略与竞争定位', delay: 54 },
    { type: 'p', text: '当前服务费均价 ¥0.85/度，低于竞品基准 ¥0.92/度约 7.6%。峰谷比 1.81 略高于竞品均值 1.76，价差结构已初步形成，但绝对价格水平仍有上调空间。', delay: 57 },
    { type: 'table', delay: 62 },
    { type: 'h2', text: '提升路径建议', delay: 70 },
    { type: 'num', num: '1', text: '短期（1-3 个月）：适度上调服务费至 ¥0.90-0.95/度，测试价格弹性', delay: 73 },
    { type: 'num', num: '2', text: '中期（3-6 个月）：增配 4-6 台慢充桩，优化功率结构错配', delay: 77 },
    { type: 'num', num: '3', text: '长期（6-12 个月）：引入比亚迪品牌合作桩，完善品牌覆盖矩阵', delay: 81 },
    { type: 'p', text: '均衡利用率推演区间为 28.5%-35.2%，当前 31.2% 处于区间下沿，通过上述调整有望提升至 35% 以上，预计月收益可增加 12%-18%。', delay: 86 },
  ];

  const renderItem = (s: typeof sections[0]) => {
    const op = fadeIn(subFrame, s.delay, 16);
    const y = slideUp(subFrame, s.delay, 16, 12);
    const base = { opacity: op, transform: `translateY(${y}px)`, marginBottom: 10 };

    switch (s.type) {
      case 'h2':
        return (
          <div key={s.delay} style={{ ...base, position: 'relative', paddingLeft: 10, marginTop: 18, marginBottom: 10 }}>
            <div style={{ position: 'absolute', left: 0, top: 4, bottom: 4, width: 3, borderRadius: 2, background: 'rgba(59,130,246,0.6)' }} />
            <div style={{ fontSize: 17, fontWeight: 700, color: TEXT }}>{s.text}</div>
          </div>
        );
      case 'h3':
        return (
          <div key={s.delay} style={{ ...base, fontSize: 12, fontWeight: 600, color: PRIMARY, textTransform: 'uppercase', letterSpacing: 1, marginTop: 14, marginBottom: 6 }}>
            {s.text}
          </div>
        );
      case 'p':
        return (
          <div key={s.delay} style={{ ...base, fontSize: 13, color: '#c9cdd3', lineHeight: 1.75, marginBottom: 12 }}>
            {s.text}
          </div>
        );
      case 'li':
        return (
          <div key={s.delay} style={{ ...base, display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 13, color: '#c9cdd3', lineHeight: 1.75, marginBottom: 6 }}>
            <span style={{ marginTop: 6, width: 8, height: 2, borderRadius: 1, background: 'rgba(59,130,246,0.5)', flexShrink: 0 }} />
            <span>{s.text}</span>
          </div>
        );
      case 'quote':
        return (
          <div key={s.delay} style={{ ...base, borderLeft: '2px solid rgba(59,130,246,0.3)', background: 'rgba(59,130,246,0.04)', padding: '10px 14px', borderRadius: '0 8px 8px 0', marginTop: 10, marginBottom: 14 }}>
            <div style={{ fontSize: 13, color: MUTED, fontStyle: 'italic', lineHeight: 1.7 }}>{s.text}</div>
          </div>
        );
      case 'num':
        return (
          <div key={s.delay} style={{ ...base, display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: '#c9cdd3', lineHeight: 1.75, marginBottom: 8 }}>
            <span style={{ width: 20, height: 20, borderRadius: '50%', background: 'rgba(59,130,246,0.15)', color: PRIMARY, fontSize: 11, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 1 }}>{s.num}</span>
            <span>{s.text}</span>
          </div>
        );
      case 'table':
        return (
          <div key={s.delay} style={{ ...base, overflow: 'hidden', borderRadius: 8, border: `1px solid ${CARD_BORDER}`, marginBottom: 14 }}>
            <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'rgba(51,65,85,0.4)' }}>
                  {['指标', '本场站', '竞品均值', '差距'].map((h, i) => (
                    <th key={i} style={{ textAlign: 'left', fontSize: 11, fontWeight: 600, color: TEXT, textTransform: 'uppercase', letterSpacing: 0.5, padding: '8px 12px', borderBottom: `1px solid ${CARD_BORDER}` }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  ['低谷价', '¥0.62', '¥0.68', '-8.8%'],
                  ['均价', '¥0.85', '¥0.92', '-7.6%'],
                  ['高峰价', '¥1.12', '¥1.20', '-6.7%'],
                ].map((row, ri) => (
                  <tr key={ri} style={{ background: ri % 2 === 0 ? 'transparent' : 'rgba(51,65,85,0.15)' }}>
                    {row.map((cell, ci) => (
                      <td key={ci} style={{ padding: '8px 12px', borderBottom: `1px solid rgba(51,65,85,0.3)`, color: ci === 3 ? (cell.startsWith('-') ? '#EF4444' : '#10B981') : '#c9cdd3', fontWeight: ci === 0 ? 600 : 400 }}>{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div style={{
      opacity: fadeIn(subFrame, 0, 18),
      transform: `translateY(${slideUp(subFrame, 0, 22, 25)}px)`,
      width: 860, margin: '0 auto',
      background: CARD,
      border: `1px solid ${CARD_BORDER}`,
      borderRadius: 20,
      overflow: 'hidden',
    }}>
      {/* 标题栏（模拟折叠展开） */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '20px 24px',
        borderBottom: '1px solid rgba(51,65,85,0.5)',
      }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: TEXT }}>📝 详细分析</div>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={MUTED} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m6 9 6 6 6-6"/>
        </svg>
      </div>
      {/* 内容区 */}
      <div style={{ padding: '20px 28px 28px', maxHeight: 580, overflow: 'hidden' }}>
        {sections.map(renderItem)}
      </div>
    </div>
  );
}

function SceneReport() {
  const frame = useCurrentFrame();

  // 5个子模块时间区间（每个展示约 2.5-3.5s，动画放慢）
  const phases = [
    { start: 15,  end: 105, render: (f: number) => <SubRadarKPI subFrame={f} /> },
    { start: 95,  end: 185, render: (f: number) => <SubPowerMismatch subFrame={f} /> },
    { start: 175, end: 265, render: (f: number) => <SubBrand subFrame={f} /> },
    { start: 255, end: 345, render: (f: number) => <SubCompetitive subFrame={f} /> },
    { start: 335, end: 450, render: (f: number) => <SubDetail subFrame={f} /> },
  ];

  // 计算当前活跃的子模块（带交叉淡入淡出）
  const active = phases.filter((p, idx) => {
    const overlap = idx < phases.length - 1 ? 10 : 0;
    return frame >= p.start - 5 && frame < p.end + overlap;
  });

  return (
    <AbsoluteFill style={{ background: BG }}>
      {/* 固定标题 */}
      <div style={{ position: 'absolute', top: 40, left: '50%', transform: 'translateX(-50%)', textAlign: 'center', zIndex: 10 }}>
        <div style={{ fontSize: 16, color: PRIMARY, fontWeight: 600, marginBottom: 8, opacity: fadeIn(frame, 0, 12), letterSpacing: 2 }}>
          STEP 04
        </div>
        <div style={{ fontSize: 40, fontWeight: 700, color: TEXT, marginBottom: 8, opacity: fadeIn(frame, 5, 15) }}>
          诊断报告
        </div>
        <div style={{ fontSize: 18, color: MUTED, opacity: fadeIn(frame, 10, 12) }}>
          硬核数据 + 可落地的提升路径
        </div>
      </div>

      {/* 子模块渲染区域 */}
      <div style={{ position: 'absolute', top: 170, left: 0, right: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {active.map((p, i) => {
          const subFrame = frame - p.start;
          // 退场：最后10帧淡出
          const exitStart = p.end - p.start - 10;
          const exitOp = subFrame > exitStart ? 1 - (subFrame - exitStart) / 10 : 1;
          return (
            <div key={i} style={{ position: 'absolute', width: '100%', opacity: Math.max(0, exitOp) }}>
              {p.render(Math.max(0, subFrame))}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
}

/* ═══════════════════════════════════════════════════════
   场景 8：结尾 CTA (58-60s)
   ═══════════════════════════════════════════════════════ */
function SceneEnd() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, from: 0.85, to: 1, config: { damping: 12 } });
  return (
    <AbsoluteFill style={{ background: BG, justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ opacity: fadeIn(frame, 0, 15), transform: `scale(${s})`, textAlign: 'center' }}>
        <div style={{ fontSize: 80, fontWeight: 800, color: TEXT, letterSpacing: 4, marginBottom: 24 }}>ChargeMind</div>
        <div style={{ fontSize: 32, color: MUTED, marginBottom: 40 }}>让数据为你的充电站说话</div>
        <div style={{
          display: 'inline-block',
          background: `linear-gradient(90deg, ${PRIMARY}, ${ACCENT})`,
          borderRadius: 12,
          padding: '16px 48px',
          fontSize: 24,
          fontWeight: 700,
          color: '#fff',
        }}>
          立即体验智能诊断 →
        </div>
      </div>
    </AbsoluteFill>
  );
}

/* ═══════════════════════════════════════════════════════
   主视频
   ═══════════════════════════════════════════════════════ */
export default function ChargeMindVideo() {
  return (
    <AbsoluteFill>
      <Sequence from={0}    durationInFrames={30}> <SceneOpen /></Sequence>
      <Sequence from={30}   durationInFrames={45}> <ScenePain /></Sequence>
      <Sequence from={75}   durationInFrames={60}> <SceneFlow /></Sequence>
      <Sequence from={135}  durationInFrames={180}><SceneInput /></Sequence>
      <Sequence from={315}  durationInFrames={180}><SceneEnrich /></Sequence>
      <Sequence from={495}  durationInFrames={120}><SceneDiagnose /></Sequence>
      <Sequence from={615}  durationInFrames={450}><SceneReport /></Sequence>
      <Sequence from={1065} durationInFrames={60}> <SceneEnd /></Sequence>
    </AbsoluteFill>
  );
}
