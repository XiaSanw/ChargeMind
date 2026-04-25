# ChargeMind 前端合并说明文档

本文档说明 `frontend`（主诊断平台）与 `frontend_clq`（Landing Page）是如何合并为 `frontend_merge` 的。

---

## 一、原始前端定位

### 1.1 `frontend` — 充电场站智能诊断平台（产品内核）

- **技术栈**：React 19 + TypeScript + Vite + Tailwind CSS v4 + Recharts
- **核心流程**：自然语言输入 → 信息补全问答 → 诊断报告
  - `StationInputPage`：文本输入，调用 `extractProfile` API 提取场站参数
  - `EnrichPage`：动态问答补全缺失字段（单选/多选/数字/文本）
  - `ReportPage`：数据可视化报告（雷达图、KPI、竞品对标、异常识别等）
- **路由方式**：`DiagnosisContext` 全局状态管理，`currentPage` 字段控制页面切换
- **视觉风格**：shadcn/ui 风格，CSS 变量主题，蓝色主色调（`#3b82f6`）
- **关键依赖**：`axios`、`recharts`、`react-markdown`、`remark-gfm`

### 1.2 `frontend_clq` — ChargeMind 营销落地页（品牌外骨骼）

- **技术栈**：React 19 + TypeScript + Vite + Tailwind CSS v4 + **Framer Motion**
- **核心功能**：单屏品牌展示 + 输入弹窗
  - `HeroSection`：大标题 "ChargeMind"、价值主张、CTA 按钮、动态粒子背景
  - `ConsultDialog`：玻璃拟态弹窗，自然语言输入，字数统计，快捷标签
  - `ParticleBackground`：Canvas 300 粒子浮动动画
- **视觉风格**：深 Navy 背景 + Copper/Teal 强调色，玻璃拟态（glassmorphism），衬线标题字体 Fraunces
- **关键依赖**：`framer-motion`

---

## 二、合并目标

将 Landing Page 的**震撼首屏与输入弹窗**作为主入口，保留诊断平台的**完整业务逻辑与数据可视化**，形成统一的单应用架构：

```
用户访问
  → LandingPage（Hero 首屏 + ConsultDialog 弹窗输入）
    → EnrichPage（信息补全）
      → ReportPage（诊断报告）
        → 重新诊断 → 回到 LandingPage 弹窗
```

**核心原则**：
1. 以 `frontend` 为底座，尽量不动原有诊断逻辑
2. 删除冗余的 `StationInputPage`，让 `ConsultDialog` 成为唯一输入入口
3. 视觉层保留 Landing 页设计，业务层复用诊断平台逻辑

---

## 三、合并步骤详解

### Step 1：基础复制（保留原框架）

```bash
# 复制 frontend 完整目录结构（排除 node_modules / dist）
rsync -av --exclude=node_modules --exclude=dist frontend/ frontend_merge/

# 复制 frontend_clq 的 landing 组件
mkdir -p frontend_merge/src/components/landing
cp frontend_clq/src/components/HeroSection.tsx      frontend_merge/src/components/landing/
cp frontend_clq/src/components/ConsultDialog.tsx    frontend_merge/src/components/landing/
cp frontend_clq/src/components/ParticleBackground.tsx frontend_merge/src/components/landing/

# 复制静态资源
cp frontend_clq/src/assets/* frontend_merge/src/assets/
```

### Step 2：样式合并（`src/index.css`）

保留 `frontend` 的 shadcn 主题变量，追加 `frontend_clq` 的 Landing 页设计系统：

| 追加内容 | 来源 |
|---------|------|
| `--color-navy`、`--color-copper`、`--color-teal`、`--color-cream` | `frontend_clq` 主题色 |
| `--font-heading`（Fraunces）、`--font-body`（Source Sans 3） | `frontend_clq` 字体 |
| `.glass-card`、`.glass-dialog`、`.glow-copper`、`.glow-teal` | `frontend_clq` utilities |

**注意**：只合并 `@theme` 变量和 `@layer utilities`，不合并 `frontend_clq` 的 `body` / `h1-h6` 全局样式，避免影响诊断报告页的视觉。

### Step 3：HTML 入口合并（`index.html`）

