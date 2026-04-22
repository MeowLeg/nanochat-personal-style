<template>
  <div class="training-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>风格模型训练</span>
          <el-button type="primary" @click="refresh">刷新</el-button>
        </div>
      </template>

      <el-table :data="jobs" stripe style="width: 100%">
        <el-table-column prop="job_id" label="任务ID" width="100" />
        <el-table-column prop="style_name" label="风格名称" width="150" />
        <el-table-column prop="model_name" label="使用模型" width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="180">
          <template #default="{ row }">
            <el-progress :percentage="Math.round(row.progress * 100)" :status="getProgressStatus(row.status)" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetails(row)">
              详情
            </el-button>
            <el-button link type="danger" @click="deleteJobConfirm(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="detailsVisible" title="训练任务详情" width="550px">
      <div v-if="selectedJob" class="job-details">
        <p><strong>任务 ID:</strong> {{ selectedJob.job_id }}</p>
        <p><strong>风格名称:</strong> {{ selectedJob.style_name }}</p>
        <p><strong>使用模型:</strong> {{ selectedJob.model_name }}</p>
        <p><strong>状态:</strong>
          <el-tag :type="getStatusType(selectedJob.status)">
            {{ getStatusText(selectedJob.status) }}
          </el-tag>
        </p>
        <p><strong>进度:</strong> {{ Math.round(selectedJob.progress * 100) }}%</p>
        <p><strong>创建时间:</strong> {{ formatDate(selectedJob.created_at) }}</p>
        <p v-if="selectedJob.started_at"><strong>开始时间:</strong> {{ formatDate(selectedJob.started_at) }}</p>
        <p v-if="selectedJob.completed_at"><strong>完成时间:</strong> {{ formatDate(selectedJob.completed_at) }}</p>
        <p v-if="selectedJob.error_message" style="color: var(--el-color-danger)">
          <strong>错误信息:</strong> {{ selectedJob.error_message }}
        </p>
      </div>
      <template #footer>
        <el-button @click="detailsVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { trainingApi } from '@/services/api'
import type { TrainingJob } from '@/types'

const jobs = ref<TrainingJob[]>([])
const detailsVisible = ref(false)
const selectedJob = ref<TrainingJob | null>(null)
let pollInterval: number | null = null

const hasRunningJobs = computed(() => {
  return jobs.value.some(job => job.status === 'pending' || job.status === 'running')
})

const getPollInterval = () => {
  return hasRunningJobs.value ? 3000 : 10000
}

const loadJobs = async () => {
  try {
    const { data } = await trainingApi.listJobs()
    const hadRunningJobs = hasRunningJobs.value
    jobs.value = data
    
    if (hadRunningJobs !== hasRunningJobs.value) {
      updatePollInterval()
    }
  } catch (error) {
    console.error('Failed to load jobs:', error)
  }
}

const updatePollInterval = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
  pollInterval = window.setInterval(loadJobs, getPollInterval())
}

const refresh = () => {
  loadJobs()
  ElMessage.success('已刷新')
}

const viewDetails = (job: TrainingJob) => {
  selectedJob.value = job
  detailsVisible.value = true
}

const deleteJobConfirm = async (job: TrainingJob) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除训练任务「${job.style_name}」吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await trainingApi.deleteJob(job.job_id)
    ElMessage.success('删除成功')
    loadJobs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('Failed to delete job:', error)
    }
  }
}

const getStatusType = (status: string) => {
  const map: Record<string, any> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '等待中',
    running: '训练中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

const getProgressStatus = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return undefined
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadJobs()
  pollInterval = window.setInterval(loadJobs, getPollInterval())
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
})

defineExpose({
  loadJobs
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.job-details p {
  margin: 10px 0;
}
</style>
