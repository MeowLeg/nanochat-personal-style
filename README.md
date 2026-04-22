# NanoChat 个人写作风格改写系统

基于 karpathy/nanochat 框架的二次开发项目，支持导入历史稿件、学习写作风格、智能改写文章。

## 功能特性

- 📝 **稿件导入** - 支持批量上传 .txt/.md 格式的历史稿件
- 🎨 **风格学习** - 自动分析写作样本，提取风格特征（词汇密度、句式结构、语气等）
- ✨ **智能改写** - 基于目标风格对文章进行改写，保持原意的同时体现风格特点
- 🎛️ **风格强度控制** - 可调节风格改写的强度（0-1）
- 📊 **风格配置管理** - 创建和管理多个风格配置文件

## 技术栈

### 后端
- FastAPI - Web 框架
- OpenAI API - LLM 集成
- Python 3.9+

### 前端
- Vue 3 - UI 框架
- Element Plus - 组件库
- Vite - 构建工具

## 快速开始

### 1. 环境配置

#### 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 OpenAI API Key
```

#### 前端设置

```bash
cd frontend

# 安装依赖
npm install
```

### 2. 启动服务

#### 启动后端

```bash
cd backend
source venv/bin/activate
python -m app.main
```

后端服务将在 http://localhost:8000 启动，API 文档访问 http://localhost:8000/docs

#### 启动前端

新开一个终端：

```bash
cd frontend
npm run dev
```

前端将在 http://localhost:3000 启动

## 使用指南

### 步骤 1: 导入稿件

1. 点击「导入稿件」标签
2. 拖拽或点击上传历史写作样本（支持 .txt, .md）
3. 输入作者名称和来源说明
4. 点击「导入样本」

### 步骤 2: 创建风格配置

1. 点击「创建风格」标签
2. 输入风格名称和描述
3. 从已导入的样本中选择关联样本
4. 点击「创建风格配置」

### 步骤 3: 改写文章

1. 点击「文章改写」标签
2. 在左侧输入需要改写的原文
3. 选择目标风格
4. 调整风格强度（可选）
5. 点击「开始改写」

## 项目结构

```
nanochat-personal-style/
├── backend/
│   ├── app/
│   │   ├── api/              # API 路由
│   │   │   ├── styles.py     # 风格管理接口
│   │   │   └── rewrite.py    # 改写接口
│   │   ├── core/             # 核心模块
│   │   │   ├── config.py     # 配置
│   │   │   └── llm.py        # LLM 集成
│   │   ├── models/           # 数据模型
│   │   ├── services/         # 业务服务
│   │   │   ├── style_analyzer.py  # 风格分析
│   │   │   └── style_rewriter.py  # 风格改写
│   │   └── main.py           # FastAPI 入口
│   ├── data/                 # 数据存储
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # Vue 组件
│   │   │   ├── StyleUploader.vue
│   │   │   ├── StyleSelector.vue
│   │   │   └── ArticleRewriter.vue
│   │   ├── services/         # API 服务
│   │   ├── types/            # TypeScript 类型
│   │   ├── App.vue
│   │   └── main.ts
│   └── package.json
└── README.md
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/samples/import` | POST | 导入写作样本 |
| `/api/samples` | GET | 获取样本列表 |
| `/api/style_profiles` | POST | 创建风格配置 |
| `/api/style_profiles` | GET | 获取风格配置列表 |
| `/api/rewrite` | POST | 文章改写 |

详细文档请访问 http://localhost:8000/docs

## 风格分析特征

系统分析以下写作风格特征：

- 词汇密度 - 内容词占比
- 平均句长 - 句子长度统计
- 标点模式 - 标点使用习惯
- 语气正式度 - 正式/非正式倾向
- 句式多样性 - 句子结构变化
- 词汇丰富度 - 用词多样性

## 注意事项

1. **API Key**: 需要有效的 OpenAI API Key（或兼容的 API）
2. **样本质量**: 建议提供至少 3-5 篇高质量的写作样本
3. **样本长度**: 单篇样本建议 500 字以上
4. **成本控制**: 改写会消耗 Token，请注意使用量

## License

MIT