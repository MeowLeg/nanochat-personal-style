<template>
  <div class="author-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>作者档案管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            创建作者档案
          </el-button>
        </div>
      </template>

      <el-table :data="authors" stripe style="width: 100%">
        <el-table-column prop="name" label="作者名称" width="200" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="sample_count" label="稿件数量" width="100">
          <template #default="{ row }">
            <el-tag type="info">{{ row.sample_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="style_count" label="风格数量" width="100">
          <template #default="{ row }">
            <el-tag type="success">{{ row.style_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleSelect(row)">
              查看
            </el-button>
            <el-button link type="success" @click="handleImportSamples(row)">
              导入稿件
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreateDialog" title="创建作者档案" width="500px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="作者名称" required>
          <el-input v-model="createForm.name" placeholder="请输入作者名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="可选，描述一下这个作者" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">
          创建
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDetailDialog" title="作者档案详情" width="900px">
      <div v-if="selectedAuthor" class="author-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="作者名称">{{ selectedAuthor.name }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ selectedAuthor.description || '无' }}</el-descriptions-item>
          <el-descriptions-item label="稿件数量">
            <el-tag type="info">{{ selectedAuthor.sample_count }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="风格数量">
            <el-tag type="success">{{ selectedAuthor.style_count }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(selectedAuthor.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <div class="samples-section">
          <h3>稿件列表</h3>
          <el-table :data="authorSamples" stripe max-height="300">
            <el-table-column prop="title" label="标题" width="200" show-overflow-tooltip />
            <el-table-column prop="source" label="来源" width="150" show-overflow-tooltip />
            <el-table-column prop="text" label="内容预览" show-overflow-tooltip />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="handleEditSample(row)">
                  编辑
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEditSampleDialog" title="编辑稿件" width="700px">
      <el-form v-if="editingSample" :model="editSampleForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="editSampleForm.title" />
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="editSampleForm.source" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="editSampleForm.text" type="textarea" :rows="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditSampleDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingSample" @click="handleSaveSample">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showImportDialog" :title="`导入稿件 - ${importingAuthor?.name}`" width="600px">
      <el-form :model="importForm" label-width="80px">
        <el-form-item label="选择文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="10"
            accept=".txt,.md,.xlsx,.xls"
            :file-list="importFileList"
            @change="handleImportFileChange"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 .txt, .md, .xlsx, .xls 格式</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="来源说明">
          <el-input v-model="importForm.source" placeholder="可选，标识这批稿件的来源" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" :loading="importing" :disabled="importFiles.length === 0" @click="handleConfirmImport">
          导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { authorsApi, samplesApi } from '@/services/api'
import type { AuthorProfile } from '@/types'

const emit = defineEmits<{
  select: [author: AuthorProfile]
  'author-created': []
  'samples-imported': [authorId: string]
}>()

const authors = ref<AuthorProfile[]>([])
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const showEditSampleDialog = ref(false)
const showImportDialog = ref(false)
const createLoading = ref(false)
const savingSample = ref(false)
const importing = ref(false)
const selectedAuthor = ref<AuthorProfile | null>(null)
const importingAuthor = ref<AuthorProfile | null>(null)
const authorSamples = ref<any[]>([])
const editingSample = ref<any>(null)
const importFiles = ref<File[]>([])
const importFileList = ref<any[]>([])

const createForm = reactive({
  name: '',
  description: ''
})

const importForm = reactive({
  source: ''
})

const editSampleForm = reactive({
  title: '',
  source: '',
  text: ''
})

const loadAuthors = async () => {
  try {
    const { data } = await authorsApi.listAuthors()
    authors.value = data
  } catch (error) {
    console.error('Failed to load authors:', error)
  }
}

const handleCreate = async () => {
  if (!createForm.name.trim()) {
    ElMessage.warning('请输入作者名称')
    return
  }

  createLoading.value = true
  try {
    const { data } = await authorsApi.createAuthor(createForm)
    ElMessage.success('作者档案创建成功')
    showCreateDialog.value = false
    createForm.name = ''
    createForm.description = ''
    emit('author-created')
    await loadAuthors()
  } catch (error) {
    ElMessage.error('创建失败')
    console.error(error)
  } finally {
    createLoading.value = false
  }
}

const handleSelect = async (author: AuthorProfile) => {
  selectedAuthor.value = author
  showDetailDialog.value = true
  emit('select', author)
  
  try {
    const { data } = await authorsApi.getAuthorSamples(author.id)
    authorSamples.value = data
  } catch (error) {
    console.error('Failed to load samples:', error)
    authorSamples.value = []
  }
}

const handleEditSample = (sample: any) => {
  editingSample.value = sample
  editSampleForm.title = sample.title || ''
  editSampleForm.source = sample.source || ''
  editSampleForm.text = sample.text || ''
  showEditSampleDialog.value = true
}

const handleSaveSample = async () => {
  if (!editingSample.value) return
  
  savingSample.value = true
  try {
    const response = await fetch(`/api/samples/${editingSample.value.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: editSampleForm.title,
        source: editSampleForm.source,
        text: editSampleForm.text
      })
    })
    
    if (response.ok) {
      ElMessage.success('保存成功')
      showEditSampleDialog.value = false
      
      if (selectedAuthor.value) {
        const { data } = await authorsApi.getAuthorSamples(selectedAuthor.value.id)
        authorSamples.value = data
      }
    } else {
      ElMessage.error('保存失败')
    }
  } catch (error) {
    console.error('Failed to save sample:', error)
    ElMessage.error('保存失败')
  } finally {
    savingSample.value = false
  }
}

const handleImportSamples = (author: AuthorProfile) => {
  importingAuthor.value = author
  importFiles.value = []
  importFileList.value = []
  importForm.source = ''
  showImportDialog.value = true
}

const handleImportFileChange = (file: any) => {
  importFiles.value.push(file.raw)
  importFileList.value.push(file)
}

const handleConfirmImport = async () => {
  if (!importingAuthor.value || importFiles.value.length === 0) return

  importing.value = true
  try {
    await samplesApi.importSamples(
      importFiles.value,
      importingAuthor.value.name,
      importForm.source || '批量导入',
      'zh',
      importingAuthor.value.id
    )
    ElMessage.success(`成功导入 ${importFiles.value.length} 个文件`)
    showImportDialog.value = false
    loadAuthors()
    emit('samples-imported', importingAuthor.value.id)
  } catch (error) {
    ElMessage.error('导入失败')
    console.error(error)
  } finally {
    importing.value = false
  }
}

const handleDelete = async (author: AuthorProfile) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除作者档案 "${author.name}" 吗？\n（稿件和风格不会被删除）`,
      '删除确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )

    await authorsApi.deleteAuthor(author.id)
    ElMessage.success('删除成功')
    loadAuthors()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadAuthors()
})

defineExpose({
  loadAuthors
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.author-detail {
  padding: 10px 0;
}

.samples-section {
  margin-top: 24px;
}

.samples-section h3 {
  font-size: 16px;
  color: #333;
  margin-bottom: 12px;
}
</style>