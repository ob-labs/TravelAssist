# OceanBase Multi-Model Search Demo

[中文版](./README_zh.md)

![ui](docs/images/ui.jpg)

## Concept Introduction

Multi-Model Fusion: Multi-model fusion is an important direction of OceanBase's integrated product philosophy. In this context, multi-model fusion mainly refers to multi-model data hybrid retrieval technology. OceanBase supports hybrid queries of vector data, spatial data, document data, scalar data, and other types. Based on the support of multiple indexes such as vector index, spatial index, and full-text index, it provides higher-performance hybrid retrieval capabilities.

![arch.jpg](docs/images/arch.jpg)

## Obtain LLM API Key

```
Note: Activating Alibaba Cloud Bailian Large Model Service requires you to jump to a third-party platform. This operation will follow the charging rules of the third-party platform and may incur corresponding fees. Before continuing, please visit its official website or consult relevant documentation to confirm and accept its charging standards. If you disagree, please do not continue.
```

Register an [Alibaba Cloud Bailian account](https://bailian.console.aliyun.com/), activate the model service, and obtain an API key.

![activate-models](docs/images/activate-models.png)
![confirm-to-activate-models](docs/images/confirm-to-activate-models.png)
![bailian1](docs/images/bailian1.jpg)
![bailian2](docs/images/bailian2.png)

## Obtain Geographic Service API Key

```
Note: Activating Amap Geographic Service requires you to jump to a third-party platform. This operation will follow the charging rules of the third-party platform and may incur corresponding fees. Before continuing, please visit its official website or consult relevant documentation to confirm and accept its charging standards. If you disagree, please do not continue.
```

Register on Amap Open Platform and obtain a [Basic LBS Service](https://lbs.amap.com/upgrade#price) API key.

![gaode1](docs/images/gaode1.jpg)
![gaode2](docs/images/gaode2.jpg)
![gaode3](docs/images/gaode3.jpg)
![gaode4](docs/images/gaode4.jpg)
![gaode5](docs/images/gaode5.jpg)
![gaode6](docs/images/gaode6.png)

## Download Public Dataset

Download the [China City Attraction Details Dataset from Kaggle](https://www.kaggle.com/datasets/audreyhengruizhang/china-city-attraction-details) ZIP archive.

## Create Cloud Experience Cluster (Optional)

Apply for a [free OceanBase cloud instance](https://www.oceanbase.com/free-trial) to get an experience cluster.

![obcloud1](docs/images/obcloud1.jpg)

## Build Your Travel Assistant

### Configure .env File

```bash
cd docker
cp .env.example .env
vim .env # Set your DASHSCOPE_API_KEY and AMAP_API_KEY.
```

Key configurations (for more details, read the .env file directly, each configuration item has comment explanations):
- Set `REUSE_CURRENT_DB=false` to automatically start a Docker database. If you have already set up an OceanBase cluster, you can set this to true
- Set `DB_STORE=seekdb` or `DB_STORE=oceanbase` to choose database type
- Configure `DASHSCOPE_API_KEY` for model service - Alibaba Cloud Bailian platform LLM API key
- Configure `AMAP_API_KEY` for map service - Amap Open Platform API key

### Quick Start (Docker Compose Method, Recommended)

```bash
cd docker
docker compose up -d
```

### Manual Start

```bash
make init
make start
```

### Load China City Attraction Details Dataset

Open http://localhost:8501, upload and load the China City Attraction Details dataset downloaded earlier.

![upload](docs/images/upload.jpg)
![load](docs/images/load.jpg)

## Quick Start (Docker Compose)

1. Create `.env` file in `docker` directory and configure API keys:

```bash
cd docker
cp .env.example .env
vim .env # Set your DASHSCOPE_API_KEY and AMAP_API_KEY.
```

2. Start services:

```bash
docker compose up -d
```

3. Open http://localhost:8501 and follow the sidebar instructions to upload and load the dataset.

## Alternative Installation Methods

### Option 1: One-Click Docker Installation

1. (Optional but Recommended) Install [uv](https://github.com/astral-sh/uv) for fast Python package management:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

3. Edit `.env` file to configure database and API keys:

```bash
vim .env
```

Key configurations:
- Set `REUSE_CURRENT_DB=false` to automatically start a Docker database
- Set `DB_STORE=seekdb` or `DB_STORE=oceanbase` to choose database type
- Set `DB_PASSWORD` as your database password
- Configure `DASHSCOPE_API_KEY` for model service
- Configure `AMAP_API_KEY` for map service

4. Run the initialization script to start Docker database:

```bash
bash scripts/init_docker.sh
```

This script will:
- Automatically download and start SeekDB or OceanBase Docker container
- Wait for database to be ready
- Verify database connection

### Option 2: Manual Docker Installation

1. Deploy a standalone OceanBase server with docker:

```bash
# For SeekDB (lightweight)
docker run --name seekdb -e -d -p 2881:2881 -p 2886:2886 oceanbase/seekdb

# Or for OceanBase CE (full features)
docker run --name=oceanbase-ce -e OB_TENANT_PASSWORD=your-password -e datafile_size=10G -p 2881:2881 -d oceanbase/oceanbase-ce
```

You can also use a [free OceanBase cloud instance](https://www.oceanbase.com/free-trial)

2. Create `.env` file in this project directory and set configurations:

```bash
vim .env
```

```plain
# Database configuration
REUSE_CURRENT_DB=true
DB_STORE=seekdb
DB_HOST="127.0.0.1"
DB_PORT="2881"
DB_USER="root"
DB_PASSWORD="your-password"
DB_NAME="test"
DB_SSL_CA_PATH=""
```

### Common Steps for All Methods

3. Obtain API keys and configure in `.env`:
   - Visit https://www.aliyun.com/product/bailian to get `DASHSCOPE_API_KEY` for model service
   - Visit https://lbs.amap.com/ to get `AMAP_API_KEY` for map service

4. Obtain the dataset:
   - Visit https://www.kaggle.com/datasets/audreyhengruizhang/china-city-attraction-details
   - Download and store it in a manually created `citydata` directory under this project directory

5. Install Python dependencies:

```bash
uv sync
```

6. Start the chat server:

```bash
streamlit run src/ui.py
```
