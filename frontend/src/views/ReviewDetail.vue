<template>
  <div class="review-detail" v-loading="loading">
    <!-- 返回 -->
    <el-button text @click="$router.push('/reviews')" style="margin-bottom: 16px">
      <el-icon><ArrowLeft /></el-icon>返回审核列表
    </el-button>

    <!-- 审核概况 -->
    <el-card v-if="review" class="summary-card">
      <div class="summary-header">
        <h3>{{ review.title }}</h3>
        <el-tag :type="statusTag" size="large">{{ review.status }}</el-tag>
      </div>

      <el-row :gutter="16" class="summary-stats">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value" :style="{ color: scoreColor(review.compliance_score) }">
              {{ review.compliance_score ?? '-' }}
            </div>
            <div class="stat-label">合规评分</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value" style="color: #f56c6c">{{ review.critical_count }}</div>
            <div class="stat-label">重大违规</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value" style="color: #e6a23c">{{ review.high_count }}</div>
            <div class="stat-label">高风险</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ review.total_findings }}</div>
            <div class="stat-label">发现问题总数</div>
          </div>
        </el-col>
      </el-row>

      <el-divider />

      <p class="summary-text">{{ review.summary }}</p>

      <!-- 人工复核 -->
      <el-alert
        v-if="review.needs_human_review"
        type="warning"
        :title="review.human_review_reason || '需要人工复核'"
        show-icon
        :closable="false"
        class="human-review-alert"
      />
    </el-card>

    <!-- 审核发现列表 -->
    <el-card v-if="review?.findings?.length" class="findings-card">
      <template #header>
        <div class="card-header">
          <span>审核发现 ({{ review.findings.length }})</span>
        </div>
      </template>

      <el-timeline>
        <el-timeline-item
          v-for="f in review.findings"
          :key="f.id"
          :timestamp="f.regulation_cited || ''"
          :color="severityColor(f.severity)"
        >
          <div class="finding-item">
            <div class="finding-header">
              <el-tag :type="severityTag(f.severity)" size="small" effect="dark">
                {{ f.severity.toUpperCase() }}
              </el-tag>
              <strong>{{ f.title }}</strong>
            </div>
            <p class="finding-desc">{{ f.description }}</p>
            <div v-if="f.source_text" class="finding-source">
              <el-tag size="small" type="info">原文引用</el-tag>
              <blockquote>{{ f.source_text }}</blockquote>
            </div>
            <div v-if="f.reasoning" class="finding-reasoning">
              <el-tag size="small" type="warning">推理过程</el-tag>
              <p>{{ f.reasoning }}</p>
            </div>
            <div v-if="f.suggestion" class="finding-suggestion">
              <el-tag size="small" type="success">整改建议</el-tag>
              <p>{{ f.suggestion }}</p>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <!-- 人工确认 -->
    <el-card v-if="review?.needs_human_review" class="confirm-card">
      <template #header>人工确认</template>
      <el-input
        v-model="confirmComment"
        type="textarea"
        :rows="3"
        placeholder="确认意见..."
        style="margin-bottom: 12px"
      />
      <div class="confirm-actions">
        <el-button type="success" @click="confirmReview('approve')">确认通过</el-button>
        <el-button type="danger" @click="confirmReview('reject')">驳回重审</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { reviewApi } from '../api'

const route = useRoute()
const loading = ref(false)
const review = ref(null)
const confirmComment = ref('')

const statusTag = computed(() => {
  const map = { pending: 'warning', completed: 'success', failed: 'danger', rejected: 'danger' }
  return map[review.value?.status] || 'info'
})
const statusLabel = computed(() => {
  const map = { pending: '待处理', completed: '已完成', rejected: '需人工', failed: '失败' }
  return map[review.value?.status] || review.value?.status
})

function severityColor(s) {
  return { critical: '#f56c6c', high: '#e6a23c', medium: '#409eff', low: '#909399' }[s] || '#409eff'
}
function severityTag(s) {
  return { critical: 'danger', high: 'warning', medium: 'primary', low: 'info' }[s] || 'info'
}
function scoreColor(s) {
  if (!s && s !== 0) return '#999'
  return s >= 80 ? '#67c23a' : s >= 60 ? '#e6a23c' : '#f56c6c'
}

async function loadReview() {
  loading.value = true
  try {
    const res = await reviewApi.get(route.params.id)
    review.value = res.data
    // Add arrow-back for status labels
  } finally {
    loading.value = false
  }
}

async function confirmReview(action) {
  try {
    await reviewApi.confirm(route.params.id, action, confirmComment.value)
    ElMessage.success('操作成功')
    loadReview()
  } catch { /* handled */ }
}

onMounted(loadReview)
</script>

<style scoped>
.summary-card { margin-bottom: 20px; }
.summary-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.summary-header h3 { font-size: 20px; }
.summary-stats { margin-bottom: 8px; }
.stat-item { text-align: center; padding: 16px 0; }
.stat-value { font-size: 28px; font-weight: 700; }
.stat-label { font-size: 14px; color: #909399; margin-top: 4px; }
.summary-text { font-size: 14px; line-height: 1.6; color: #606266; }
.human-review-alert { margin-top: 12px; }
.findings-card { margin-bottom: 20px; }
.card-header { display: flex; align-items: center; }
.finding-item { padding: 4px 0; }
.finding-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.finding-desc { color: #606266; margin-bottom: 8px; line-height: 1.5; }
.finding-source, .finding-reasoning, .finding-suggestion {
  margin-top: 8px; padding-left: 8px; border-left: 3px solid #e4e7ed;
}
.finding-source blockquote {
  margin: 4px 0; padding: 8px; background: #f5f7fa; border-radius: 4px;
  font-size: 13px; color: #909399;
}
.finding-reasoning p, .finding-suggestion p {
  margin: 4px 0; font-size: 13px; color: #606266;
}
.confirm-card { margin-bottom: 20px; }
.confirm-actions { display: flex; gap: 12px; }
</style>
