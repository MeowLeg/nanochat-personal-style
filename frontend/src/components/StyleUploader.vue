<template>
  <div class="sample-uploader">
    <el-upload
      drag
      multiple
      :auto-upload="false"
      :on-change="handleFileChange"
      :on-remove="handleFileRemove"
      :file-list="fileList"
      accept=".txt,.md,.xlsx,.xls"
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        将文件拖到此处，或 <em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持 .txt, .md, .xlsx, .xls 文件，可多选上传
          <br />
          <span style="color: var(--el-color-primary)">Excel 格式: 标题列 + 内容列</span>
        </div>
      </template>
    </el-upload>

    <el-form :model="form" label-width="100px" style="margin-top: 20px">
      <el-form-item label="选择作者" required>
        <el-select v-model="form.authorId" placeholder="请先创建作者档案，然后选择" clearable filterable style="width: 100%" @focus="loadAuthors">
          <el-option
            v-for="author in authors"
            :key="author.id"
            :label="author.name"
            :value="author.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="来源说明">
        <el-input v-model="form.source" placeholder="可选，如博客、书籍等" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="handleUpload" :disabled="!form.authorId">
          导入样本
        </el-button>
        <el-button @click="loadAuthors">
          刷新作者列表
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage, type UploadUserFile, type UploadProps } from 'element-plus'
import { samplesApi, authorsApi } from '@/services/api'
import type { AuthorProfile } from '@/types'

const emit = defineEmits<{
  uploaded: [samples: any[]]
}>()

const fileList = ref<UploadUserFile[]>([])
const loading = ref(false)
const authors = ref<AuthorProfile[]>([])

const form = reactive({
  authorId: '',
  source: ''
})

const selectedFiles = ref<File[]>([])

const selectedAuthor = computed(() => {
  return authors.value.find(a => a.id === form.authorId)
})

const loadAuthors = async () => {
  try {
    const { data } = await authorsApi.listAuthors()
    authors.value = data
  } catch (error) {
    console.error('Failed to load authors:', error)
  }
}

const handleFileChange: UploadProps['onChange'] = (file) => {
  if (file.raw) {
    selectedFiles.value.push(file.raw)
  }
}

const handleFileRemove: UploadProps['onRemove'] = (file) => {
  const index = selectedFiles.value.findIndex(f => f.name === file.name)
  if (index > -1) {
    selectedFiles.value.splice(index, 1)
  }
}

const handleUpload = async () => {
  if (!selectedFiles.value.length) {
    ElMessage.warning('请选择要上传的文件')
    return
  }
  if (!form.authorId) {
    ElMessage.warning('请先选择作者档案')
    return
  }

  const author = selectedAuthor.value
  if (!author) {
    ElMessage.warning('未找到作者信息')
    return
  }

  loading.value = true
  try {
    const { data } = await samplesApi.importSamples(
      selectedFiles.value,
      author.name,
      form.source,
      'zh',
      form.authorId
    )
    ElMessage.success(`成功导入 ${data.length} 个样本到「${author.name}」`)
    emit('uploaded', data)
    fileList.value = []
    selectedFiles.value = []
    form.source = ''
    loadAuthors()
  } catch (error) {
    ElMessage.error('导入失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAuthors()
})

defineExpose({
  loadAuthors
})
</script>

<style scoped>
.sample-uploader {
  padding: 20px;
}
</style>