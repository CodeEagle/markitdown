# MarkItDown MCP 懒猫微服

[MarkItDown](https://github.com/microsoft/markitdown) 是 Microsoft 维护的文件与 URL 转 Markdown 工具。本仓库将其 `markitdown-mcp` HTTP 服务移植到懒猫微服，提供可直接接入 MCP 客户端的 Streamable HTTP 与 SSE 入口。

## 上游项目

- 上游仓库: https://github.com/microsoft/markitdown
- 上游主页: https://github.com/microsoft/markitdown
- 上游许可证: MIT
- 当前适配版本:
  - `source_version`: `v0.1.5`
  - `build_version`: `0.1.5`

## 应用说明

迁移后的应用默认运行 `markitdown-mcp --http --host 0.0.0.0 --port 3001`，并提供以下入口：

- 首页: `https://<你的应用域名>/`
- MCP Streamable HTTP: `https://<你的应用域名>/mcp`
- MCP SSE: `https://<你的应用域名>/sse`
- SSE 消息通道: `https://<你的应用域名>/messages/`

首页为静态说明页；真正的 MCP 服务入口是 `/mcp` 与 `/sse`。
由于上游服务未提供独立的 `/health` HTTP 探针，本迁移版默认通过入口访问与运行日志做验收，不额外伪造健康检查端点。

## 功能特性

- 将 `http:`、`https:`、`file:`、`data:` URI 转换为 Markdown
- 内置 `markitdown[all]` 依赖，覆盖 PDF、Office、图片、音频等常见格式
- 支持 Streamable HTTP 与 SSE 两种 MCP 传输方式
- 提供持久化工作目录，便于通过 `file:///workdir/...` 访问本地文件

## 环境变量

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `MARKITDOWN_ENABLE_PLUGINS` | `true` | 启用 MarkItDown 插件加载 |

## 数据目录

应用将懒猫持久化目录映射为容器内工作目录：

| 懒猫目录 | 容器内路径 | 用途 |
| --- | --- | --- |
| `/lzcapp/var/data` | `/workdir` | 存放待转换文件，供 `file:///workdir/...` URI 访问 |

示例：如果你把文件写入 `/lzcapp/var/data/report.pdf`，则 MCP 调用时可传入 `file:///workdir/report.pdf`。

## 使用方式

### 1. 浏览器查看首页

访问应用根路径 `/` 可以看到服务说明和端点列表。

### 2. 使用 MCP Inspector 调试

将 Inspector 连接到：

- Streamable HTTP: `https://<你的应用域名>/mcp`
- SSE: `https://<你的应用域名>/sse`

### 3. 转换远程文件

通过 MCP 工具 `convert_to_markdown(uri)` 传入：

- `https://example.com/file.pdf`
- `file:///workdir/example.docx`
- `data:application/pdf;base64,...`

## 自动构建

仓库包含兼容 `lzcat-trigger` 的 `.github/workflows/update-image.yml`。目标 workflow 只负责：

1. 获取上游 `source_version`
2. 构建 `markitdown-mcp` 镜像
3. 推送 `ghcr.io/<owner>/markitdown:<source_version>`

后续镜像复制到 `registry.lazycat.cloud`、manifest 回写、`.lpk` 构建与发布，默认由 `lzcat-trigger` 统一处理。

## 相关链接

- 上游 README: https://github.com/microsoft/markitdown#readme
- `markitdown-mcp` 文档: https://github.com/microsoft/markitdown/tree/main/packages/markitdown-mcp
- LazyCat 开发文档: https://developer.lazycat.cloud/
