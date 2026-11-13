# 潮汐 Tide - 加密货币交易平台

原项目名 GeneticGrid，现名潮汐 Tide。仓库使用 `tsaitang404/Tide`，新发布镜像使用 `ghcr.io/tsaitang404/tide`；Python 包名、Compose 项目名与数据库标识保留，以兼容现有部署。

基于 **Vue 3 + TypeScript + Django** 的现代化加密货币K线图分析平台。

## ✨ 特性

- 🚀 **Vue 3 + TypeScript**: 完整的类型安全前端应用
- 📊 **22 种技术指标**: MA, EMA, BOLL, MACD, RSI, KDJ 等
- 🎨 **画线工具**: 直线、射线、斐波那契回调、等距通道
- 🔄 **多数据源**: OKX, Binance, Coinbase, CoinGecko, TradingView
- 💱 **15 种货币**: 支持多货币单位和实时汇率转换
- ⚡ **Web Worker**: 异步计算指标，不阻塞UI
- 🎯 **无限滚动**: 自动加载历史和实时数据
- 🌍 **全球交易所覆盖**: 支持北美(Coinbase)、亚洲(OKX/币安)等主要市场

## 📦 技术栈

**前端**: Vue 3 + TypeScript + Vite + Lightweight Charts  
**后端**: Django 4.2 + Python 3.11+

## �️ 环境准备（pyenv + nvm）

使用 [pyenv](https://github.com/pyenv/pyenv) 与 [nvm](https://github.com/nvm-sh/nvm) 可以为 Python 和 Node.js 创建可重复的开发环境。


### 🧰 一键初始化本地环境

项目提供初始化脚本，可自动完成以下操作：
- 根据 `.python-version` 安装并启用 Python（优先 pyenv）
- 创建 `.venv` 并安装后端依赖
- 根据 `.nvmrc` 安装并启用 Node（通过 nvm）
- 在 `frontend/` 执行 `npm ci`
- 从 `.env.example` 生成 `.env`（若不存在）
- 执行 `python manage.py migrate` 与 `python manage.py check`

```bash
./scripts/init.sh
```

初始化完成后可直接启动开发环境：

```bash
./scripts/dev.sh
```

### ⚙️ 一键启动前后端

如果想在同一个终端里同时启动 Django 与 Vite，可使用项目自带脚本：

```bash
./scripts/dev.sh
```

脚本会自动创建缺失的 `.venv`、安装 `requirements.txt`，然后依据 `.python-version` 使用 `pyenv` 激活对应解释器；接着读取 `.nvmrc`（若缺失则回退到 20.17.0）并通过 `nvm use` 启动对应的 Node 版本，最后分别运行 `python manage.py runserver` 与 `npm run dev -- --host 0.0.0.0`。可通过环境变量来自定义监听地址：

```bash
DJANGO_ADDR=0.0.0.0:8000 VITE_HOST=127.0.0.1 ./scripts/dev.sh
```

> 提示：脚本会在启动前执行 `pyenv init -` 并读取 `.python-version` / `.nvmrc`，确保 Python 与 Node 均使用项目锁定的版本，并会等待 Django 端口就绪后再启动前端，避免初次请求命中未就绪的 API。

按 `Ctrl+C` 将同时停止前后端进程。
### Python（pyenv）

```bash
# 安装项目所需的 Python 版本
pyenv install 3.11.9

# 将当前目录固定为该版本
pyenv local 3.11.9

# 可选：使用 pyenv-virtualenv 管理独立的虚拟环境
pyenv virtualenv 3.11.9 geneticgrid
pyenv activate geneticgrid

# 安装后端依赖
pip install -r requirements.txt
```

> 如果你更倾向于使用系统 Python，也可以通过 `python -m venv .venv && source .venv/bin/activate` 来创建虚拟环境，确保最终使用的是 3.11.x 版本。

### Node.js（nvm）

```bash
# 安装并启用项目指定的 Node.js 版本
nvm install 20.17.0
nvm use

# 安装前端依赖
cd frontend
npm install
```

## �🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt
cd frontend && npm install

# 2. 开发模式
# 终端1: Django API
python manage.py runserver

# 终端2: Vite 开发服务器  
cd frontend && npm run dev
# 访问: http://localhost:3000

# 3. 生产部署
# 见 docs/DEPLOYMENT.md；不要用 Django runserver 对外提供生产服务。
```

## ✅ 单元测试

安装依赖后，先配置 PostgreSQL 测试数据库连接并导出 `DATABASE_URL`、
`DJANGO_DEBUG=true`、`REALTIME_INGESTION_AUTO_START=false`。无数据库的配置/路由检查可运行
`pytest tests/test_production_settings.py tests/test_entrypoints.py tests/test_urls.py`。
全套测试还包含数据库和联网诊断脚本，目前不能当作全部隔离的单元测试。

原有完整测试命令：

```bash
pytest
```

如果使用项目虚拟环境，推荐：

```bash
./.venv/bin/python -m pytest
```

覆盖率报告示例：

```bash
./.venv/bin/python -m pytest --cov=core --cov=geneticgrid --cov-report=term-missing
```

## 📁 项目结构

```
frontend/src/
  ├── components/  # Vue 组件
  ├── composables/ # 可复用逻辑
  └── types/       # TypeScript 类型
core/              # Django 应用
static/dist/       # Vue 构建输出
```

## 🐳 Docker 打包与运行

最终交付是 **版本化 Docker 镜像 + Compose 配置 + 部署说明**，不是独立二进制。
Vue 前端和 Django 后端在一个镜像中，PostgreSQL 与 Redis 独立持久化。

请按 [部署说明](docs/DEPLOYMENT.md) 配置 `.env.production`，再通过
`compose.production.yml` 拉取已发布版本。默认不启用市场采集，不需要交易所密钥。
旧版“无需配置、默认 SQLite 单容器”的说明已失效。

本地源码构建仍可用 `docker build -t geneticgrid:local .`。
版本发布前必须通过 `GENETICGRID_IMAGE=geneticgrid:local ./scripts/smoke-image.sh`。
仓库中的 `compose.yml` 保留作开发用途，生产部署使用新的独立配置。

## 🎯 功能

- **22个技术指标**: MA, EMA, BOLL, SAR, MACD, RSI, KDJ, CCI, WR, OBV 等
- **画线工具**: 直线, 射线, 横线, 斐波那契, 等距通道
- **30+时间周期**: 支持自定义周期（如 2h, 7d）
- **15种货币**: USDT, USD, CNY, EUR, JPY 等

## 📄 许可证

MIT
