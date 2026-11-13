# 潮汐 Tide 版本化交付与部署

## 交付物和状态

- 应用：`ghcr.io/tsaitang404/tide:vX.Y.Z`，Vue 静态资源和 Django API 在同一镜像。
- 部署文件：`compose.production.yml`、`.env.production.example`、本说明。
- PostgreSQL 16 和 Redis 7 是独立服务，各有持久卷。它不是单文件二进制，也不再支持文档旧示例里的默认 SQLite。
- `vX.Y.Z` 是占位符，必须换成已成功发布的版本；不要把本文当成某一版本已发布的证明。
- 交付必须遵循：修改代码 → 验证 → 提交并推送 → CI 构建和烟测 → 下载成功发布的镜像 → 部署验证。仓库归档时先解决归档阻塞，不以本地构建绕过发布流程。

生产部署默认关闭 DEBUG、市场实时采集，使用 Gunicorn。应用只绑定宿主机回环地址，数据库和 Redis 不发布宿主机端口。没有配置交易所密钥，不运行真实交易。

## 首次部署

要求：Linux x86_64、Docker Engine 和支持 `--wait` 的 Docker Compose v2。暂未验证 ARM 镜像。不要直接复用开发 Compose 的旧数据库卷，先备份并单独设计迁移。

```sh
cp .env.production.example .env.production
chmod 600 .env.production
# 分别运行两次，将结果填入 DJANGO_SECRET_KEY 和 POSTGRES_PASSWORD
openssl rand -hex 32
```

编辑 `.env.production`：指定已发布的 `GENETICGRID_IMAGE`（优先使用 `@sha256:...` 固定摘要），填入两个不同的随机值。数据库密码使用十六进制，以免破坏连接 URL。保留密钥和数据库备份，不要提交到 Git。不要把镜像标签 `edge` 或 `latest` 用作可回滚的生产版本记录。

```sh
docker compose --env-file .env.production -f compose.production.yml config --quiet
docker compose --env-file .env.production -f compose.production.yml pull
docker compose --env-file .env.production -f compose.production.yml up -d --wait
docker compose --env-file .env.production -f compose.production.yml ps
curl --fail http://127.0.0.1:8000/
```

远程访问应走你控制的 HTTPS 反向代理和访问控制，先在 `ALLOWED_HOSTS` 加入实际域名。配置包不是公开交易服务的安全审计结果；不要未经审计直接公开账户/订单接口。

入口会先迁移数据库，然后启动 API。迁移过程中强制关闭实时采集；没有启动时向交易所请求数据的强制预热步骤。`REALTIME_INGESTION_AUTO_START=true` 仅在部署验证后按需启用，当前使用单 worker 避免重复后台采集。不要把“采集关闭”当成交易接口禁用开关。

## 数据持久化、备份和升级

Compose 项目名决定卷名。首次确定项目目录/项目名后保持不变，避免误接新空卷。

```sh
# 升级前导出 PostgreSQL；备份可能含账户敏感数据，应私密保存并加密。
docker compose --env-file .env.production -f compose.production.yml exec -T postgres \
  pg_dump -U geneticgrid -d geneticgrid -Fc > geneticgrid-before-upgrade.dump
```

更新前记录旧镜像摘要，保存 `.env.production`，检查备份可恢复。修改镜像版本，执行 `pull`、`up -d --wait`。启动自动迁移不等于数据库迁移可逆：镜像回退仅适用于数据库兼容的版本；不兼容时停止写入，按独立恢复方案恢复数据库备份，不直接覆盖生产库。

`docker compose ... down` 保留卷；**不要使用 `down -v` 清理生产环境**。Redis 可重建缓存，但这里也使用持久卷和 AOF。

## 构建和发布

```sh
docker build -t geneticgrid:local .
GENETICGRID_IMAGE=geneticgrid:local ./scripts/smoke-image.sh
```

烟测使用唯一 Compose 项目、随机测试密码、独立数据卷，检查迁移、健康、首页、Vue JS/CSS 和 API。结束只清理该测试项目的容器和卷，不需要交易所凭据，也不启用采集。

流水线在 PR 和手动触发时只验证；推送 `main` 发布 `edge`，推送版本 tag 发布对应版本。只有烟测成功才推送镜像。部署配置归档和 SHA-256 校验文件保存在对应 Actions run 的制品中；这不等于自动创建 GitHub Release。

发布前还应运行后端测试。仓库旧 `scripts/test_okx_auth.py` 是需凭据的交互诊断脚本，不应被普通 pytest 自动收集。不可通过跳过类型检查来发布镜像。

## 已知验证边界

本地验证记录见本次任务报告。云开发环境没有 Docker Engine 时，前端构建和 Python 检查成功也不能替代完整镜像构建、Compose 迁移和启动烟测。正式发布以前必须在 CI 或有 Docker 的隔离环境完成后者。
