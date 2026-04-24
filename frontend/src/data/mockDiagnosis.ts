import type { DiagnosisResult } from '@/types/dashboard';

export const mockDiagnosis: DiagnosisResult = {
  dashboard: {
    headline: '你的场站年收益预估 -8.3 万元，对标场站最高 45.2 万，差距 53.5 万。综合运营评分 62 分（满分 100）。',
    overall_score: 62,
    radar: {
      位置价值: { score: 70, comment: '周边 POI 密度高，但充电供给过剩' },
      硬件配置: { score: 55, comment: '快充占比过高，慢充补充不足' },
      运营效率: { score: 38, comment: '利用率 5.2%，低于区域均值 7.4%' },
      收益能力: { score: 32, comment: '年利润为负，主要受租金拖累' },
      竞争格局: { score: 60, comment: '2km 内 3 家竞品，价格无优势' },
      增长潜力: { score: 75, comment: '夜间低谷利用率有 3 倍提升空间' },
    },
    scoring_logic: '综合算法预测(30%) + RAG知识库对标(50%) + 行业基准(20%)加权计算',
  },
  kpi_cards: [
    { label: '预测利用率', value: '5.2%', trend: 'down', benchmark: '区域均值 7.4%', detail: '低于 60% 同类场站' },
    { label: '年收益预估', value: '-8.3万', trend: 'down', benchmark: '对标最高 45.2万', detail: '租金占比过高' },
    { label: '日均充电量', value: '240度', trend: 'flat', benchmark: '对标均值 580度', detail: '午间集中，低谷闲置' },
    { label: '高峰时段', value: '13:00', trend: 'flat', benchmark: '行业高峰 12-14点', detail: '峰谷比 4:1，极不均衡' },
  ],
  benchmark: {
    labels: ['你的场站', '小鹏S4超快充', '南山科技园站', '来福士广场站', '福田枢纽站', '区域均值'],
    metrics: [
      { key: 'utilization', name: '利用率', unit: '%', values: [5.2, 25.9, 11.2, 1.2, 18.5, 7.4] },
      { key: 'annual_profit', name: '年收益', unit: '万元', values: [-8.3, 45.2, 18.6, -15.1, 32.0, 5.2] },
      { key: 'daily_energy', name: '日均充电量', unit: '度', values: [240, 1240, 580, 89, 920, 420] },
    ],
    selected_metric: 'utilization',
  },
  trend_projection: {
    months: [0, 3, 6, 9, 12],
    scenarios: [
      { name: '保守', values: [-8.3, -5.1, -2.0, 0.5, 1.5], description: '仅实施峰谷电价优化' },
      { name: '基准', values: [-8.3, -2.5, 3.0, 6.0, 8.5], description: '峰谷优化 + 基础引流措施' },
      { name: '乐观', values: [-8.3, 1.0, 8.0, 14.0, 18.0], description: '全面优化 + 竞品博弈优势' },
    ],
  },
  paths: [
    {
      title: '峰谷电价优化',
      category: '成本优化',
      annual_gain: 5.2,
      probability: 0.7,
      effort: 'low',
      source: '[算法预测]',
      detail: '将 40% 充电量从高峰(1.2元)移至低谷(0.3元)，预计年降本 5.2 万',
    },
    {
      title: '午间引流套餐',
      category: '效率提升',
      annual_gain: 8.1,
      probability: 0.5,
      effort: 'medium',
      source: '[知识库类比]',
      detail: '参考小鹏S4超快充模式：推出午间 11-14 点优惠套餐，预计提升利用率 8%',
    },
    {
      title: '周边价格博弈',
      category: '博弈调价',
      annual_gain: 3.4,
      probability: 0.4,
      effort: 'low',
      source: '[行业规律推断]',
      detail: '2km 内竞品均高于你 0.1 元/度，适度提价 0.05 元不会流失客户',
    },
    {
      title: '慢充桩改造',
      category: '资产盘活',
      annual_gain: 2.0,
      probability: 0.3,
      effort: 'high',
      source: '[知识库类比]',
      detail: '将 3 个闲置快充位改为 6 个慢充位，吸引夜间长停车辆，提升低谷利用率',
    },
  ],
  detail_text: `## 周边竞争格局分析

该场站位于南山区科技园片区，周边 2km 范围内共有 3 家竞品充电站，总装机功率约 3,600kW。竞品平均电价为 1.15 元/度（含服务费），你的场站定价 1.05 元/度，具有一定价格优势但差距不大。

## 运营效率瓶颈

当前利用率 5.2%，主要受两个因素制约：
1. **峰谷结构失衡**：高峰 13:00 利用率可达 18%，但低谷时段仅 1.2%，全天利用率被严重拉低
2. **快充配比过高**：20 个桩全为快充，缺乏慢充补充，无法覆盖夜间长停需求

## 引流潜力分析

周边 500m 内有 4 栋甲级写字楼（约 8,000 名白领），目前午间充电渗透率不足 5%。参考小鹏 S4 超快充的午间套餐模式，若推出 11:00-14:00 限时 8 折优惠，预计可将午间利用率提升至 25%。`,
};
