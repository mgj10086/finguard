<template>
  <div class="reviews-page">
    <div class="page-header">
      <h2 class="page-title">审核管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>新建审核
        </el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部" style="width: 140px">
            <el-option label="待处理" value="pending" />
            <el-option label="已完成" value="completed" />
            <el-option label="需人工复核" value="rejected" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="loadReviews">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-card>
      <el-table :data="reviews" stripe v-loading="loading" style="width: 100%">
        <el-table-column type="index" width="50" />
        <el-table-column prop="title" label="任务名称" min-width="200" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="compliance_score" label="评分" width="80" align="center">
          <template #default="{ row }">
            <span :style="{ color: scoreColor(row.compliance_score), fontWeight: 600 }">
              {{ row.compliance_score ?? '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="total_findings" label="发现问题" width="80" align="center" />
        <el-table-column label="需要人工" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.needs_human_review" type="danger" size="small">是</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="160" fixed="right">
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
    </el-card>

    <!-- 新建审核对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建审核任务" width="500px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="选择文档" prop="document_id">
          <el-select v-model="createForm.document_id" filterable placeholder="请选择待审核文档" style="width: 100%">
            <el-option
              v-for="doc in documentOptions"
              :key="doc.id"
              :label="doc.filename"
              :value="doc.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="任务名称" prop="title">
          <el-input v-model="createForm.title" placeholder="留空自动生成" />
        </el-form-item>
        <el-form-item label="业务类型" prop="business_type">
          <el-select v-model="createForm.business_type" placeholder="选择业务类型" style="width: 100%">
            <el-option label="信息披露" value="信息披露" />
            <el-option label="风险自评" value="风险自评" />
            <el-option label="年度报告" value="年度报告" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createReview">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { reviewApi, documentApi } from '../api'

const loading = ref(false)
const creating = ref(false)
const reviews = ref([])
const showCreateDialog = ref(false)
const documentOptions = ref([])

const filters = ref({ status: '' })
const createForm = ref({ document_id: null, title: '', business_type: '' })
const createRules = { document_id: [{ required: true, message: '请选择文档', trigger: 'change' }] }

async function loadReviews() {
  loading.value = true
  try {
    const res = await reviewApi.list({ page: 1, page_size: 50, ...filters.value })
    reviews.value = res.data?.items || []
  } finally {
    loading.value = false
  }
}

async function loadDocuments() {
  try {
    const res = await documentApi.list({ page: 1, page_size: 100, status: 'parsed' })
    documentOptions.value = (res.data?.items || []).map(d => ({
      id: d.id, filename: d.filename,
    }))
  } catch { /* ignore */ }
}

async function createReview() {
  creating.value = true
  try {
    await reviewApi.create({
      document_id: createForm.value.document_id,
      title: createForm.value.title,
      business_type: createForm.value.business_type,
    })
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    loadReviews()
  } finally {
    creating.value = false
  }
}

async function startReview(id) {
  try {
    await reviewApi.start(id)
    ElMessage.success('审核流水线已启动')
    loadReviews()
  } catch { /* handled by interceptor */ }
}

function resetFilters() {
  filters.value = { status: '' }
  loadReviews()
}

const statusType = (s) => ({
  pending: 'warning', completed: 'success', failed: 'danger',
  rejected: 'danger', reviewing: 'primary',
}[s] || 'info')
const statusLabel = (s) => ({
  pending: '待处理', dispatching: '分发中', reviewing: '审核中',
  adjudicating: '裁决中', final_reviewing: '复审中',
  completed: '已完成', rejected: '需人工', failed: '失败',
}[s] || s)
const scoreColor = (s) => {
  if (!s && s !== 0) return '#999'
  return s >= 80 ? '#67c23a' : s >= 60 ? '#e6a23c' : '#f56c6c'
}

onMounted(() => {
  loadReviews()
  loadDocuments()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 22px; }
.filter-card { margin-bottom: 16px; }
</style>
