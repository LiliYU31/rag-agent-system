<template>
  <div class="progress-view">
    <div class="page-heading">
      <div>
        <div class="eyebrow">SCHEDWISE · WORKLOAD ANALYTICS</div>
        <h1>计划负载分析</h1>
        <p>基于计划日期与日程时段的可解释统计，不代表实际投入或完成情况。</p>
      </div>
      <div class="month-switcher">
        <el-button circle plain aria-label="上个月" @click="shiftSelectedMonth(-1)">‹</el-button>
        <span>{{ year }}年{{ String(month).padStart(2, '0') }}月</span>
        <el-button circle plain aria-label="下个月" @click="shiftSelectedMonth(1)">›</el-button>
      </div>
    </div>

    <div class="metric-grid">
      <article class="metric-card">
        <span class="metric-label">月计划</span>
        <strong>{{ data.month_plans?.total ?? 0 }}</strong>
        <span class="metric-foot">截止日期在所选月份</span>
      </article>
      <article class="metric-card">
        <span class="metric-label">周计划</span>
        <strong>{{ data.week_plans?.total ?? 0 }}</strong>
        <span class="metric-foot">截止日期在所选月份</span>
      </article>
      <article class="metric-card metric-card-accent">
        <span class="metric-label">日程安排时长</span>
        <strong>{{ formatHours(data.planned_hours) }}<small>小时</small></strong>
        <span class="metric-foot">仅统计有完整起止时间的日程</span>
      </article>
      <article class="metric-card">
        <span class="metric-label">周计划关联率</span>
        <strong>{{ data.linked_schedule_ratio ?? 0 }}<small>%</small></strong>
        <span class="metric-foot">已关联周计划的日程占比</span>
      </article>
    </div>

    <section class="panel trend-panel">
      <div class="panel-heading">
        <div>
          <h2>六个月计划趋势</h2>
          <p>按截止月份统计计划数，按日程日期统计日程数</p>
        </div>
        <div class="legend-note"><i></i>月计划 <i></i>周计划 <i></i>日程</div>
      </div>
      <v-chart :option="trendOption" class="trend-chart" autoresize />
    </section>

    <div class="detail-grid">
      <section class="panel heatmap-panel">
        <div class="panel-heading">
          <div>
            <h2>每日安排热力图</h2>
            <p>颜色越深，代表已排定的日程时长越长</p>
          </div>
          <span class="unit-label">小时 / 天</span>
        </div>
        <v-chart :option="heatmapOption" class="heatmap-chart" autoresize />
        <div class="heatmap-scale"><span>少</span><i></i><i></i><i></i><i></i><span>多</span></div>
      </section>

      <section class="panel insight-panel">
        <div class="panel-heading">
          <div>
            <h2>负载摘要</h2>
            <p>从本月日程安排中计算</p>
          </div>
          <span class="insight-mark">Σ</span>
        </div>
        <div class="insight-feature">
          <span>日程最密集日期</span>
          <strong>{{ formatDate(data.busiest_day?.date) }}</strong>
          <small>{{ formatHours(data.busiest_day?.planned_hours) }} 小时 · {{ data.busiest_day?.schedule_count ?? 0 }} 个日程</small>
        </div>
        <div class="insight-row">
          <span>日均安排时长</span>
          <strong>{{ formatHours(data.daily_mean_hours) }} 小时</strong>
        </div>
        <div class="insight-row">
          <span>每日负载波动（标准差）</span>
          <strong>{{ formatHours(data.daily_stddev_hours) }} 小时</strong>
        </div>
        <div class="method-note">
          <b>口径说明</b>
          <span>时长由日程开始与结束时间计算；未填写完整时段的日程计入数量，但不计入时长。</span>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, HeatmapChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, VisualMapComponent } from 'echarts/components'
import request from '../api/request'

use([CanvasRenderer, BarChart, HeatmapChart, GridComponent, TooltipComponent, LegendComponent, VisualMapComponent])

const today = new Date()
const year = ref(today.getFullYear())
const month = ref(today.getMonth() + 1)
const data = ref({
  month_plans: { total: 0, items: [] },
  week_plans: { total: 0, items: [] },
  schedules: { total: 0, items: [] },
  planned_hours: 0,
  linked_schedule_ratio: 0,
  daily_load: [],
  trend: [],
  daily_mean_hours: 0,
  daily_stddev_hours: 0,
})

