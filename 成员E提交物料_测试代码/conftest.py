"""
测试配置
"""
import pytest
import os
import sys

# 设置测试环境
os.environ["APP_ENV"] = "testing"

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
