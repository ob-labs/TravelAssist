# OceanBase 多模型搜索演示项目

[English Version](./README.md)

## 快速开始 (Docker Compose)

1. 在 `docker` 目录下创建 `.env` 文件并配置 API 密钥：
```bash
cd docker
cp .env.example .env
vim .env # 设置你的 DASHSCOPE_API_KEY 和 AMAP_API_KEY。
```
2. 启动服务：
```bash
docker compose up -d
```
3. 打开 http://localhost:8501 并按照侧边栏指引上传并加载数据集。

## 其他安装方式

### 选项 1: 一键 Docker 安装

1. (可选但推荐) 安装 [uv](https://github.com/astral-sh/uv) 以实现快速 Python 包管理：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. 根据 `.env.example` 创建 `.env` 文件：

```bash
cp .env.example .env
```

3. 编辑 `.env` 文件以配置数据库和 API 密钥：

```bash
vim .env
```

关键配置：
- 设置 `REUSE_CURRENT_DB=false` 以自动启动 Docker 数据库
- 设置 `DB_STORE=seekdb` 或 `DB_STORE=oceanbase` 选择数据库类型
- 配置模型服务的 `DASHSCOPE_API_KEY`
- 配置地图服务的 `AMAP_API_KEY`

4. 运行初始化脚本以启动 Docker 数据库：

```bash
bash scripts/init_docker.sh
```

该脚本将：
- 自动下载并启动 SeekDB 或 OceanBase Docker 容器
- 等待数据库准备就绪
- 验证数据库连接

### 选项 2: 手动 Docker 安装

1. 使用 docker 部署单机版 OceanBase 服务器：

```bash
# 对于 SeekDB (轻量级)
docker run --name seekdb -e -d -p 2881:2881 -p 2886:2886 oceanbase/seekdb

# 或对于 OceanBase CE (全功能版)
docker run --name=oceanbase-ce -e OB_TENANT_PASSWORD=your-password -e datafile_size=10G -p 2881:2881 -d oceanbase/oceanbase-ce
```

你也可以使用 [免费的 OceanBase 云实例](https://www.oceanbase.com/free-trial)

2. 在本项目目录下创建 `.env` 文件并进行配置：

```bash
vim .env
```

```plain
# 数据库配置
REUSE_CURRENT_DB=true
DB_STORE=seekdb
DB_HOST="127.0.0.1"
DB_PORT="2881"
DB_USER="root"
DB_PASSWORD="your-password"
DB_NAME="test"
DB_SSL_CA_PATH=""
```

### 所有方式通用步骤

3. 获取 API 密钥并在 `.env` 中配置：
   - 访问 https://www.aliyun.com/product/bailian 获取模型服务的 `DASHSCOPE_API_KEY`
   - 访问 https://lbs.amap.com/ 获取地图服务的 `AMAP_API_KEY`

4. 获取数据集：
   - 访问 https://www.kaggle.com/datasets/audreyhengruizhang/china-city-attraction-details
   - 下载并将其存储在本项目目录下手动创建的 `citydata` 目录中

5. 安装 Python 依赖：

```bash
uv sync
```

6. 启动对话服务器：

```bash
streamlit run src/ui.py
```
