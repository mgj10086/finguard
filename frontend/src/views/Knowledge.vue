<template>
  <div class="knowledge-page">
    <div class="page-header">
      <h2 class="page-title">法规知识库</h2>
      <div class="header-actions">
        <el-button type="primary" @click="showUpload = true">
          <el-icon><Upload /></el-icon>上传法规
        </el-button>
      </div>
    </div>

    <!-- 法规列表 -->
    <el-card>
      <el-table :data="regulations" stripe v-loading="loading" style="width: 100%">
        <el-table-column type="index" width="50" />
        <el-table-column prop="short_title" label="法规名称" min-width="200">
          <template #default="{ row }">
            <el-icon><Reading /></el-icon>
            {{ row.short_title || row.title }}
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="120" />
        <el-table-column prop="doc_number" label="文号" width="180" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '有效' : '废止' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="effective_date" label="生效日期" width="120" />
      </el-table>
    </el-card>

    <!-- 法规检索 -->
    <el-card class="search-card">
      <template #header>语义检索</template>
      <el-form :inline="true" @submit.prevent="searchRegulations">
        <el-form-item style="width: 400px">
          <el-input
            v-model="searchQuery"
            placeholder="输入检索内容，如：信息披露、风险分类、资本充足率..."
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchRegulations" :loading="searching">检索</el-button>
        </el-form-item>
      </el-form>

      <el-table v-if="searchResults.length" :data="searchResults" stripe style="width: 100%">
        <el-table-column prop="content" label="条款内容" min-width="500">
          <template #default="{ row }">
            <div class="search-result-content">{{ row.content }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="匹配度" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.score >= 0.85 ? 'success' : row.score >= 0.7 ? 'warning' : 'info'" size="small">
              {{ (row.score * 100).toFixed(1) }}%
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 上传法规对话框 -->
    <el-dialog v-model="showUpload" title="上传法规文档" width="500px">
      <el-upload
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        accept=".pdf,.docx"
        :limit="1"
      >
        <el-icon class="upload-icon" :size="48"><UploadFilled /></el-icon>
        <div class="upload-text">拖拽法规文件到此处</div>
      </el-upload>
      <el-form v-if="selectedFile" style="margin-top: 16px">
        <el-form-item label="来源">
          <el-select v-model="uploadSource" style="width: 100%">
            <el-option label="国家金融监督管理总局" value="cbirc" />
            <el-option label="中国人民银行" value="pboc" />
            <el-option label="中国证监会" value="csrc" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" :loading="uploading" :disabled="!selectedFile" @click="uploadRegulation">
          上传并建立索引
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Reading, Upload, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { knowledgeApi } from '../api'

const loading = ref(false)
const regulations = ref([])
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const showUpload = ref(false)
const uploading = ref(false)
const selectedFile = ref(null)
const uploadSource = ref('cbirc')

async function loadRegulations() {
  loading.value = true
  try {
    const res = await knowledgeApi.list({ page: 1, page_size: 50 })
    regulations.value = res.data?.items || []
  } finally {
    loading.value = false
  }
}

async function searchRegulations() {
  if (!searchQuery.value.trim()) return
  searching.value = true
  try {
    const res = await knowledgeApi.search(searchQuery.value, 10)
    searchResults.value = res.data?.results || []
  } finally {
    searching.value = false
  }
}

function handleFileChange(file) {
  selectedFile.value = file.raw
}

async function uploadRegulation() {
  if (!selectedFile.value) return
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('source', uploadSource.value)
    await knowledgeApi.upload(formData)
    ElMessage.success('法规上传并建立索引成功')
    showUpload.value = false
    selectedFile.value = null
    loadRegulations()
  } finally {
    uploading.value = false
  }
}

onMounted(loadRegulations)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 22px; }
.search-card { margin-top: 16px; }
.search-result-content {
  font-size: 13px;
  line-height: 1.5;
  max-height: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}
.upload-icon { margin-bottom: 12px; }
.upload-text { font-size: 14px; color: #606266; }
</style>
