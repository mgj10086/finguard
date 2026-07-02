<template>
  <div class="documents-page">
    <div class="page-header">
      <h2 class="page-title">文档管理</h2>
      <el-button type="primary" @click="showUpload = true">
        <el-icon><Upload /></el-icon>上传文档
      </el-button>
    </div>

    <!-- 文档列表 -->
    <el-card>
      <el-table :data="docs" stripe v-loading="loading" style="width: 100%">
        <el-table-column type="index" width="50" />
        <el-table-column prop="filename" label="文件名称" min-width="250">
          <template #default="{ row }">
            <el-icon style="margin-right: 4px"><Document /></el-icon>
            {{ row.filename }}
          </template>
        </el-table-column>
        <el-table-column prop="file_type" label="类型" width="70">
          <template #default="{ row }">
            <el-tag size="small">{{ row.file_type?.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="解析状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="page_count" label="页数" width="60" align="center">
          <template #default="{ row }">{{ row.page_count ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="doc_type" label="文档类型" width="120" />
        <el-table-column prop="created_at" label="上传时间" width="180" />
      </el-table>
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUpload" title="上传文档" width="500px">
      <el-upload
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        accept=".pdf,.docx,.doc"
        :limit="1"
      >
        <el-icon class="upload-icon" :size="48"><UploadFilled /></el-icon>
        <div class="upload-text">拖拽文件到此处，或<em>点击选择</em></div>
        <template #tip>
          <div class="upload-hint">支持 PDF、Word 格式，单文件不超过 50MB</div>
        </template>
      </el-upload>
      <el-form v-if="selectedFile" style="margin-top: 16px">
        <el-form-item label="文档类型">
          <el-select v-model="uploadType" style="width: 100%">
            <el-option label="信息披露报告" value="disclosure_report" />
            <el-option label="风险自评表" value="risk_self_assessment" />
            <el-option label="年报" value="annual_report" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" :loading="uploading" :disabled="!selectedFile" @click="uploadDoc">
          上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Document, Upload, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { documentApi } from '../api'

const loading = ref(false)
const docs = ref([])
const showUpload = ref(false)
const uploading = ref(false)
const selectedFile = ref(null)
const uploadType = ref('other')

function statusType(s) {
  return { uploaded: 'info', parsing: 'warning', parsed: 'success', failed: 'danger' }[s] || 'info'
}
function statusLabel(s) {
  return { uploaded: '待解析', parsing: '解析中', parsed: '已解析', failed: '失败' }[s] || s
}

async function loadDocs() {
  loading.value = true
  try {
    const res = await documentApi.list({ page: 1, page_size: 50 })
    docs.value = res.data?.items || []
  } finally {
    loading.value = false
  }
}

function handleFileChange(file) {
  selectedFile.value = file.raw
}

async function uploadDoc() {
  if (!selectedFile.value) return
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('doc_type', uploadType.value)
    await documentApi.upload(formData)
    ElMessage.success('上传成功，正在解析')
    showUpload.value = false
    selectedFile.value = null
    loadDocs()
  } finally {
    uploading.value = false
  }
}

onMounted(loadDocs)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 22px; }
.upload-icon { margin-bottom: 12px; }
.upload-text { font-size: 14px; color: #606266; }
.upload-text em { color: #409eff; font-style: normal; }
.upload-hint { font-size: 12px; color: #909399; margin-top: 4px; }
</style>
