"""
数据库模型初始化文件
====================

本目录包含所有 SQLAlchemy 数据模型定义。

模型说明：
---------
1. Teacher: 教师用户模型
2. Student: 学生用户模型
3. Class: 班级模型
4. ClassStudent: 班级-学生关联模型（多对多关系）
5. Assessment: 随堂测试模型
6. Question: 测试题目模型
7. Answer: 学生答案模型
8. Checkin: 签到记录模型

使用方式：
    from extensions import db
    from models import Teacher, Student, Class, Assessment

    # 创建新用户
    teacher = Teacher(username='test', password_hash='xxx', ...)
    db.session.add(teacher)
    db.session.commit()
"""

# 导入所有模型，方便一次性导入
from .user import Teacher, Student
from .class_model import Class, ClassStudent
from .assessment import Assessment, Question, Answer
from .checkin import Checkin

__all__ = [
    'Teacher',
    'Student',
    'Class',
    'ClassStudent',
    'Assessment',
    'Question',
    'Answer',
    'Checkin'
]
