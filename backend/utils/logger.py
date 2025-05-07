#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日誌設置 - 配置系統日誌
"""

import logging
import os
import sys
from datetime import datetime

def setup_logger(log_level=logging.INFO, log_to_file=True):
    """設置日誌系統
    
    Args:
        log_level (int, optional): 日誌級別，默認為INFO
        log_to_file (bool, optional): 是否記錄到文件，默認為True
        
    Returns:
        logging.Logger: 根日誌記錄器
    """
    # 創建根日誌記錄器
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 清除現有的處理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 創建控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # 設置格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加控制台處理器
    logger.addHandler(console_handler)
    
    # 如果需要，添加文件處理器
    if log_to_file:
        # 創建日誌目錄
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "logs"
        )
        os.makedirs(log_dir, exist_ok=True)
        
        # 創建日誌文件名
        log_file = os.path.join(
            log_dir,
            f"robot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        # 創建文件處理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # 添加文件處理器
        logger.addHandler(file_handler)
        
        logger.info(f"日誌將記錄到文件: {log_file}")
    
    return logger
