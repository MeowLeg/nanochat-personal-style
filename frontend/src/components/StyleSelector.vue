<template>
  <div class="style-creator">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>创建风格配置文件</span>
        </div>
      </template>

      <el-form :model="form" label-width="100px">
        <el-form-item label="选择作者" required>
          <el-select v-model="form.authorId" placeholder="请选择作者" clearable filterable style="width: 100%" @focus="loadAuthors" @change="handleAuthorChange">
            <el-option
              v-for="author in authors"
              :key="author.id"
              :label="`${author.name} (${author.sample_count} 篇稿件)`"
              :value="author.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="风格名称" required>
          <el-input v-model="form.name" placeholder="给这个风格起个名字" />
        </el-form-item>
        <el-form-item label="风格描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="描述一下这个风格的特点" />
        </el-form-item>
        <el-form-item label="选择样本" required v-if="form.authorId">
          <div class="sample-selection-header">
            <span>该作者共 {{ filteredSamples.length }} 个样本，已选 {{ selectedSampleIds.length }} 个</span>
            <el-button-group>
              <el-button size="small" @click="selectAll">
                全选
              </el-button>
              <el-button size="small" @click="deselectAll">
                取消全选
              </el-button>
            </el-button-group>
          </div>
          <div class="sample-table-container">
            <el-table
              ref="sampleTableRef"
              :data="paginatedSamples"
              @selection-change="handleSelectionChange"
              style="width: 100%"
              height="400"
            >
              <el-table-column type="selection" width="55" />
              <el-table-column prop="author_name" label="作者" width="120" />
              <el-table-column prop="source" label="来源" show-overflow-tooltip />
              <el-table-column prop="length_chars" label="字数" width="100">
                <template #default="{ row }">
                  {{ row.length_chars.toLocaleString() }}
                </template>
              </el-table-column>
              <el-table-column prop="date_collected" label="导入时间" width="180">
                <template #default="{ row }">
                  {{ formatDate(row.date_collected) }}
                </template>
              </el-table-column>
              <el-table-column label="预览" min-width="200">
                <template #default="{ row }">
                  <span class="text-preview">{{ row.text.slice(0, 80) }}{{ row.text.length > 80 ? '...' : '' }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[20, 50, 100]"
              :total="filteredSamples.length"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleCreate" :disabled="!form.authorId">
            创建风格配置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>已有风格配置</span>
        </div>
      </template>

      <el-table :data="profiles" stripe>
        <el-table-column prop="name" label="风格名称" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="sample_ids" label="样本数量">
          <template #default="{ row }">
            {{ row.sample_ids?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleTrain(row)" :disabled="row.sample_ids.length < 3">
              训练模型
            </el-button>
            <el-button link type="primary" @click="handleSelect(row)">
              选择
            </el-button>
            <el-button link type="danger" @click="deleteProfileConfirm(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="trainDialogVisible" title="训练模型" width="500px">
      <el-form :model="trainForm" label-width="120px">
        <el-form-item label="选择模型">
          <el-select v-model="trainForm.modelName" placeholder="请选择要使用的模型" @focus="loadNanochatModels">
            <el-option
              v-for="model in availableModels"
              :key="model.name"
              :label="`${model.display_name} (${model.params}参数, 需${model.min_vram_gb}GB显存)`"
              :value="model.name"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <div style="font-size: 12px; color: var(--el-color-info);">
            <p>💡 提示：</p>
            <p>• 使用 nanochat (nanoGPT) 进行风格训练</p>
            <p>• 训练将在后台异步执行</p>
            <p>• 点击「开始训练」后会自动跳转到训练页面</p>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="trainDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="trainLoading" @click="confirmTrain">
          开始训练
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { samplesApi, stylesApi, trainingApi, authorsApi } from '@/services/api'
import type { WritingSample, StyleProfile, MLXModel, AuthorProfile } from '@/types'

const emit = defineEmits<{
  select: [profile: StyleProfile]
  'train-started': [jobId: string]
}>()

const loading = ref(false)
const trainLoading = ref(false)
const trainDialogVisible = ref(false)
const currentTrainingProfile = ref<StyleProfile | null>(null)
const sampleTableRef = ref()

const samples = ref<WritingSample[]>([])
const profiles = ref<StyleProfile[]>([])
const authors = ref<AuthorProfile[]>([])
const availableModels = ref<any[]>([])
const selectedSampleIds = ref<string[]>([])
const selectedSamples = ref<WritingSample[]>([])

const currentPage = ref(1)
const pageSize = ref(20)

const form = reactive({
  authorId: '',
  name: '',
  description: ''
})

const trainForm = reactive({
  modelName: ''
})

const filteredSamples = computed(() => {
  if (!form.authorId) return []
  return samples.value.filter(s => s.author_id === form.authorId)
})

const paginatedSamples = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredSamples.value.slice(start, end)
})

const loadAuthors = async () => {
  try {
    const { data } = await authorsApi.listAuthors()
    authors.value = data
  } catch (error) {
    console.error('Failed to load authors:', error)
  }
}

const loadSamples = async () => {
  try {
    const { data } = await samplesApi.listSamples()
    samples.value = data
  } catch (error) {
    console.error('Failed to load samples:', error)
  }
}

const loadProfiles = async () => {
  try {
    const { data } = await stylesApi.listProfiles()
    profiles.value = data
  } catch (error) {
    console.error('Failed to load profiles:', error)
  }
}

const loadModels = async () => {
  try {
    const { data } = await trainingApi.listModels()
    availableModels.value = data.models || []
    if (availableModels.value.length > 0) {
      trainForm.modelName = availableModels.value[0].name
    }
  } catch (error) {
    console.error('Failed to load models:', error)
  }
}

const loadNanochatModels = async () => {
  try {
    const { data } = await trainingApi.listNanochatModels()
    availableModels.value = data.models || []
    if (availableModels.value.length > 0 && !trainForm.modelName) {
      trainForm.modelName = availableModels.value[0].name
    }
  } catch (error) {
    console.error('Failed to load nanochat models:', error)
  }
}

const handleAuthorChange = async () => {
  currentPage.value = 1
  selectedSampleIds.value = []
  selectedSamples.value = []

  await nextTick()

  if (form.authorId && filteredSamples.value.length > 0) {
    selectAll()

    await nextTick()

    if (sampleTableRef.value) {
      filteredSamples.value.forEach(sample => {
        sampleTableRef.value.toggleRowSelection(sample, true)
      })
    }
  }
}

const handleSelectionChange = (selection: WritingSample[]) => {
  selectedSamples.value = selection
  selectedSampleIds.value = selection.map(s => s.id)
}

const selectAll = () => {
  selectedSampleIds.value = filteredSamples.value.map(s => s.id)
  selectedSamples.value = [...filteredSamples.value]
}

const deselectAll = () => {
  selectedSampleIds.value = []
  selectedSamples.value = []
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}

const handleCreate = async () => {
  if (!form.authorId) {
    ElMessage.warning('请先选择作者')
    return
  }
  if (!form.name.trim()) {
    ElMessage.warning('请输入风格名称')
    return
  }
  if (!selectedSampleIds.value.length) {
    ElMessage.warning('请至少选择一个样本')
    return
  }

  loading.value = true
  try {
    const { data } = await stylesApi.createProfile({
      name: form.name,
      description: form.description,
      sample_ids: selectedSampleIds.value,
      author_id: form.authorId
    })
    ElMessage.success('风格配置创建成功')
    profiles.value.push(data)
    form.name = ''
    form.description = ''
    form.authorId = ''
    selectedSampleIds.value = []
    selectedSamples.value = []
    loadAuthors()
  } catch (error) {
    ElMessage.error('创建失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleTrain = async (profile: StyleProfile) => {
  if (profile.sample_ids.length < 3) {
    ElMessage.warning('至少需要 3 个样本才能训练')
    return
  }

  currentTrainingProfile.value = profile
  await loadModels()
  trainDialogVisible.value = true
}

const confirmTrain = async () => {
  if (!currentTrainingProfile.value) return

  trainLoading.value = true
  try {
    const { data } = await trainingApi.createJob(
      currentTrainingProfile.value,
      trainForm.modelName || undefined
    )
    ElMessage.success(`训练任务已创建，任务 ID: ${data.job_id}，正在跳转到训练页面...`)
    trainDialogVisible.value = false
    
    setTimeout(() => {
      emit('train-started', data.job_id)
    }, 500)
  } catch (error: any) {
    ElMessage.error('创建训练任务失败')
    console.error(error)
  } finally {
    trainLoading.value = false
  }
}

const handleSelect = (profile: StyleProfile) => {
  emit('select', profile)
}

const deleteProfileConfirm = async (profile: StyleProfile) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除风格配置「${profile.name}」吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await stylesApi.deleteProfile(profile.id)
    ElMessage.success('删除成功')
    loadProfiles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('Failed to delete profile:', error)
    }
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadAuthors()
  loadSamples()
  loadProfiles()
})

defineExpose({
  loadAuthors,
  loadSamples,
  loadProfiles
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sample-selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.sample-table-container {
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
}

.text-preview {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.pagination-container {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>