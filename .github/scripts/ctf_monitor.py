#!/usr/bin/env python3
"""
CTF 竞赛监控哨兵
自动抓取 CTF 竞赛信息并生成 GitHub Issue
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests

# 配置文件路径
CONFIG_FILE = Path(".github/scripts/monitor_config.json")
DATA_FILE = Path(".github/scripts/tracked_events.json")

# GitHub API 配置
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "")


class CTFMonitor:
    """CTF 竞赛监控器"""
    
    def __init__(self):
        self.config = self.load_config()
        self.tracked_events = self.load_tracked_events()
        self.headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def load_config(self) -> Dict:
        """加载监控配置"""
        default_config = {
            "sources": {
                "ctftime": {
                    "enabled": True,
                    "url": "https://ctftime.org/api/v1/events/",
                    "days_ahead": 30
                },
                "custom_feeds": []
            },
            "filters": {
                "min_duration_hours": 1,
                "max_duration_hours": 168,
                "keywords": ["CTF", "网络安全", "信息安全", "渗透测试"]
            },
            "issue_template": {
                "labels": ["CTF", "竞赛提醒"],
                "assignees": []
            }
        }
        
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return {**default_config, **json.load(f)}
        return default_config
    
    def load_tracked_events(self) -> Dict:
        """加载已追踪的赛事"""
        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"events": [], "last_check": None}
    
    def save_tracked_events(self):
        """保存已追踪的赛事"""
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tracked_events, f, ensure_ascii=False, indent=2)
    
    def fetch_ctftime_events(self) -> List[Dict]:
        """从 CTFtime 获取赛事信息"""
        if not self.config["sources"]["ctftime"]["enabled"]:
            return []
        
        try:
            # 计算时间范围
            now = datetime.now()
            days_ahead = self.config["sources"]["ctftime"]["days_ahead"]
            end_date = now + timedelta(days=days_ahead)
            
            # CTFtime API 限制，需要添加 User-Agent
            headers = {
                "User-Agent": "CTF-Monitor-Bot/1.0"
            }
            
            url = f"{self.config['sources']['ctftime']['url']}"
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            events = response.json()
            filtered_events = []
            
            for event in events:
                # 解析时间
                start_time = datetime.fromisoformat(event["start"].replace("Z", "+00:00"))
                end_time = datetime.fromisoformat(event["finish"].replace("Z", "+00:00"))
                
                # 只保留未来赛事
                if start_time > now and start_time <= end_date:
                    duration_hours = (end_time - start_time).total_seconds() / 3600
                    
                    # 检查时长过滤
                    min_dur = self.config["filters"]["min_duration_hours"]
                    max_dur = self.config["filters"]["max_duration_hours"]
                    
                    if min_dur <= duration_hours <= max_dur:
                        filtered_events.append({
                            "id": f"ctftime_{event['id']}",
                            "title": event["title"],
                            "description": event.get("description", ""),
                            "start_time": event["start"],
                            "end_time": event["finish"],
                            "duration_hours": duration_hours,
                            "url": event.get("url", ""),
                            "ctf_url": event.get("ctftime_url", ""),
                            "format": event.get("format", ""),
                            "location": event.get("location", ""),
                            "weight": event.get("weight", 0),
                            "source": "CTFtime"
                        })
            
            print(f"从 CTFtime 获取到 {len(filtered_events)} 个赛事")
            return filtered_events
            
        except Exception as e:
            print(f"获取 CTFtime 数据失败: {e}")
            return []
    
    def check_existing_issue(self, event_id: str) -> Optional[int]:
        """检查是否已存在相关 Issue"""
        try:
            search_query = f"repo:{GITHUB_REPO} is:issue in:title {event_id}"
            response = requests.get(
                "https://api.github.com/search/issues",
                headers=self.headers,
                params={"q": search_query},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result["total_count"] > 0:
                return result["items"][0]["number"]
            return None
            
        except Exception as e:
            print(f"检查 Issue 失败: {e}")
            return None
    
    def create_issue(self, event: Dict) -> bool:
        """创建 GitHub Issue"""
        try:
            # 格式化时间
            start_time = datetime.fromisoformat(event["start_time"].replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(event["end_time"].replace("Z", "+00:00"))
            
            # 构建 Issue 标题和正文
            title = f"🏆 CTF 竞赛提醒: {event['title']}"
            
            body = f"""## 🎯 竞赛信息

| 项目 | 详情 |
|------|------|
| **竞赛名称** | {event['title']} |
| **开始时间** | {start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC |
| **结束时间** | {end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC |
| **持续时间** | {event['duration_hours']:.1f} 小时 |
| **竞赛形式** | {event.get('format', '未知')} |
| **竞赛地点** | {event.get('location', '线上')} |
| **数据来源** | {event['source']} |
| **权重** | {event.get('weight', 'N/A')} |

## 🔗 相关链接

- [CTFtime 页面]({event.get('ctf_url', '')})
- [竞赛官网]({event.get('url', '')})

## 📝 描述

{event.get('description', '暂无描述')}

---

*此 Issue 由 CTF 监控哨兵自动生成*
*赛事 ID: {event['id']}*
"""
            
            # 创建 Issue
            issue_data = {
                "title": title,
                "body": body,
                "labels": self.config["issue_template"]["labels"]
            }
            
            if self.config["issue_template"]["assignees"]:
                issue_data["assignees"] = self.config["issue_template"]["assignees"]
            
            response = requests.post(
                f"https://api.github.com/repos/{GITHUB_REPO}/issues",
                headers=self.headers,
                json=issue_data,
                timeout=30
            )
            response.raise_for_status()
            
            issue_number = response.json()["number"]
            print(f"✅ 创建 Issue #{issue_number}: {event['title']}")
            return True
            
        except Exception as e:
            print(f"❌ 创建 Issue 失败: {e}")
            return False
    
    def run(self):
        """运行监控"""
        print("🚀 启动 CTF 监控哨兵...")
        print(f"📅 当前时间: {datetime.now().isoformat()}")
        print(f"📁 仓库: {GITHUB_REPO}")
        print()
        
        # 获取所有赛事
        all_events = []
        
        # 从 CTFtime 获取
        ctftime_events = self.fetch_ctftime_events()
        all_events.extend(ctftime_events)
        
        print(f"\n📊 共获取到 {len(all_events)} 个赛事")
        
        # 检查并创建 Issue
        new_count = 0
        existing_count = 0
        
        for event in all_events:
            # 检查是否已存在
            existing_issue = self.check_existing_issue(event["id"])
            
            if existing_issue:
                print(f"⏭️  已存在 Issue #{existing_issue}: {event['title']}")
                existing_count += 1
            else:
                # 创建新 Issue
                if self.create_issue(event):
                    new_count += 1
        
        # 保存追踪记录
        self.tracked_events["events"] = all_events
        self.tracked_events["last_check"] = datetime.now().isoformat()
        self.save_tracked_events()
        
        print(f"\n✨ 监控完成!")
        print(f"   新赛事: {new_count}")
        print(f"   已存在: {existing_count}")
        print(f"   总计: {len(all_events)}")


if __name__ == "__main__":
    if not GITHUB_TOKEN:
        print("❌ 错误: 未设置 GITHUB_TOKEN 环境变量")
        sys.exit(1)
    
    if not GITHUB_REPO:
        print("❌ 错误: 无法获取 GITHUB_REPOSITORY")
        sys.exit(1)
    
    monitor = CTFMonitor()
    monitor.run()
