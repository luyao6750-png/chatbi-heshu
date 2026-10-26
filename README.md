# ChatBI 数据可视化模块（独立抽取版）

从 [tiangong-agent](https://github.com/) 主项目的 `src/nl2sql` 模块抽取而来，实现「自然语言 → SQL 生成 → 执行 → 摘要 → 图表可视化」的完整链路，可脱离主项目单独运行。

## 目录结构

```
chatbi/
├── chatbi/                  # 核心包
│   ├── config.py            # 自包含配置（数据库 + LLM）
│   ├── database.py          # 自包含异步数据库会话
│   ├── engine.py            # NL2SQL 引擎（生成/校验/执行/摘要/重试/多轮）
│   ├── security.py          # SQL 安全校验 + 角色数据过滤
│   ├── prompts.py           # 表结构 / NL2SQL / 追问 / 摘要 / 图表推荐 Prompt
│   ├── chart_advisor.py     # LLM 图表推荐 + Plotly 渲染
│   ├── echarts_builder.py   # 结果 + 配置 → ECharts option JSON
│   └── router.py            # FastAPI 路由（返回 ECharts option）
├── app.py                   # Gradio 可视化面板（Plotly，端口 7861）
├── main.py                  # FastAPI 入口（ECharts option，端口 8081）
├── scripts/init_db.py       # 建库 + 建表 + 样例数据
├── requirements.txt
└── .env.example
```

> 与原主项目差异：`src.core.config` → `chatbi.config`、`src.infra.database` → `chatbi.database`，并剔除了 Redis/Milvus/Neo4j/MinIO 等与 ChatBI 无关的配置；`app.py` 的 LLM 模型统一走 `settings.CHAT_MODEL`。

## 快速开始

### 1. 安装依赖

建议复用主项目的 `tiangong` conda 环境（已装齐所有依赖），或新建环境：

```bash
conda create -n chatbi python=3.13 -y
conda activate chatbi
pip install -r requirements.txt
```

### 2. 配置

```bash
cp .env.example .env   # Windows: copy .env.example .env
```

编辑 `.env`，填写：

- 数据库连接（`DB_*`）——连到本地任意一个 PostgreSQL 实例即可（例如主项目 `docker compose` 起的那个）；
- `DASHSCOPE_API_KEY`（走 DashScope 兼容模式的 qwen 模型）。

> ⚠️ 默认使用独立的 `chatbi_db` 数据库，`init_db.py` 只会重建 `chatbi_db` 里的表，**不会**影响主项目的 `medical_db`。

### 3. 初始化演示数据

`scripts/init_db.py` 会自动建库（若 `chatbi_db` 不存在）、建 9 张表并灌入样例数据（科室/疾病/症状/药品/患者/问诊记录等），覆盖面板中的示例问题：

```bash
python scripts/init_db.py
```

### 4. 启动

两个入口任选其一：

- **Gradio 可视化面板**（交互式，Plotly 渲染，推荐先跑这个看效果）：

  ```bash
  python app.py          # 浏览器打开 http://localhost:7861
  ```

- **FastAPI 接口**（返回 ECharts option，供前端 `chart.setOption()`）：

  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8081 --reload
  # 或：python main.py
  ```

  接口：
  - `POST /api/v1/bi/query` — 查询（返回 sql + data + echarts_option）
  - `GET  /api/v1/bi/history/{session_id}` — 会话历史
  - `DELETE /api/v1/bi/history/{session_id}` — 清空会话
  - `GET  /health` — 健康检查

  示例请求：

  ```bash
  curl -X POST http://localhost:8081/api/v1/bi/query \
    -H "Content-Type: application/json" \
    -d '{"question": "各科室问诊量排名", "session_id": "demo", "role": "operator"}'
  ```

## 示例问题

- 各科室问诊量排名
- 库存不足 50 的药品有哪些
- 本月每天的问诊量趋势
- OTC 药品和处方药的数量对比
- 各科室常见疾病 TOP5
- 药品价格分布

## 安全设计

- 仅允许 `SELECT` 查询；
- 黑名单正则拦截 `INSERT/UPDATE/DELETE/DROP/ALTER/CREATE` 及 `patients.phone`/`id_card` 敏感字段；
- 无 `LIMIT` 时强制追加 `LIMIT 100`，执行超时 10 秒；
- `doctor` 角色自动注入 `department_id` 越权过滤。
