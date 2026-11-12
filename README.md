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
