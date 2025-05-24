#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
生产环境运行脚本，使用 Waitress 作为 WSGI 服务器
"""

import os
import logging
from waitress import serve
from app import app, start_background_tasks

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("waitress.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("waitress")

if __name__ == "__main__":
    # 启动后台任务（数据刷新）
    start_background_tasks()
    
    # 获取端口（优先使用环境变量）
    port = int(os.environ.get("PORT", 5000))
    
    # 启动服务器
    logger.info(f"Starting Waitress server on port {port}...")
    serve(app, host='0.0.0.0', port=port, threads=4) 