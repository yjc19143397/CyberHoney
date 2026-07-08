# CyberHoney - 多服务蜜罐管理系统

一款功能强大的多服务蜜罐系统，用于网络安全监控和攻击检测。

## 功能特性

- **GUI界面**: 基于PyQt6的图形用户界面，支持实时监控和管理
- **深色/浅色主题**: 支持跟随系统、浅色模式、深色模式三种主题
- **管理员权限**: 支持以管理员身份运行和设置始终以管理员身份运行
- **多服务蜜罐**: SSH、FTP、HTTP、TCP、UDP、Telnet、API 七种服务
- **服务独立控制**: 每个服务可以单独启动和停止，互不影响
- **实时日志监控**: 实时显示系统日志，支持日志级别过滤和自动滚动
- **攻击记录**: 记录所有认证尝试和攻击行为，支持实时刷新
- **连接状态**: 显示当前活跃连接和历史连接记录
- **统计信息**: 攻击总数、活跃连接、封禁IP、连接总数统计
- **日志缓存**: 内存日志缓存，支持最大50000条记录
- **日志保存**: 支持将日志保存到本地文件
- **退出自动清理**: 退出时自动清除缓存和日志
- **自定义保存路径**: 支持修改缓存和日志保存路径
- **配置持久化**: 设置保存在 config.json，重启后保留

## 支持的服务

| 服务 | 端口 | 协议 | 说明 |
|------|------|------|------|
| SSH | 2222 | TCP | 模拟SSH服务，记录认证尝试 |
| FTP | 2121 | TCP | 模拟FTP服务，支持常见FTP命令 |
| HTTP | 8080 | TCP | 模拟Web服务器，记录所有请求 |
| TCP | 1234 | TCP | 通用TCP服务，记录数据传输 |
| UDP | 5678 | UDP | 通用UDP服务，记录数据包 |
| Telnet | 2323 | TCP | 模拟Telnet服务，支持命令交互 |
| API | 5000 | TCP | REST API接口，查询收集的数据 |

## 环境要求

- Python 3.14+
- 依赖包见 `requirements.txt`

## 安装方法

```bash
cd honeypot
pip install -r requirements.txt
pip install -e .
```

## 使用方法

### 命令行方式

安装完成后，可以在CMD/PowerShell中直接使用 `cyberhoney` 命令：

```bash
# 查看帮助
cyberhoney --help

# 启动GUI界面（推荐）
cyberhoney gui

# 启动蜜罐服务（无界面）
cyberhoney start

# 启动API服务
cyberhoney api

# 查看版本
cyberhoney version
```

### Python脚本方式

```bash
# 启动GUI界面
python main.py gui

# 启动蜜罐服务
python main.py start
```

## 配置文件

编辑 `config.yaml` 自定义蜜罐设置：

- 服务端口和启用状态
- 日志配置
- API设置
- 数据库路径

## API接口

- `GET /api/status` - 检查蜜罐状态
- `GET /api/connections` - 获取连接日志
- `GET /api/credentials` - 获取认证尝试记录
- `GET /api/http` - 获取HTTP请求记录

## 项目结构

```
honeypot/
├── honeypot/
│   ├── core/           # 核心组件（配置、日志、数据库、服务管理）
│   ├── services/       # 服务实现（SSH、FTP、HTTP、TCP、UDP、Telnet）
│   ├── api/            # REST API服务器
│   ├── cli/            # 命令行接口
│   ├── gui/            # 图形用户界面（主窗口、主题、权限）
│   ├── __init__.py
│   └── main.py
├── data/               # 数据库文件
├── logs/               # 日志文件
├── tests/              # 单元测试
├── config.yaml         # 配置文件
├── requirements.txt    # 依赖列表
├── setup.py            # 包安装配置
├── main.py             # 入口脚本
├── README.md           # 项目说明
└── CHANGELOG.md        # 更新日志
```

## 安全说明

- 所有认证尝试都会被记录但会被拒绝
- 不暴露真实服务
- 所有数据本地存储
- API访问受IP白名单限制

## 许可证

MIT License

## 更新日志

请查看 [CHANGELOG.md](CHANGELOG.md)