const loadData = async () => {
  try {
    data.value = await request.get('/progress/monthly', { params: { year: year.value, month: month.value } })
  } catch (error) {
    console.error('加载负载分析失败', error)
  }
}

const shiftSelectedMonth = (step) => {
  const next = new Date(year.value, month.value - 1 + step, 1)
  year.value = next.getFullYear()
  month.value = next.getMonth() + 1
  loadData()
}

const formatHours = (value) => Number(value || 0).toFixed(1)
const formatDate = (value) => value ? `${Number(value.slice(5, 7))}月${Number(value.slice(8, 10))}日` : '暂无数据'

const trendOption = computed(() => ({
  color: ['#3978d4', '#43a895', '#d8a34b'],
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  legend: { show: false },
  grid: { left: 38, right: 20, top: 22, bottom: 32 },
  xAxis: {
    type: 'category',
    data: data.value.trend.map(item => item.month.slice(5, 7) + '月'),
    axisTick: { show: false },
    axisLine: { lineStyle: { color: '#e4e9f0' } },
    axisLabel: { color: '#7b8798' },
  },
  yAxis: {
    type: 'value',
    minInterval: 1,
    splitLine: { lineStyle: { color: '#edf0f5', type: 'dashed' } },
    axisLabel: { color: '#98a2b1' },
  },
  series: [
    { name: '月计划', type: 'bar', stack: 'total', barMaxWidth: 24, data: data.value.trend.map(item => item.month_plans), itemStyle: { borderRadius: [0, 0, 0, 0] } },
    { name: '周计划', type: 'bar', stack: 'total', barMaxWidth: 24, data: data.value.trend.map(item => item.week_plans) },
    { name: '日程', type: 'bar', stack: 'total', barMaxWidth: 24, data: data.value.trend.map(item => item.schedules), itemStyle: { borderRadius: [5, 5, 0, 0] } },
  ],
}))

