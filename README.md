# RPA Agent Final

整合 `RPA Agent + NanoBot + 本地 LLM + Dash UI（OpenClaw 风格）` 的纯离线单机版模板。

纯离线・单机版 | 300+ Python RPA 统一管理 | AI 智能任务编排 | 可视化专业 UI | Python 入门可完全掌握

本版本面向：

- ✅ 已自研 300+ Python RPA 的用户
- ✅ Python 基础入门用户
- ✅ 需本地 / 离线 / 内网部署的场景
- ✅ 需 AI 智能调度 RPA 的需求
- ✅ 需专业可视化管理界面的交付场景

## 一、快速开始

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 启动 Dash UI

```bash
python ui_start.py
```

3. 启动 NanoBot + RPA 服务

```bash
python start.py
```

## 二、项目整体定位

### 1) 解决核心痛点

- 300+ 自研 Python RPA 无统一管理、无标准化调用
- RPA 无法被本地小模型 AI 智能编排、自动执行
- 无可视化 UI，配置 / 运行 / 日志全靠改代码
- 无法在单机 / 离线 / 内网环境稳定运行
- Python 入门用户无法快速驾驭复杂系统

### 2) 核心能力

- ✅ 300+ RPA 统一注册、标准化管理（零修改旧 RPA）
- ✅ 双模式运行：技能包模式（同进程极速）+ 本地 API 模式（解耦稳定）
- ✅ NanoBot 智能 Agent + 本地离线 LLM（Ollama / LM Studio）
- ✅ AI 任务编排：自动串联多步骤 RPA 流程
- ✅ Dash 专业 UI（仿 OpenClaw 深色控制台）
- ✅ 统一日志、异常捕获、失败重试
- ✅ 纯 Python，入门可维护、可交付、可上线

### 3) 适用环境

- 运行环境：Windows / Linux / 树莓派
- 网络：纯离线 / 内网 / 无外网
- 模型：本地轻量 LLM（Qwen / Llama3.2）
- 部署：单机一键启动

## 三、核心技术架构（分层图解）

```plaintext
┌─────────────────────────────────────────────────────┐
│ 【展示层】Dash UI（仿 OpenClaw 风格）               │
│  → 系统配置 | RPA 列表 | 流程编排 | LLM 配置 | 日志 │
├─────────────────────────────────────────────────────┤
│ 【智能层】NanoBot Agent + 本地离线 LLM              │
│  → 意图理解 | 任务决策 | RPA 编排 | 流程生成        │
├─────────────────────────────────────────────────────┤
│ 【调度层】统一执行引擎 | 双模式适配器                │
│  → 技能包模式（直接调用）| API 模式（本地 HTTP）     │
├─────────────────────────────────────────────────────┤
│ 【执行层】300+ Python RPA 注册中心                   │
│  → 桌面/网页/Excel/系统/业务全品类 RPA              │
└─────────────────────────────────────────────────────┘
```

## 四、项目文件树（生产版核心）

```plaintext
rpa_agent_final/
├── requirements.txt           # 全项目依赖（一键安装）
├── config.yaml                # 全局配置（唯一配置文件）
├── start.py                   # 一键启动：NanoBot + RPA 服务
├── ui_start.py                # 一键启动：Dash UI 控制台
├── nanobot_tool.py            # NanoBot 调用 RPA 统一入口
├── core/
│   ├── registry.py            # ✅ 核心：RPA 注册中心（主要维护点）
│   ├── executor.py            # 执行引擎（重试 + 超时 + 日志）
│   └── schema.py              # 数据结构定义
├── adapter/
│   ├── skill.py               # 技能包模式（同进程）
│   └── api.py                 # API 模式（127.0.0.1:8976）
├── workflow/
│   └── engine.py              # AI 多步骤流程执行
├── dash_ui/
│   ├── app.py                 # UI 主程序
│   ├── layout.py              # UI 布局（侧边栏 + 内容区）
│   └── pages/                 # 配置 / RPA 列表 / 流程 / LLM / 日志 / 注册中心
├── logs/                      # 运行日志与注册中心备份
├── tests/                     # 项目测试
└── nanobot/                   # NanoBot 子项目
```

## 五、运行与配置说明

- 配置入口：`config.yaml`
- 运行模式：`system.mode` 支持 `skill` 与 `api`
- API 服务：`api.host` + `api.port`（默认 `127.0.0.1:8976`）
- 日志文件：`rpa.log_file`（默认 `logs/rpa.log`）

> 当前仓库默认配置为 `api` 模式；若用于离线生产单机，建议改为 `skill` 模式。

## 六、Registry 编辑器（MVP）

- 入口：Dash UI 左侧菜单 `注册中心`
- 功能：可在前端直接编辑 `core/registry.py`
- 保存流程：语法/结构检查 → 自动备份到 `logs/registry_backups/` → 原子写入
- 生效方式：保存后重启 `ui_start.py` 与 `start.py`
- 限制：建议仅在 localhost 单机环境使用

## 九、生产环境优化（离线部署）

- 模式选择：正式环境用 `skill` 模式（更稳定）
- 模型选择：`qwen2:1.5b` / `llama3.2:1b`（轻量离线）
- 日志管理：`logs/` 目录自动生成，建议按日期归档
- 离线运行：无外网、无云、无中间件
- 打包交付：可打包为 EXE 桌面软件（如 PyInstaller）

## 十、项目核心优势（可直接写交付文档）

### 1) 架构优势

- 纯 Python 技术栈，入门可维护
- 分层解耦，稳定可靠
- 双模式兼容，适配所有场景

### 2) 功能优势

- 300+ RPA 统一标准化管理
- 本地 AI 智能编排
- 专业可视化 UI
- 离线单机部署
- 生产级日志、重试、异常

### 3) 交付优势

- 一键启动、开箱即用
- 零修改旧 RPA
- 纯离线、安全合规
- 可直接交付客户 / 上线

## 十一、入门用户学习路线（3 天掌握）

- Day 1：跑通项目
  - 安装依赖 → 启动 UI → 启动 Agent → 运行示例 RPA
- Day 2：接入 RPA
  - 在 `core/registry.py` 注册自己的 10 个 RPA → 在 UI 运行测试
- Day 3：AI 编排
  - 对接本地 LLM → 让 AI 自动执行多步骤 RPA 流程
