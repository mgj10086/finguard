<template>
  <div class="dashboard">
    <div class="page-header">
      <h2 class="page-title">工作台</h2>
      <div class="header-time">{{ currentTime }}</div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <el-card shadow="hover" class="stat-card" @click="stat.path && $router.push(stat.path)">
          <div class="stat-inner">
            <div class="stat-icon" :style="{ background: stat.bg }">
              <el-icon :size="24" color="#fff"><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value" :style="{ color: stat.color }">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表行 -->
    <el-row :gutter="16" class="chart-row">
      <!-- 合规评分分布 -->
      <el-col :span="14">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>合规评分趋势</span>
              <el-tag type="success" size="small">最近 7 天</el-tag>
            </div>
          </template>
          <div ref="trendChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <!-- 严重程度分布 -->
      <el-col :span="10">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>问题严重程度分布</span>
            </div>
          </template>
          <div ref="pieChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近审核任务 -->
    <el-card class="section-card">
      <template #header>
        <div class="card-header">
          <span><el-icon><DocumentChecked /></el-icon> 最近审核任务</span>
          <div class="header-actions">
            <el-button text type="primary" @click="$router.push('/reviews')">查看全部</el-button>
            <el-button type="primary" size="small" @click="$router.push('/documents')">
              <el-icon><Plus /></el-icon>新建审核
            </el-button>
          </div>
        </div>
      </template>
      <el-table :data="recentReviews" stripe style="width: 100%" v-loading="tableLoading">
        <el-table-column type="index" width="50" />
        <el-table-column prop="title" label="任务名称" min-width="200">
          <template #default="{ row }">
            <el-icon><Document /></el-icon>
            {{ row.title }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="plain">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="compliance_score" label="评分" width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.compliance_score !== null && row.compliance_score !== undefined"
                  :style="{ color: scoreColor(row.compliance_score), fontWeight: 700, fontSize: '16px' }">
              {{ row.compliance_score }}
            </span>
            <span v-else style="color: #c0c4cc">待审核</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_findings" label="发现" width="60" align="center" />
        <el-table-column label="人工" width="60" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.needs_human_review" type="danger" size="small" effect="dark">需</el-tag>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="$router.push(`/reviews/${row.id}`)">
              详情
            </el-button>
            <el-button
              v-if="row.status === 'pending'"
              text type="success" size="small"
              @click="startReview(row.id)"
            >
              启动
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!recentReviews.length && !tableLoading" class="empty-state">
        <el-empty description="暂无审核任务" />
      </div>
    </el-card>

    <!-- 系统状态 -->
    <el-card class="section-card">
      <template #header>
        <span><el-icon><Monitor /></el-icon> 系统状态</span>
      </template>
      <el-row :gutter="16">
        <el-col :span="6" v-for="svc in services" :key="svc.name">
          <div class="service-item">
            <el-tag :type="svc.status ? 'success' : 'danger'" size="small" effect="dark">
              {{ svc.status ? '●' : '○' }}
            </el-tag>
            <span class="service-name">{{ svc.name }}</span>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { Document, DocumentChecked, Monitor, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { reviewApi } from '../api'
import * as echarts from 'echarts'

const router = useRouter()
const tableLoading = ref(false)
const recentReviews = ref([])
const currentTime = ref('')
const trendChartRef = ref(null)
const pieChartRef = ref(null)
let trendChart = null
let pieChart = null
let timer = null

const stats = computed(() => {
  const items = recentReviews.value
  return [
    { label: '待审核', value: items.filter(r => r.status === 'pending').length, icon: 'Clock', color: '#e6a23c', bg: '#fdf6ec', path: '/reviews?status=pending' },
    { label: '审核中', value: items.filter(r => ['dispatching','reviewing','adjudicating','final_reviewing'].includes(r.status)).length, icon: 'Loading', color: '#409eff', bg: '#ecf5ff', path: '/reviews' },
    { label: '已完成', value: items.filter(r => r.status === 'completed').length, icon: 'CircleCheck', color: '#67c23a', bg: '#f0f9eb', path: '/reviews?status=completed' },
    { label: '需人工复核', value: items.filter(r => r.needs_human_review).length, icon: 'WarningFilled', color: '#f56c6c', bg: '#fef0f0', path: '/reviews' },
  ]
})

const services = ref([
  { name: 'FastAPI', status: false },
  { name: 'PostgreSQL', status: false },
  { name: 'Milvus', status: false },
  { name: 'Neo4j', status: false },
  { name: 'Redis', status: false },
  { name: 'vLLM', status: false },
])

function statusType(s) {
  const map = { pending: 'warning', completed: 'success', failed: 'danger', rejected: 'danger', reviewing: 'primary', dispatching: 'info', adjudicating: 'warning', final_reviewing: 'primary' }
  return map[s] || 'info'
}
function statusLabel(s) {
  const map = { pending: '待处理', dispatching: '分发中', reviewing: '审核中', adjudicating: '裁决中', final_reviewing: '复审中', completed: '已完成', rejected: '需人工', failed: '失败' }
  return map[s] || s
}
function scoreColor(s) {
  if (s === null || s === undefined) return '#999'
  return s >= 80 ? '#67c23a' : s >= 60 ? '#e6a23c' : '#f56c6c'
}
function formatDate(d) {
  if (!d) return '-'
  const date = new Date(d)
  return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function loadDashboard() {
  tableLoading.value = true
  try {
    const res = await reviewApi.list({ page: 1, page_size: 10 })
    recentReviews.value = (res.data?.items || []).slice(0, 5)
  } catch {
    recentReviews.value = []
  } finally {
    tableLoading.value = false
  }
}

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    weekday: 'long',
  })
}