保留原有 `meta` 和 `favicon`，追加 Google Fonts 预连接与加载：

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Fraunces:...&family=Source+Sans+3:...&display=swap" rel="stylesheet" />
```

### Step 4：`ConsultDialog` 内核替换（核心改动）

保留 `frontend_clq` 的**视觉外壳**（Framer Motion 动画、glass-dialog、排版），替换内部逻辑为 `StationInputPage` 的**业务内核**：

| 维度 | 改动前（纯前端_clq） | 改动后（合并版） |
|------|---------------------|-----------------|
| 数据提交 | `setTimeout` 模拟假提交 | 真实调用 `extractProfile()` API |
| 状态管理 | 本地 `useState` | 接入 `useDiagnosis` + `setProfile` + `setCurrentPage` |
| 示例填充 | ❌ 无 | ✅ `EXAMPLE_TEXTS` 数组 + "使用示例"按钮 |
| 错误处理 | ❌ 无 | ✅ 弹窗内红色错误提示 + `setError` 同步 |
| 跳转逻辑 | `onSubmit` 回调给父级 | 成功后直接 `setCurrentPage('enrich')` |
| 草稿恢复 | ❌ 关闭即丢 | ✅ 关闭时保存到 `landingInput`， reopen 时恢复 |

**关键代码片段**：

```tsx
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
    setTimeout(() => setCurrentPage('enrich'), 400); // 等退场动画
  } catch (err) {
    const msg = err instanceof Error ? err.message : '解析失败，请重试';
    setLocalError(msg);
    setError(msg);
  } finally {
    setLoading(false);
  }
}, [...]);
```

### Step 5：新建 `LandingPage` 页面组件

将 `frontend_clq` 的 `App.tsx` 逻辑（`HeroSection` + `ConsultDialog`）封装为 `pages/LandingPage.tsx`：

```tsx
export default function LandingPage() {
  const { autoOpenDialog, clearAutoOpenDialog } = useDiagnosis();
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // 重新诊断后自动打开弹窗
  useEffect(() => {
    if (autoOpenDialog) {
      setIsDialogOpen(true);
      clearAutoOpenDialog();
    }
  }, [autoOpenDialog, clearAutoOpenDialog]);

  return (
    <div className="relative min-h-screen bg-navy">
      <HeroSection onStartConsult={() => setIsDialogOpen(true)} />
      <ConsultDialog isOpen={isDialogOpen} onClose={() => setIsDialogOpen(false)} />
    </div>
  );
}
```

### Step 6：路由精简（`App.tsx`）

删除 `StationInputPage` 及其路由分支，最终只保留三页：

```tsx
function PageRouter() {
  const { currentPage } = useDiagnosis();
  if (currentPage === 'landing') return <LandingPage />;
  return (
    <div className="min-h-screen bg-background text-foreground">
      {currentPage === 'enrich' && <EnrichPage />}
      {currentPage === 'report' && <ReportPage />}
    </div>
  );
}
```

### Step 7：`DiagnosisContext` 状态管理调整

#### 7.1 删除有害的自动跳转 `useEffect`

`frontend` 原有一段用于"刷新后恢复诊断进度"的 `useEffect`：

```tsx
// ❌ 已删除（导致刷新/重启后强制进入加载界面）
useEffect(() => {
  if (profile && currentPage === 'landing' && !diagnoseResult) {
    setCurrentPage('enrich');
  }
}, []);
```

**删除原因**：`profile` 被持久化到 `localStorage`，但 `diagnoseResult` 没有。刷新后 `profile` 有值、`diagnoseResult` 为空，该 effect 误判为"诊断中断需恢复"，强制跳转到 `EnrichPage` → `runDiagnose()` → `ReportPage` LoadingOverlay，导致用户**永远回不到 LandingPage**。

#### 7.2 `reset()` 目标改为 `'landing'`

```tsx
const reset = useCallback(() => {
  setProfileState(null);
  setDiagnoseResult(null);
  setCurrentPage('landing');      // 原为 'input'，现改为 'landing'
  setIsDiagnosing(false);
  setError(null);
  setLandingInputState(null);
  setAutoOpenDialog(true);        // 新增：重新诊断后自动打开弹窗
  localStorage.removeItem(STORAGE_KEY);
}, []);
```

#### 7.3 新增 `autoOpenDialog` 状态

用于"重新诊断"后自动唤起 `ConsultDialog`，避免用户回到 LandingPage 后还需手动点击"开始诊断"。

### Step 8：依赖安装

```bash
cd frontend_merge
npm install
# 新增依赖：framer-motion（已由 package.json 声明）
```

### Step 9：构建验证

```bash
npm run build
# ✅ tsc -b && vite build 成功
# dist/ 产物生成
```

---

## 四、最终目录结构

```
frontend_merge/
├── public/
│   ├── favicon.svg
│   └── icons.svg
├── src/
│   ├── assets/                          # 来自 frontend_clq
│   │   ├── hero.png
│   │   ├── react.svg
│   │   └── vite.svg
│   ├── components/
│   │   ├── dashboard/                   # 来自 frontend（报告页组件）
│   │   │   ├── BenchmarkChart.tsx
│   │   │   ├── BrandAnalysisCard.tsx
│   │   │   ├── CompetitivePositionCard.tsx
│   │   │   ├── DetailSection.tsx
│   │   │   ├── Headline.tsx
│   │   │   ├── KPICard.tsx
│   │   │   ├── KPICards.tsx
│   │   │   ├── PathCard.tsx
│   │   │   ├── PathCards.tsx
│   │   │   ├── PowerMismatchCard.tsx
│   │   │   └── RadarChart.tsx
│   │   └── landing/                     # 来自 frontend_clq（Landing 页组件）
│   │       ├── ConsultDialog.tsx        # ⭐ 核心改动：保留视觉，替换业务逻辑
│   │       ├── HeroSection.tsx
│   │       └── ParticleBackground.tsx
│   ├── data/
│   │   └── mockDiagnosis.ts             # 来自 frontend
│   ├── lib/
│   │   ├── adaptLegacyToDashboard.ts    # 来自 frontend
│   │   └── api.ts                       # 来自 frontend
│   ├── pages/
│   │   ├── EnrichPage.tsx               # 来自 frontend（未改动）
│   │   ├── LandingPage.tsx              # ⭐ 新增：Landing 入口页
│   │   └── ReportPage.tsx               # 来自 frontend（未改动）
│   ├── store/
│   │   └── DiagnosisContext.tsx         # ⭐ 核心改动：删除自动跳转，新增 autoOpenDialog
│   ├── types/
│   │   ├── dashboard.ts                 # 来自 frontend
│   │   └── diagnosis.ts                 # ⭐ 扩展 PageType：增加 'landing'
│   ├── App.tsx                          # ⭐ 精简路由：删除 StationInputPage
│   ├── index.css                        # ⭐ 合并样式：追加 Landing 主题变量
│   ├── main.tsx                         # 来自 frontend（未改动）
│   └── vite-env.d.ts                    # 来自 frontend
├── index.html                           # ⭐ 追加 Google Fonts
├── package.json                         # ⭐ 新增 framer-motion
├── vite.config.ts                       # 来自 frontend（未改动）
├── tsconfig.json / tsconfig.app.json    # 来自 frontend（未改动）
└── MERGE.md                             # 本文档
```

---

## 五、关键文件改动汇总

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| `src/App.tsx` | 修改 | 删除 `StationInputPage` 引用与 `input` 路由分支 |
| `src/store/DiagnosisContext.tsx` | 修改 | 删除自动跳转 useEffect；`reset()` 回 `'landing'`；新增 `autoOpenDialog` 状态 |
| `src/pages/LandingPage.tsx` | **新增** | 组合 `HeroSection` + `ConsultDialog`，支持自动打开弹窗 |
| `src/components/landing/ConsultDialog.tsx` | **新增+大改** | 基于 `frontend_clq` 视觉，内部替换为 `StationInputPage` 业务逻辑 |
| `src/index.css` | 修改 | 合并 Landing 页主题色、字体、utilities |
| `index.html` | 修改 | 加载 Fraunces + Source Sans 3 字体 |
| `package.json` | 修改 | 新增 `framer-motion` 依赖 |
| `src/types/diagnosis.ts` | 修改 | `PageType` 增加 `'landing'` |
| `src/pages/StationInputPage.tsx` | **删除** | 功能被 `ConsultDialog` 完全取代 |

---

## 六、合并后的用户旅程

```
┌─────────────────────────────────────────────────────────────────┐
│  LandingPage（HeroSection + ParticleBackground）                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ConsultDialog（玻璃拟态弹窗）                          │   │
│  │  • 自然语言输入 + 字数统计 + 快捷标签                    │   │
│  │  • 使用示例（随机填充）                                  │   │
│  │  • 真实 API 提交 → 成功 → 自动跳转                      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                     EnrichPage（信息补全问答）
                              ↓
                     ReportPage（可视化诊断报告）
                              ↓
                        点击"重新诊断"
                              ↓
                     reset() → 回到 LandingPage
                     弹窗自动打开，可直接重新输入
