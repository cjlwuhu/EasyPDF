# EasyPDF

EasyPDF 是一个本地优先的论文 PDF 阅读与翻译工具。它面向英文论文阅读场景，支持上传 PDF、提取段落、按段生成中文译文、维护术语表，并将整篇中文译文导出为 Word 文档。

## 主要功能

- PDF 阅读工作台：原始 PDF、英文提取段落、中文译文三栏并排查看。
- 面板隐藏与重排：可隐藏 PDF、英文段落或中文译文面板，剩余面板会自动铺满空间。
- 双栏论文顺序优化：按常见论文阅读顺序先读左栏，再读右栏。
- 术语表：添加、保留英文、删除术语，翻译时可作为提示上下文。
- 批量翻译：支持整篇文档翻译，也支持选择区间重译。
- Word 导出：只导出中文译文，方便脱离原论文连续阅读。

## 技术栈

- 后端：FastAPI、SQLAlchemy、Alembic、PyMuPDF、python-docx
- 前端：Vue 3、Vite、TypeScript、pdf.js
- 数据库：MySQL 8
- Docker：Compose 编排 MySQL、后端和前端 Nginx

## Docker 一键启动

1. 准备环境变量：

       Copy-Item .env.docker.example .env

   编辑 .env，至少填写：

       API_KEY=你的模型服务密钥
       BASE_URL=https://api.openai.com/v1
       MODEL_NAME=gpt-4.1-mini

2. 构建并启动：

       docker compose up --build

3. 打开浏览器：

       http://127.0.0.1:5173

Docker Compose 会自动创建 MySQL 数据库，并在后端启动时执行 Alembic 迁移。上传的 PDF 文件会保存在 Docker volume backend-storage 中，数据库数据保存在 mysql-data 中。

## 本地开发启动

1. 创建 MySQL 数据库：

       Get-Content -Raw scripts/init-db.sql | mysql -uroot -p123456

2. 配置后端：

       cd backend
       Copy-Item .env.example .env

   填写 MYSQL_PASSWORD、API_KEY、BASE_URL 和 MODEL_NAME。

3. 执行数据库迁移：

       conda activate lang-chain01
       cd backend
       alembic upgrade head

4. 安装并构建前端：

       cd ../frontend
       npm.cmd install
       npm.cmd run build

5. 启动开发服务：

       cd ..
       ./scripts/dev.ps1

开发模式下：

- 前端：http://127.0.0.1:5173
- 后端：http://127.0.0.1:8002

## 常用命令

后端测试：

    cd backend
    conda run -n lang-chain01 pytest -q

前端测试：

    cd frontend
    npm.cmd test

前端生产构建：

    cd frontend
    npm.cmd run build

Docker 停止并保留数据：

    docker compose down

Docker 停止并清除数据：

    docker compose down -v

## 配置说明

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| API_KEY | 模型服务 API Key | 空 |
| BASE_URL | OpenAI 兼容接口地址 | https://api.openai.com/v1 |
| MODEL_NAME | 翻译模型名称 | gpt-4.1-mini |
| MYSQL_HOST | MySQL 主机 | localhost / Docker 中为 mysql |
| MYSQL_DATABASE | 数据库名 | easypdf |
| TRANSLATION_CONCURRENCY | 翻译并发数 | 2 |
| TRANSLATION_BATCH_SIZE | 每批翻译段落数 | 6 |
| STORAGE_DIR | 上传文件存储目录 | ../storage |

## 使用流程

1. 在首页上传英文论文 PDF。
2. 等待系统解析出英文段落。
3. 在术语表中维护固定译法。
4. 回到阅读器，点击“生成中文翻译”。
5. 根据需要隐藏某些面板，专注阅读原文或译文。
6. 翻译完成后点击“导出中文译文为 Word”。

## 注意事项

- EasyPDF 默认是本地部署应用，上传文件和数据库内容都保存在本机或 Docker volume 中。
- 翻译质量取决于你配置的模型服务。
- Word 导出只包含中文译文，不包含原始英文段落和 PDF 页面。
- 对于复杂版式、表格和公式密集的 PDF，段落提取可能仍需人工检查。