async function initCharts() {
  await nextTick()
  if (!trendChartRef.value || !pieChartRef.value) return

  // 折线图 — 合规评分趋势
  trendChart = echarts.init(trendChartRef.value)
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ['06-26', '06-27', '06-28', '06-29', '06-30', '07-01', '07-02'],
      axisLabel: { fontSize: 11, color: '#909399' },
    },
    yAxis: {
      type: 'value', min: 0, max: 100,
      axisLabel: { fontSize: 11, color: '#909399', formatter: '{value}' },
    },
    series: [{
      data: [85, 78, 72, 90, 88, 65, 82],
      type: 'line',
      smooth: true,
      lineStyle: { width: 3, color: '#409eff' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(64,158,255,0.3)' },
          { offset: 1, color: 'rgba(64,158,255,0.02)' },
        ])
      },
      itemStyle: { color: '#409eff' },
      markLine: {
        silent: true,
        data: [{ yAxis: 60, label: { formatter: '及格线', color: '#e6a23c', fontSize: 10 } }],
        lineStyle: { color: '#e6a23c', type: 'dashed' },
      },
    }],
  })

  // 饼图 — 严重程度分布
  pieChart = echarts.init(pieChartRef.value)
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: '0%', textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie', radius: ['40%', '65%'], center: ['50%', '45%'],
      avoidLabelOverlap: true,
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      data: [
        { value: 1, name: '重大', itemStyle: { color: '#f56c6c' } },
        { value: 3, name: '高风险', itemStyle: { color: '#e6a23c' } },
        { value: 2, name: '中风险', itemStyle: { color: '#409eff' } },
        { value: 1, name: '低风险', itemStyle: { color: '#909399' } },
      ],
    }],
  })

  // 自适应
  window.addEventListener('resize', handleResize)
}

function handleResize() {
  trendChart?.resize()
  pieChart?.resize()
}

async function startReview(id) {
  try {
    await reviewApi.start(id)
    ElMessage.success('审核流水线已启动')
    loadDashboard()
  } catch { /* handled by interceptor */ }
}

onMounted(async () => {
  await loadDashboard()
  updateTime()
  timer = setInterval(updateTime, 1000)
  initCharts()
})

onUnmounted(() => {
  clearInterval(timer)
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  pieChart?.dispose()
})
</script>

<style scoped>
.dashboard { max-width: 1400px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-title { font-size: 24px; font-weight: 600; color: #303133; }
.header-time { font-size: 14px; color: #909399; }
.stat-row { margin-bottom: 20px; }
.stat-card { cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.stat-inner { display: flex; align-items: center; gap: 16px; }
.stat-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.stat-value { font-size: 28px; font-weight: 700; line-height: 1.2; }
.stat-label { font-size: 13px; color: #909399; margin-top: 2px; }
.chart-row { margin-bottom: 20px; }
.chart-card { margin-bottom: 0; }
.chart-box { height: 260px; }
.section-card { margin-bottom: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.header-actions { display: flex; gap: 8px; align-items: center; }
.empty-state { padding: 40px 0; }
.service-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; }
.service-name { font-size: 13px; color: #606266; }
</style>
