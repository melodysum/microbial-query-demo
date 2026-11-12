# 微生物信息查询平台 Demo

用于验证分类筛选、自然语言受控解析、菌株详情、文献库和 FASTA 近邻检索的完整链路。

## 本地运行

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m backend.db
npm ci
npm run build
npm run dev
```

默认前端为 `http://localhost:7100`，后端 API 为 `http://localhost:8000`。

## 服务器内部部署

项目目录：`/media/desk16/te188122/LZ/microbial-query-demo`

```bash
cd /media/desk16/te188122/LZ/microbial-query-demo
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 7100
```

服务只监听服务器本地地址。通过 VS Code Remote-SSH 端口转发，或在 Mac 上执行：

```bash
ssh -L 7100:127.0.0.1:7100 lz-cloud
```

然后访问 `http://localhost:7100`。

## 数据边界

- 12 个基因组来自用户项目数据，服务器端近邻检索使用 skani 0.4.0。
- 当前 138 条性状记录是合成演示值，仅用于验证查询逻辑，不能用于科研判断。
- 文献库包含 6 条核心题录和 64 条分享线索。未提供的 DOI／网址保持为空，分享线索未核对原文。
- 当前没有配置 GPU 或本地千问；自然语言使用透明的受控规则解析。
- 本地没有 skani 时，序列检索明确降级为规范 21-mer Jaccard，分数不与 ANI 混称。

## 验收结果

- 初始菌株记录 12 条，自然语言示例返回 4 条。
- 核心文献 6 条，分享线索 64 条。
- 服务器端基因组自比对返回 ANI 100%。
- 浏览器控制台错误 0，HTTP 404 为 0，移动端无页面级横向溢出。

## 大参考库策略

四个 ANI 物种的原始基因组只保存在新服务器，不直接提交到 GitHub。`data/library_sources.json` 记录数据集、预期文件数、服务器路径和传输状态；GitHub 仅保存代码、配置和小型演示数据。

大库索引位于 `/media/desk16/te188122/LZ/genome-library/indexes/<物种>`，与应用程序目录分离，避免更新代码时覆盖索引。只有对应目录下的 `READY` 标记存在时，该物种才被视为可查询。

- `GET /api/library`：返回各数据集的文件数、传输状态和索引进度。
- `POST /api/sequence/search` 携带 `library=four_species`：使用 `skani search` 对四物种预建索引做最近邻检索。
- 默认 `library=demo`：继续使用 12 株演示库，不受大库索引构建进度影响。
- 传输完成不等于索引就绪；未完成索引时接口会明确返回原因，不使用全对全 `triangle` 冒充大库查询。

## 界面语言与样式

- 默认英文界面，可通过右上角按钮切换中文，语言偏好保存在当前浏览器。
- 自然语言查询支持中英文关键词，结构化筛选条件在执行前展示。
- 界面采用克制的学术风：中性色、衬线标题、细边框和清晰的数据表，不使用宣传式 AI 文案。
- 桌面与移动端分别验收；手机端导航分行显示，避免横向溢出。
