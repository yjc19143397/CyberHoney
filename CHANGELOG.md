# Changelog
## [v1.0.1] - 2026-07-08

### Changed

- 添加同步脚本，支持自动更新CHANGELOG和推送GitHub


All notable changes to this project will be documented in this file.

## [v1.0.0] - 2026-07-08

### Added

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
- **命令行集成**: 支持 cyberhoney 命令在CMD中直接使用

### Changed

- 项目入口从 `main.py` 改为 `cyberhoney` 命令
- 服务管理使用线程安全的独立控制机制
- 优化启动速度，采用懒加载机制

### Fixed

- 修复相对导入错误（attempted relative import with no known parent package）
- 修复服务无法独立启停的问题
- 修复日志显示和过滤问题

## [v0.1.0] - Initial Release

- 基础SSH、FTP、HTTP蜜罐服务
- CLI命令行接口
- SQLite数据库存储
- 基础日志系统