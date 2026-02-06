# OceanBase Multi-Model Search Demo

[中文版](./README_zh.md)

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
3. Open http://localhost:8501 and follow the sidebar to upload and load the dataset.

## Alternative Setup Methods

## Setup

### Option 1: One-Click Docker Setup (Recommended)

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

### Option 2: Manual Docker Setup

1. Deploy a standalone OceanBase server with docker:

```bash
# For SeekDB (lightweight)
docker run --name seekdb -e ROOT_PASSWORD=your-password -d -p 2881:2881 -p 2886:2886 oceanbase/seekdb

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

### Common Steps for Both Options

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

6. Import data into database:

```bash
python -m src.data.data_loader
```

7. Start the chat server:

```bash
streamlit run src/frontend/ui.py
```
