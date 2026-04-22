nanochat-personal-style/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 入口
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── styles.py        # 风格管理 API
│   │   │   └── rewrite.py       # 改写 API
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py        # 配置
│   │   │   └── llm.py           # LLM 集成
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py       # Pydantic 模型
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── style_analyzer.py  # 风格分析服务
│   │       └── style_rewriter.py  # 风格改写服务
│   ├── data/
│   │   └── styles/              # 风格数据存储
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── StyleUploader.tsx
│   │   │   ├── StyleSelector.tsx
│   │   │   └── ArticleRewriter.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
└── README.md