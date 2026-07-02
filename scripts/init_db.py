#!/usr/bin/env python
"""
数据库初始化脚本

创建所有表并插入基础数据。
运行方式：python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

# 将项目根目录加入 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.database import init_db, close_db


async def main():
    print("=== FinGuard 数据库初始化 ===")
    print("正在创建数据库表...")
    await init_db()
    print("✅ 数据库表创建完成")
    await close_db()
    print("✅ 数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
