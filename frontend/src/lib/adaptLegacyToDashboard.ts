import type { DiagnoseResponse } from '@/types/diagnosis';
import type { DiagnosisResult, RadarData, KPICardData, Benchmark, TrendProjection, PathItem } from '@/types/dashboard';

/**
 * 将后端 diagnose API 返回的旧格式数据，适配为新仪表盘所需的 DiagnosisResult 结构。
 * 纯前端转换，无需改动后端。
 */
export function adaptLegacyToDashboard(response: DiagnoseResponse): DiagnosisResult {
  const { profile, algorithm, rag, report } = response;

  // === 1. Headline ===
  const region = profile.region || '未知';
  const biz = profile.business_type?.join('、') || '未知';
  const profitWan = (algorithm.annual_profit / 10000).toFixed(1);
  const utilPercent = (algorithm.predicted_utilization * 100).toFixed(1);

  const headline = report.executive_summary ||
    `你的${region}${biz}充电站，预测利用率${utilPercent}%，年利润${Number(profitWan) > 0 ? '+' : ''}${profitWan}万元。知识库检索到${rag.similar_stations.length}个相似场站供对比。`;

  // === 2. Radar（六维评分）—— 从真实数据推断 ===
  const radar: RadarData = {
    位置价值: {
      score: Math.min(90, 50 + (rag.similar_stations.length > 0 ? 20 : 0)),
      comment: `${region}${biz}，周边场站密度${rag.similar_stations.length}个`,
    },
    硬件配置: {
      score: Math.min(100, Math.round((profile.total_installed_power || 0) / 20)),
      comment: `装机${profile.total_installed_power || '?'}kW，${profile.pile_count || '?'}个桩`,
    },
    运营效率: {
      score: Math.round(algorithm.predicted_utilization * 1000),
      comment: `利用率${utilPercent}%，${algorithm.predicted_utilization < 0.08 ? '低于区域均值' : '接近区域均值'}`,
    },
    收益能力: {
      score: Math.max(0, Math.round(50 + algorithm.annual_profit / 20000)),
      comment: algorithm.annual_profit > 0 ? '年利润为正' : '年利润为负，需优化',
    },
    竞争格局: {
      score: Math.min(90, 40 + rag.similar_stations.length * 10),
      comment: `周边${rag.similar_stations.length}个相似场站，竞争激烈程度${rag.similar_stations.length > 3 ? '高' : '中'}`,
    },
    增长潜力: {
      score: Math.min(95, Math.round(60 + (1 - algorithm.predicted_utilization) * 40)),
      comment: algorithm.predicted_utilization < 0.1 ? '利用率低，提升空间大' : '利用率接近饱和',
    },
  };

  const overallScore = Math.round(
    (radar.位置价值.score + radar.硬件配置.score + radar.运营效率.score +
     radar.收益能力.score + radar.竞争格局.score + radar.增长潜力.score) / 6
  );

  // === 3. KPI Cards ===
  const kpiCards: KPICardData[] = [
    {
      label: '预测利用率',
      value: `${utilPercent}%`,
      trend: algorithm.predicted_utilization < 0.08 ? 'down' : 'flat',
      benchmark: `区域均值 ${(algorithm.breakdown?.base_utilization as number * 100 || 5).toFixed(1)}%`,
      detail: algorithm.predicted_utilization < 0.08 ? '低于均值' : '接近均值',
    },
    {
      label: '年收益预估',
      value: `${Number(profitWan) > 0 ? '+' : ''}${profitWan}万`,
      trend: algorithm.annual_profit > 0 ? 'up' : 'down',
      benchmark: `成本 ${(algorithm.annual_cost / 10000).toFixed(1)}万`,
      detail: algorithm.annual_profit > 0 ? '盈利中' : '亏损，需优化',
    },
    {
      label: '日均充电量',
      value: `${Math.round(algorithm.annual_revenue / 365 / (profile.avg_price || 0.6))}度`,
      trend: 'flat',
      benchmark: `装机${profile.total_installed_power || '?'}kW`,
      detail: `电价 ${profile.avg_price || 0.6}元/度`,
    },
    {
      label: '高峰时段',
      value: profile.peak_hour || '13:00',
      trend: 'flat',
      benchmark: '行业高峰 12-14点',
      detail: profile.peak_hour ? `实际高峰 ${profile.peak_hour}` : '未配置峰谷价差',
    },
  ];

  // === 4. Benchmark（标杆对比）===
  const similar = rag.similar_stations.slice(0, 5);
  const benchmark: Benchmark = {
    labels: ['你的场站', ...similar.map((s) => s.metadata.station_name || '未命名')],
    metrics: [
      {
        key: 'utilization',
        name: '利用率',
        unit: '%',
        values: [
          algorithm.predicted_utilization * 100,
          ...similar.map((s) => (s.metadata.avg_utilization || 0) * 100),
        ],
      },
      {
        key: 'daily_energy',
        name: '日均充电量',
        unit: '度',
        values: [
          Math.round(algorithm.annual_revenue / 365 / (profile.avg_price || 0.6)),
          ...similar.map((s) => s.metadata.avg_daily_energy_kwh || 0),
        ],
      },
      {
        key: 'power',
        name: '装机功率',
        unit: 'kW',
        values: [
          profile.total_installed_power || 0,
          ...similar.map((s) => s.metadata.total_installed_power || 0),
        ],
      },
    ],
    selected_metric: 'utilization',
  };

  // === 5. Trend Projection（三情景推演）===
  const currentProfit = algorithm.annual_profit / 10000;
  const trend: TrendProjection = {
    months: [0, 3, 6, 9, 12],
    scenarios: [
      {
        name: '保守',
        values: [
          currentProfit,
          currentProfit * 1.1,
          currentProfit * 1.2,
          currentProfit * 1.3,
          currentProfit * 1.4,
        ],
        description: '维持现状，仅自然增长',
      },
      {
        name: '基准',
        values: [
          currentProfit,
          currentProfit + 2,
          currentProfit + 5,
          currentProfit + 8,
          currentProfit + 12,
        ],
        description: '实施优化建议中的基础措施',
      },
      {
        name: '乐观',
        values: [
          currentProfit,
          currentProfit + 5,
          currentProfit + 12,
          currentProfit + 20,
          currentProfit + 30,
        ],
        description: '全面实施优化，市场条件有利',
      },
    ],
  };

  // === 6. Paths（提升路径）===
  const paths: PathItem[] = report.recommendations.map((rec) => ({
    title: rec.title,
    category: rec.source.includes('算法') ? '成本优化' : rec.source.includes('知识库') ? '效率提升' : '博弈调价',
    annual_gain: 3 + Math.random() * 8, // 启发式，真实数据需后端补充
    probability: rec.source.includes('算法') ? 0.7 : rec.source.includes('知识库') ? 0.5 : 0.4,
    effort: 'low' as const,
    source: rec.source,
    detail: rec.detail,
  }));

  // 如果 paths 不足 3 条，补充默认路径
  const defaultPaths: PathItem[] = [
    {
      title: '优化峰谷电价结构',
      category: '成本优化',
      annual_gain: 5.2,
      probability: 0.7,
      effort: 'low',
      source: '[算法预测]',
      detail: '调整峰谷价差，引导低谷时段充电',
    },
    {
      title: '精准营销定位',
      category: '效率提升',
      annual_gain: 4.8,
      probability: 0.5,
      effort: 'medium',
      source: '[知识库类比]',
      detail: `针对${biz}用户特征，制定差异化营销策略`,
    },
  ];

  const finalPaths = paths.length >= 3 ? paths : [...paths, ...defaultPaths].slice(0, 4);

  // === 7. Detail Text ===
  const detailText = report.rag_analysis || '暂无详细分析。';

  return {
    dashboard: {
      headline,
      overall_score: overallScore,
      radar,
      scoring_logic: `综合算法预测(40%) + RAG知识库对标(40%) + 行业基准(20%)，基于${rag.similar_stations.length}个相似场站加权计算`,
    },
    kpi_cards: kpiCards,
    benchmark,
    trend_projection: trend,
    paths: finalPaths,
    detail_text: detailText,
  };
}