const heatmapOption = computed(() => {
  const firstDay = new Date(year.value, month.value - 1, 1).getDay()
  const daysInMonth = new Date(year.value, month.value, 0).getDate()
  const loadByDate = new Map((data.value.daily_load || []).map(item => [item.date, item]))
  const points = Array.from({ length: daysInMonth }, (_, index) => {
    const day = index + 1
    const key = `${year.value}-${String(month.value).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    const load = loadByDate.get(key)
    return [new Date(year.value, month.value - 1, day).getDay(), Math.floor((day - 1 + firstDay) / 7), load?.planned_hours || 0, day, load?.schedule_count || 0]
  })
  const weekCount = Math.ceil((firstDay + daysInMonth) / 7)
  const maxHours = Math.max(1, ...points.map(point => point[2]))
  return {
    tooltip: {
      position: 'top',
      formatter: ({ data: point }) => `${month.value}月${point[3]}日<br/>日程数量：${point[4]} 个<br/>安排时长：${formatHours(point[2])} 小时`,
    },
    grid: { left: 54, right: 18, top: 12, bottom: 30 },
    xAxis: { type: 'category', data: ['日', '一', '二', '三', '四', '五', '六'], splitArea: { show: true }, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#7b8798' } },
    yAxis: { type: 'category', data: Array.from({ length: weekCount }, (_, i) => `第${i + 1}周`), inverse: true, splitArea: { show: true }, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#7b8798' } },
    visualMap: { min: 0, max: maxHours, calculable: false, show: false, inRange: { color: ['#f0f4fa', '#d8e7fa', '#91b5e5', '#3978d4'] } },
    series: [{ type: 'heatmap', data: points, label: { show: true, formatter: params => params.data[3], color: '#344258', fontSize: 11 }, itemStyle: { borderColor: '#fff', borderWidth: 4, borderRadius: 5 }, emphasis: { itemStyle: { shadowBlur: 8, shadowColor: 'rgba(35, 67, 112, 0.18)' } } }],
  }
})

onMounted(loadData)
</script>

<style scoped>
.progress-view { height: 100%; overflow-y: auto; padding: 4px 2px 24px; color: #263449; }
.page-heading { display: flex; justify-content: space-between; align-items: center; margin: 0 0 18px; }
.eyebrow { color: #8290a4; font-size: 10px; font-weight: 700; letter-spacing: .12em; }
h1 { margin: 5px 0 4px; font-size: 23px; line-height: 1.25; }
.page-heading p, .panel-heading p { margin: 0; color: #8793a5; font-size: 12px; }
.month-switcher { display: flex; align-items: center; gap: 12px; padding: 5px; border: 1px solid #e5eaf1; border-radius: 12px; background: #fff; }
.month-switcher span { min-width: 82px; text-align: center; font-size: 14px; font-weight: 700; }
.metric-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }
.metric-card, .panel { border: 1px solid #e5eaf1; border-radius: 13px; background: #fff; box-shadow: 0 3px 12px rgba(34, 52, 79, .035); }
.metric-card { display: flex; flex-direction: column; min-height: 112px; padding: 15px 17px; }
.metric-card-accent { background: linear-gradient(135deg, #fff 35%, #f2f7ff); }
.metric-label { color: #77859a; font-size: 12px; font-weight: 600; }
.metric-card strong { margin: 9px 0 4px; color: #263449; font-size: 26px; font-variant-numeric: tabular-nums; line-height: 1; }
.metric-card strong small { margin-left: 4px; font-size: 13px; font-weight: 600; }
.metric-foot { margin-top: auto; color: #9aa4b2; font-size: 10px; }
.panel { padding: 16px 18px 12px; }
.trend-panel { margin-bottom: 14px; }
.panel-heading { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.panel-heading h2 { margin: 0 0 5px; font-size: 15px; font-weight: 700; }
.legend-note { display: flex; align-items: center; gap: 5px; color: #78869a; font-size: 11px; }
.legend-note i { width: 8px; height: 8px; margin-left: 8px; border-radius: 2px; background: #3978d4; }
.legend-note i:nth-of-type(2) { background: #43a895; }
.legend-note i:nth-of-type(3) { background: #d8a34b; }
.trend-chart { height: 235px; width: 100%; }
.detail-grid { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(280px, .75fr); gap: 14px; }
.heatmap-chart { height: 220px; width: 100%; }
.unit-label { padding: 4px 8px; border-radius: 6px; background: #f4f6fa; color: #8793a5; font-size: 10px; }
.heatmap-scale { display: flex; align-items: center; justify-content: flex-end; gap: 4px; color: #8793a5; font-size: 10px; }
.heatmap-scale i { width: 12px; height: 8px; border-radius: 2px; background: #e4edf9; }
.heatmap-scale i:nth-of-type(2) { background: #c6daf4; }
.heatmap-scale i:nth-of-type(3) { background: #91b5e5; }
.heatmap-scale i:nth-of-type(4) { background: #3978d4; }
.insight-mark { display: grid; width: 30px; height: 30px; place-items: center; border-radius: 9px; background: #edf4ff; color: #3978d4; font-size: 16px; font-weight: 700; }
.insight-feature { display: flex; flex-direction: column; gap: 5px; margin: 17px 0 12px; padding: 13px; border-radius: 10px; background: #f7f9fc; }
.insight-feature span, .insight-row span { color: #7b8798; font-size: 11px; }
.insight-feature strong { font-size: 20px; }
.insight-feature small { color: #8793a5; font-size: 11px; }
.insight-row { display: flex; justify-content: space-between; gap: 10px; padding: 11px 1px; border-bottom: 1px solid #eef1f5; }
.insight-row strong { color: #344258; font-size: 12px; font-variant-numeric: tabular-nums; }
.method-note { display: flex; flex-direction: column; gap: 5px; margin-top: 12px; color: #8995a5; font-size: 10px; line-height: 1.6; }
.method-note b { color: #66758a; font-size: 11px; }
@media (max-width: 900px) { .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .detail-grid { grid-template-columns: 1fr; } }
@media (max-width: 560px) { .progress-view { padding: 0 0 16px; } .page-heading { align-items: flex-start; flex-direction: column; gap: 12px; } .month-switcher { align-self: flex-end; } .metric-grid { gap: 8px; } .metric-card { min-height: 104px; padding: 13px; } .metric-card strong { font-size: 22px; } .panel { padding: 14px 12px 10px; } .legend-note { display: none; } }
</style>
