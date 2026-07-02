<template>
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-circle c1"></div>
      <div class="bg-circle c2"></div>
      <div class="bg-circle c3"></div>
    </div>

    <div class="login-container">
      <!-- Logo 区 -->
      <div class="login-brand">
        <img src="/favicon.svg" alt="FinGuard" class="brand-logo" />
        <h1 class="brand-title">FinGuard</h1>
        <p class="brand-subtitle">金融合规文档智能审核系统</p>
        <div class="brand-features">
          <div class="feature-item">
            <el-icon><Lightning /></el-icon>
            <span>AI 智能预审</span>
          </div>
          <div class="feature-item">
            <el-icon><Connection /></el-icon>
            <span>知识图谱追溯</span>
          </div>
          <div class="feature-item">
            <el-icon><Clock /></el-icon>
            <span>30 分钟出报告</span>
          </div>
        </div>
      </div>

      <!-- 登录卡片 -->
      <div class="login-card-wrapper">
        <div class="login-card">
          <h2 class="card-title">欢迎登录</h2>
          <p class="card-desc">请使用合规部门账号登录系统</p>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            class="login-form"
            @keyup.enter="handleLogin"
          >
            <el-form-item prop="username">
              <el-input
                v-model="form.username"
                placeholder="用户名"
                :prefix-icon="User"
                size="large"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="密码"
                :prefix-icon="Lock"
                show-password
                size="large"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="login-btn"
                :loading="loading"
                @click="handleLogin"
              >
                {{ loading ? '登录中...' : '登 录' }}
              </el-button>
            </el-form-item>
          </el-form>

          <div class="login-footer">
            <p class="demo-hint">
              <el-icon><InfoFilled /></el-icon>
              演示账号：admin / admin123
            </p>
          </div>
        </div>

        <p class="copyright">© 2026 FinGuard. All rights reserved.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, InfoFilled, Lightning, Connection, Clock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAppStore } from '../stores/app'

const router = useRouter()
const store = useAppStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  await new Promise(r => setTimeout(r, 600)) // 模拟登录延时

  if (form.username === 'admin' && form.password === 'admin123') {
    store.login('fg-mock-token', {
      username: 'admin',
      role: 'admin',
      displayName: '合规管理员',
      department: '合规管理部',
    })
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } else {
    ElMessage.error('用户名或密码错误')
  }
  loading.value = false
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0a1a2f 0%, #001529 30%, #003a70 70%, #0050b3 100%);
  position: relative;
  overflow: hidden;
}

.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.08;
}
.c1 { width: 600px; height: 600px; background: #409eff; top: -200px; left: -100px; }
.c2 { width: 400px; height: 400px; background: #67c23a; bottom: -100px; right: -50px; }
.c3 { width: 300px; height: 300px; background: #e6a23c; top: 50%; left: 60%; }

.login-container {
  display: flex;
  align-items: center;
  gap: 80px;
  z-index: 1;
}

.login-brand {
  color: #fff;
  text-align: center;
}
.brand-logo { width: 72px; height: 72px; margin-bottom: 16px; filter: drop-shadow(0 4px 12px rgba(0,0,0,0.3)); }
.brand-title { font-size: 36px; font-weight: 700; margin-bottom: 8px; letter-spacing: 2px; }
.brand-subtitle { font-size: 15px; opacity: 0.7; margin-bottom: 32px; }
.brand-features { display: flex; flex-direction: column; gap: 12px; align-items: center; }
.feature-item { display: flex; align-items: center; gap: 8px; font-size: 14px; opacity: 0.6; transition: opacity 0.3s; }
.feature-item:hover { opacity: 1; }

.login-card-wrapper { text-align: center; }
.login-card {
  width: 400px;
  padding: 40px 36px;
  background: rgba(255,255,255,0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.25);
}
.card-title { font-size: 22px; font-weight: 600; color: #303133; margin-bottom: 4px; }
.card-desc { font-size: 14px; color: #909399; margin-bottom: 28px; }
.login-form { margin-bottom: 16px; }
.login-btn { width: 100%; height: 44px; font-size: 16px; }
.login-footer { margin-top: 12px; }
.demo-hint { font-size: 12px; color: #c0c4cc; display: flex; align-items: center; justify-content: center; gap: 4px; }
.copyright { font-size: 12px; color: rgba(255,255,255,0.35); margin-top: 20px; }
</style>
