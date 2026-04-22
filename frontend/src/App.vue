<template>
  <div id="app">
    <el-container>
      <el-header>
        <div class="header-main">
          <div class="logo">
            <h1>舟传媒科技部</h1>
            <span>风格仿写系统</span>
          </div>
          
          <el-menu
            mode="horizontal"
            :default-active="currentSection"
            class="nav-menu"
            @select="handleNavSelect"
          >
            <el-menu-item index="author-list">作者稿件维护</el-menu-item>
            
            <el-sub-menu index="training">
              <template #title>训练模型</template>
              <el-menu-item index="style">创建风格</el-menu-item>
              <el-menu-item index="training">训练管理</el-menu-item>
            </el-sub-menu>
            
            <el-menu-item index="rewrite">生成文本</el-menu-item>
          </el-menu>
        </div>
      </el-header>

      <el-main>
        <div class="content-wrapper">
          <div class="content-header">
            <h2>{{ currentTitle }}</h2>
          </div>
          <transition name="fade" mode="out-in">
            <component :is="currentComponent" :key="currentSection" ref="currentRef" />
          </transition>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, markRaw } from 'vue'
import AuthorManager from '@/components/AuthorManager.vue'
import StyleUploader from '@/components/StyleUploader.vue'
import StyleSelector from '@/components/StyleSelector.vue'
import TrainingManager from '@/components/TrainingManager.vue'
import ArticleRewriter from '@/components/ArticleRewriter.vue'

const componentMap: Record<string, any> = {
  'author-list': markRaw(AuthorManager),
  'upload': markRaw(StyleUploader),
  'style': markRaw(StyleSelector),
  'training': markRaw(TrainingManager),
  'rewrite': markRaw(ArticleRewriter)
}

const titleMap: Record<string, string> = {
  'author-list': '作者列表',
  'style': '创建风格',
  'training': '训练管理',
  'rewrite': '生成文本'
}

const currentSection = ref('author-list')
const currentRef = ref()

const currentComponent = computed(() => componentMap[currentSection.value])
const currentTitle = computed(() => titleMap[currentSection.value] || '')

const handleNavSelect = (key: string) => {
  currentSection.value = key
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  height: 100vh;
}

.el-container {
  height: 100%;
}

.el-header {
  background: #fff;
  padding: 0;
  border-bottom: 1px solid #e8e8e8;
}

.header-main {
  display: flex;
  align-items: center;
  height: 60px;
  padding: 0 24px;
}

.logo {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-right: 40px;
}

.logo h1 {
  color: #333;
  font-size: 20px;
}

.logo span {
  color: #999;
  font-size: 12px;
}

.nav-menu {
  border-bottom: none;
  background: transparent;
  flex: 1;
}

.nav-menu .el-menu-item,
.nav-menu .el-sub-menu__title {
  color: #666;
  font-size: 14px;
}

.nav-menu .el-menu-item:hover,
.nav-menu .el-sub-menu__title:hover {
  background: #f5f7fa;
}

.nav-menu .el-menu-item.is-active,
.nav-menu .el-sub-menu.is-active .el-sub-menu__title {
  color: #667eea;
  background: #f5f7fa;
}

.nav-menu .el-sub-menu .el-menu-item {
  color: #333;
}

.nav-menu .el-sub-menu .el-menu-item:hover {
  background: #f5f7fa;
}

.el-main {
  background: #f5f7fa;
  padding: 24px;
}

.content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
}

.content-header {
  margin-bottom: 20px;
}

.content-header h2 {
  font-size: 20px;
  color: #333;
  font-weight: 600;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
