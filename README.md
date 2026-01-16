# 情感鸡尾酒推荐系统

基于用户故事的情感分析系统，通过语义分析、鸡尾酒调配、呈现和排版四个Agent，为用户推荐个性化的鸡尾酒并生成精美的名片卡片。

## ✨ 功能特性

- 🎤 **语音/文本输入**：支持用户语音输入或文本输入故事
- 🧠 **语义分析**：通过Grok/GPT-4分析用户情感，输出Energy/Tension/Control/Need四维度分析
- 🍸 **智能调配**：根据情感维度从数据库匹配最适合的鸡尾酒，并进行创意微调
- 🎨 **视觉生成**：使用DALL-E/Grok/Replicate生成真实的鸡尾酒图片
- 🎬 **制作视频**：使用Replicate Stable Video Diffusion生成鸡尾酒制作动画（可选）
- 📇 **精美名片**：自动排版生成左图右文的精美名片卡片，支持下载

## 🛠 技术栈

### 前端
- React 18 + TypeScript
- Vite
- Axios
- MediaRecorder API (音频录制)

### 后端
- Python 3.10+
- FastAPI
- **LLM服务**：Grok API (xAI) / OpenAI GPT-4
- **图片生成**：DALL-E / Grok Image Generation / Replicate Stable Diffusion
- **视频生成**：Replicate Stable Video Diffusion
- Pillow (图像处理和排版)
- httpx (HTTP客户端)

## 📁 项目结构

```
Alex-vibe-coding/
├── frontend/              # React前端应用
│   ├── src/
│   │   ├── components/    # React组件
│   │   │   ├── WelcomeScreen.tsx
│   │   │   ├── VoiceInputScreen.tsx  # 语音/文本输入界面
│   │   │   ├── LoadingScreen.tsx
│   │   │   └── ResultCard.tsx
│   │   ├── services/      # API服务
│   │   ├── hooks/         # React Hooks (useAudioRecorder)
│   │   └── App.tsx
│   └── package.json
├── backend/               # Python FastAPI后端
│   ├── app/
│   │   ├── agents/        # 四个核心Agent
│   │   │   ├── semantic_agent.py     # 语义分析Agent
│   │   │   ├── cocktail_agent.py     # 鸡尾酒调配Agent
│   │   │   ├── presentation_agent.py # 呈现Agent（图片、视频、命名）
│   │   │   ├── layout_agent.py       # 排版Agent
│   │   │   └── processor.py          # 流程编排
│   │   ├── services/      # API服务封装
│   │   │   ├── llm_service.py        # LLM服务（Grok/OpenAI）
│   │   │   ├── dalle_image_service.py
│   │   │   ├── grok_image_service.py
│   │   │   ├── image_service.py      # Replicate图片服务
│   │   │   └── video_service.py      # Replicate视频服务
│   │   ├── models/        # 数据模型
│   │   ├── utils/         # 工具类
│   │   └── main.py        # FastAPI应用入口
│   ├── generated_cards/   # 生成的名片图片
│   └── requirements.txt
├── cocktails.json         # 鸡尾酒数据库
├── .env                   # 环境变量配置（需自行创建）
└── README.md
```

## 🚀 快速开始

### 前置要求

- **Node.js 18+**
- **Python 3.10+**
- **API密钥**（至少需要以下之一）：
  - `GROK_API_KEY` - Grok API密钥（推荐，用于LLM和图片生成）
  - `OPENAI_API_KEY` - OpenAI API密钥（用于GPT-4和DALL-E，可选）
  - `REPLICATE_API_TOKEN` - Replicate API令牌（用于图片/视频生成，可选）

### 环境变量配置

在项目根目录创建 `.env` 文件：

```env
# Grok API (推荐)
GROK_API_KEY=your_grok_api_key_here
GROK_API_BASE=https://api.x.ai/v1

# OpenAI API (可选)
OPENAI_API_KEY=your_openai_api_key_here

# Replicate API (可选，用于图片/视频生成)
REPLICATE_API_TOKEN=your_replicate_api_token_here

# 服务器配置
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
```

### 后端设置

1. **进入后端目录：**
```bash
cd backend
```

2. **创建虚拟环境（推荐）：**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **安装依赖：**
```bash
pip install -r requirements.txt
```

4. **启动后端服务：**
```bash
# 方式1：直接运行
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式2：使用批处理文件（Windows）
# 在项目根目录运行
start_backend.bat
```

后端将在 `http://localhost:8000` 运行。

### 前端设置

1. **进入前端目录：**
```bash
cd frontend
```

2. **安装依赖：**
```bash
npm install
```

3. **启动开发服务器：**
```bash
npm run dev
```

前端将在 `http://localhost:5173` 运行。

**提示**：可以使用批处理文件快速启动：
- Windows: `start_backend.bat` 和 `start_frontend.bat`

## 🔄 使用流程

1. **进入欢迎界面**：打开 `http://localhost:5173`，点击"来一杯吧"按钮
2. **输入故事**：
   - 选择"🎤 语音输入"：点击录音按钮开始录音，再次点击停止并提交
   - 选择"✍️ 文字输入"：在文本框中输入您的故事，点击提交
