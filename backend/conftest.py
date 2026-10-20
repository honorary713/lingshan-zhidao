import os
import sys

# 把 backend 目录加入模块搜索路径，确保 `from app...` 在任何工作目录下都能导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
