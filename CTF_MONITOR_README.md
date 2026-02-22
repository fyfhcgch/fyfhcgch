# 🎯 CTF 监控哨兵

自动抓取 CTF 竞赛信息并生成 GitHub Issue 提醒的监控系统。

## 📋 功能特性

- **自动抓取**: 从 CTFtime 等平台抓取即将开始的 CTF 竞赛
- **智能去重**: 自动检测已存在的赛事，避免重复创建 Issue
- **定时任务**: 每天自动运行，及时获取最新赛事信息
- **自定义配置**: 支持配置监控范围、过滤条件等

## 🚀 快速开始

### 1. 系统已自动配置

监控哨兵已经集成到本仓库，无需额外配置即可使用。

### 2. 手动触发

访问 [Actions 页面](https://github.com/fyfhcgch/fyfhcgch/actions/workflows/ctf-monitor.yml)，点击 "Run workflow" 手动运行。

### 3. 查看结果

监控运行后，新的 CTF 竞赛会自动创建为 GitHub Issue，带有 `CTF` 和 `竞赛提醒` 标签。

## ⚙️ 配置说明

编辑 `.github/scripts/monitor_config.json` 文件：

```json
{
  "sources": {
    "ctftime": {
      "enabled": true,          // 是否启用 CTFtime
      "days_ahead": 30          // 监控未来多少天的赛事
    }
  },
  "filters": {
    "min_duration_hours": 1,    // 最短赛事时长
    "max_duration_hours": 168   // 最长赛事时长
  },
  "issue_template": {
    "labels": ["CTF", "竞赛提醒"],
    "assignees": []             // 自动分配给指定用户
  }
}
```

## 📁 文件结构

```
.github/
├── scripts/
│   ├── ctf_monitor.py          # 监控主程序
│   ├── monitor_config.json     # 配置文件
│   └── tracked_events.json     # 已追踪赛事记录
└── workflows/
    └── ctf-monitor.yml         # GitHub Actions 工作流
```

## 🔧 扩展开发

### 添加新的数据源

在 `ctf_monitor.py` 中添加新的抓取方法：

```python
def fetch_custom_events(self) -> List[Dict]:
    """从自定义源获取赛事"""
    events = []
    # 实现抓取逻辑
    return events
```

然后在 `run()` 方法中调用：

```python
custom_events = self.fetch_custom_events()
all_events.extend(custom_events)
```

## 📝 Issue 模板

自动生成的 Issue 包含以下信息：

- 竞赛名称和时间
- 持续时间和形式
- 相关链接（官网、CTFtime）
- 竞赛描述

## ⏰ 定时任务

默认每天早上 9 点（北京时间）自动运行，可通过修改 `.github/workflows/ctf-monitor.yml` 中的 `cron` 表达式调整：

```yaml
schedule:
  - cron: "0 1 * * *"  # UTC 时间 1:00 = 北京时间 9:00
```

## 🔒 权限说明

监控脚本使用 `GITHUB_TOKEN` 自动创建 Issue，无需额外配置权限。

## 🐛 故障排查

### 工作流运行失败

1. 检查 Actions 日志查看具体错误
2. 确认 `GITHUB_TOKEN` 权限正常
3. 检查网络连接（CTFtime API 访问）

### 没有生成 Issue

1. 可能是当前没有符合条件的赛事
2. 检查 `days_ahead` 配置是否过短
3. 检查过滤条件是否过于严格

## 📄 许可证

MIT License