3. **等待处理**：系统会自动进行以下处理：
   - 语义分析：分析情感维度（Energy/Tension/Control/Need）
   - 鸡尾酒匹配：从数据库匹配最适合的鸡尾酒
   - 创意调配：根据情感需求微调配方
   - 视觉生成：生成鸡尾酒图片和制作视频
   - 创意命名：生成四字中文名称
   - 名片排版：生成左图右文的精美名片
4. **查看结果**：查看生成的专属鸡尾酒名片，可下载保存

## 📡 API端点

### POST `/api/process-story`
处理用户故事（开始处理流程）

**请求体：**
```json
{
  "audio_url": "可选，音频文件URL",
  "text": "可选，直接文本输入"
}
```

**响应：**
```json
{
  "task_id": "任务ID",
  "status": "processing"
}
```

### GET `/api/process-status/{task_id}`
获取处理状态和进度

**响应：**
```json
{
  "task_id": "任务ID",
  "status": "completed|processing|failed",
  "progress": {
    "step": "当前步骤描述",
    "progress": 80
  },
  "result": {
    "semantic_analysis": {...},
    "cocktail_mix": {...},
    "presentation": {...},
    "layout": {...}
  }
}
```

### GET `/generated_cards/{filename}`
访问生成的名片图片（静态文件服务）

## 🎨 核心功能说明

### Agent架构

系统包含4个主要Agent，按顺序执行：

1. **语义分析Agent** (`semantic_agent.py`)
   - 分析用户故事的情感维度
   - 输出Energy/Tension/Control/Need（1-5分）
   - 识别情感需求（Need）和细微情感
   - 生成300字以内的正面回复

2. **鸡尾酒调配Agent** (`cocktail_agent.py`)
   - 从`cocktails.json`数据库匹配最适合的鸡尾酒
   - 根据情感需求创意调整配方
   - 使用8大类别配料：Base Spirit, Modifier, Fruit/Juice, Spice/Botanical, Tea/Coffee, Fermentation, Fat/Texture, Umami/Saline

3. **呈现Agent** (`presentation_agent.py`)
   - 生成创意四字中文名称（避免"XX之酒"等俗套）
   - 生成真实鸡尾酒图片（根据配方显示正确颜色、高级酒杯、装饰品）
   - 生成鸡尾酒制作动画视频（可选）

4. **排版Agent** (`layout_agent.py`)
   - 简化300字回复为2句叙事性文字（避免主语）
   - 将图片和文字排版成名片（左图右文）
   - 使用中文字体（华文行楷/楷体）
   - 支持图片下载

### 鸡尾酒数据库

`cocktails.json` 包含完整的鸡尾酒数据库，每个条目包含：
- `Name`: 鸡尾酒名称
- `Category`: 类别
- `Energy/Tension/Control`: 情感维度（1-5）
- `Need`: 情感需求列表（如：restraint, balance, comfort）
- `Recipe`: 配方
- `Description`: 描述

### 图片生成特性

- **真实鸡尾酒照片**：强调"photorealistic"、"actual drinkable beverage"
- **根据配方显示颜色**：自动分析基础酒和调制剂，生成准确的颜色描述
- **高级酒杯**：随机选择高级玻璃杯（水晶、有色玻璃等）
- **装饰元素**：吸管、冰块、创意牙签+水果切片
- **手部位置**：酒保的手在酒杯后面，不遮挡鸡尾酒

## 🌐 网络访问

系统默认配置为允许本地网络访问：

- **后端**：`--host 0.0.0.0` 允许局域网访问
- **前端**：Vite配置 `server.host: '0.0.0.0'`

其他设备可以通过 `http://[你的IP地址]:5173` 访问前端。

## ⚠️ 注意事项

1. **API密钥配置**：确保至少配置了`GROK_API_KEY`或`OPENAI_API_KEY`
2. **成本控制**：图片和视频生成API调用成本较高，建议：
   - 使用Grok API（相对便宜）
   - 实现结果缓存机制
   - 控制并发请求
3. **异步处理**：长时间运行的任务使用后台任务处理，前端通过轮询获取进度
4. **错误处理**：各Agent都包含错误处理和降级机制，确保系统稳定性
5. **图片加载**：确保图片完全加载后再进行排版，避免出现灰色区域

## 🔧 开发说明

### 代码风格
- 后端使用Python类型提示
- 前端使用TypeScript
- 所有API服务都有错误处理和日志记录

### 扩展开发
- 添加新的Agent：在`backend/app/agents/`目录创建新文件
- 添加新的API服务：在`backend/app/services/`目录创建新文件
- 修改名片样式：编辑`backend/app/agents/layout_agent.py`的`_design_card`方法

## 📝 许可证

MIT License

## 🙏 致谢

- [xAI Grok](https://x.ai/) - LLM和图片生成服务
- [OpenAI](https://openai.com/) - GPT-4和DALL-E服务
- [Replicate](https://replicate.com/) - Stable Diffusion和视频生成
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能Python Web框架
- [React](https://react.dev/) - UI框架
