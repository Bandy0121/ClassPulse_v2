"""
Blueprint 初始化文件
===================

本文件用于注册所有 API 蓝图，保持主应用文件的整洁。

什么是 Blueprint（蓝图）？
-------------------------
蓝图是 Flask 的模块化机制，它可以：
1. 将不同的功能分离到不同的文件中
2. 每个蓝图有独立的路由定义
3. 可以在主应用中注册蓝图并设置 URL 前缀

例如：
    auth_bp (认证蓝图) => /api/auth/*
    teacher_bp (教师蓝图) => /api/teacher/*
    student_bp (学生蓝图) => /api/student/*
"""

# 从各个模块导入蓝图实例
# 这些导入会在各自的__init__.py中创建蓝图对象
from blueprints import auth
from blueprints import teacher
from blueprints import student
from blueprints import stats
