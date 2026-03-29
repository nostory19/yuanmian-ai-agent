# yuanmian-ai-agent

基于 **FastAPI + LangGraph** 的独立 Agent 服务，作为三层架构中的 Agent 层。

## 目录结构

```text
yuanmian-ai-agent/
├── app/
│   ├── api/                    # API 接口层（路由、请求响应模型）
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── routes.py
│   ├── application/            # 应用服务层（编排调用）
│   │   ├── __init__.py
│   │   └── assistant_app_service.py
│   ├── domain/                 # 领域层（核心业务规则）
│   │   ├── __init__.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── intent_service.py
│   ├── graph/                  # LangGraph 工作流层
│   │   ├── __init__.py
│   │   └── workflow.py
│   ├── infrastructure/         # 基础设施层（模型/外部服务接入）
│   │   ├── __init__.py
│   │   └── llm_client.py
│   ├── prompt/                 # Prompt 模板
│   │   ├── __init__.py
│   │   └── system_prompt.txt
│   ├── __init__.py
│   ├── config.py               # 配置
│   └── main.py                 # FastAPI 启动入口
├── assets/                     # 资源目录（预留）
├── doc/                        # 文档目录（预留）
├── .env.example                # 环境变量示例
├── .gitignore
├── get_graph_img.ipynb         # 工作流可视化预留 notebook
├── requirements.txt
└── run.py
```

## 启动方式

```bash
pip install -r requirements.txt
python run.py
```

默认地址：`http://localhost:8291`
运行访问： `http://0.0.0.0:8291/docs` 查看 Swagger UI API 文档

## 环境变量

参考 `.env.example` 配置以下变量后启动：

- `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL_NAME`
- `OPENAI_SMALL_API_KEY` / `OPENAI_SMALL_BASE_URL` / `OPENAI_SMALL_MODEL_NAME`

说明：
- 主模型用于一般回复；
- 小模型用于短输入场景（当前按消息长度自动选择）；
- 若 LLM 调用失败，服务会自动回退到规则回复，保障可用性。

## 已提供接口

- `GET /agent/health`：健康检查
- `POST /agent/chat`：普通对话
- `POST /agent/chat-stream`：SSE 流式对话

## 与后端联调

后端 `application.yml` 配置：

```yaml
agent:
  base-url: http://localhost:8291
```

前端走后端网关接口：

- `POST /api/ai_assistant/chat`
- `POST /api/ai_assistant/chat-stream`
