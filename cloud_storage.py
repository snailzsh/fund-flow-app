"""
用于云环境的数据持久化模块
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

def is_cloud_env():
    """检测是否在云环境（如Render）中运行"""
    return os.environ.get('RENDER') == 'true'

def get_cache_dir():
    """获取缓存目录，在Render上使用指定的持久化路径"""
    if is_cloud_env():
        # Render提供的持久化目录
        cache_dir = os.environ.get('RENDER_CACHE_DIR', '/tmp')
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir
    else:
        # 本地环境直接使用当前目录
        return os.getcwd()

def save_cache_to_cloud(data):
    """保存缓存到云存储"""
    try:
        cache_dir = get_cache_dir()
        cache_file = os.path.join(cache_dir, 'data_cache.json')
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Cache saved to cloud storage: {cache_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save cache to cloud: {str(e)}")
        return False

def load_cache_from_cloud():
    """从云存储加载缓存"""
    try:
        cache_dir = get_cache_dir()
        cache_file = os.path.join(cache_dir, 'data_cache.json')
        
        if not os.path.exists(cache_file):
            logger.warning(f"Cache file not found: {cache_file}")
            return None
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Cache loaded from cloud storage: {cache_file}")
        return data
    except Exception as e:
        logger.error(f"Failed to load cache from cloud: {str(e)}")
        return None 