```

---

## 七、已知问题与解决记录

### 问题 1：刷新/重启后卡在"双引擎诊断中"加载界面

**现象**：诊断完成后刷新网页或重启 dev server，页面自动进入 `ReportPage` 的 `LoadingOverlay`，无法回到 LandingPage。

**根因**：`DiagnosisContext` 中原有一个 `useEffect`，在 Provider 挂载时检测到 `localStorage` 中有旧 `profile` 且 `diagnoseResult` 为空，就强制 `setCurrentPage('enrich')`，触发自动诊断流程。

**解决**：**删除该 `useEffect`**。刷新后用户始终停留在 `LandingPage`，不再自作主张恢复诊断进度。

### 问题 2：点击"重新诊断"后弹窗未自动打开

**现象**：`reset()` 后回到 `LandingPage`，但 `ConsultDialog` 关闭，需要用户再点一次"开始诊断"。

**解决**：在 `DiagnosisContext` 中新增 `autoOpenDialog` 布尔状态，`reset()` 时设为 `true`；`LandingPage` 通过 `useEffect` 检测并自动打开弹窗。

---

## 八、如何运行

```bash
cd frontend_merge
npm install
npm run dev        # 开发模式，端口 5173
npm run build      # 生产构建
npm run preview    # 预览生产构建
```

后端 API 代理配置在 `vite.config.ts` 中：

```ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```
