<template>
  <div class="article-rewriter">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>原文</span>
              <el-button type="primary" link @click="clearSource">清空</el-button>
            </div>
          </template>
          <el-input
            v-model="sourceText"
            type="textarea"
            :rows="20"
            placeholder="请输入或粘贴需要改写的文章..."
            @input="updateSourceCount"
          />
          <div class="word-count">当前字数：{{ sourceCount }}</div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>改写结果</span>
              <el-button type="success" link @click="copyResult" v-if="resultText">复制</el-button>
            </div>
          </template>
          <el-input
            v-model="resultText"
            type="textarea"
            :rows="20"
            readonly
            placeholder="改写后的内容将显示在这里..."
          />
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px">
      <el-form :inline="true" :model="settings" class="settings-form">
        <el-form-item label="选择风格">
          <el-select v-model="settings.styleId" placeholder="请选择风格" style="width: 250px" @focus="loadProfiles">
            <el-option
              v-for="profile in profiles"
              :key="profile.id"
              :label="profile.name"
              :value="profile.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="风格强度">
          <el-slider v-model="settings.styleStrength" :min="0" :max="1" :step="0.1" style="width: 150px" />
          <span style="margin-left: 10px">{{ settings.styleStrength.toFixed(1) }}</span>
        </el-form-item>
        <el-form-item label="字数限制">
          <el-input-number v-model="settings.maxLength" :min="100" :max="5000" :step="100" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="rewriting" @click="handleRewrite">
            开始改写
          </el-button>
        </el-form-item>
      </el-form>

      <div v-if="metadata" class="metadata">
        <el-divider />
        <h4>改写信息</h4>
        <p>原文长度: {{ metadata.source_length }} 字符</p>
        <p>改写长度: {{ metadata.rewritten_length }} 字符</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { stylesApi, rewriteApi } from '@/services/api'
import type { StyleProfile } from '@/types'

const profiles = ref<StyleProfile[]>([])
const sourceText = ref('')
const resultText = ref('')
const rewriting = ref(false)
const metadata = ref<any>(null)
const sourceCount = ref(0)

const settings = reactive({
  styleId: '',
  styleStrength: 0.7,
  maxLength: 800
})

const updateSourceCount = () => {
  sourceCount.value = sourceText.value.length
}

const loadProfiles = async () => {
  try {
    const { data } = await stylesApi.listProfiles()
    profiles.value = data
    if (data.length && !settings.styleId) {
      settings.styleId = data[0].id
    }
  } catch (error) {
    console.error('Failed to load profiles:', error)
  }
}

const handleRewrite = async () => {
  if (!sourceText.value.trim()) {
    ElMessage.warning('请输入需要改写的文章')
    return
  }
  if (!settings.styleId) {
    ElMessage.warning('请选择一个风格')
    return
  }

  rewriting.value = true
  resultText.value = ''
  metadata.value = null

  try {
    const { data } = await rewriteApi.rewrite({
      style_id: settings.styleId,
      source_text: sourceText.value,
      style_strength: settings.styleStrength,
      max_length: settings.maxLength
    })
    resultText.value = data.rewritten_text
    metadata.value = data.generation_metadata
    ElMessage.success('改写完成')
  } catch (error) {
    ElMessage.error('改写失败')
    console.error(error)
  } finally {
    rewriting.value = false
  }
}

const clearSource = () => {
  sourceText.value = ''
  resultText.value = ''
  metadata.value = null
}

const copyResult = async () => {
  try {
    await navigator.clipboard.writeText(resultText.value)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const selectStyle = (profile: StyleProfile) => {
  settings.styleId = profile.id
}

onMounted(() => {
  loadProfiles()
})

defineExpose({
  selectStyle,
  loadProfiles
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.settings-form {
  margin: 0;
}
.metadata {
  margin-top: 10px;
}
.word-count {
  margin-top: 8px;
  text-align: right;
  color: #999;
  font-size: 13px;
}
</style>