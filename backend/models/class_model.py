"""
班级模型 - 定义班级和班级-学生关联
==================================

本文件定义了两个模型：
- Class: 班级模型，由教师创建
- ClassStudent: 班级-学生关联模型，记录学生加入班级的关系

数据库表结构说明：
----------------
1. classes 表：存储班级信息
2. class_students 表：关联表，实现学生和班级的多对多关系
"""

from extensions import db
from datetime import datetime
from typing import Optional, Dict, Any

from utils.datetime_display import format_stored_utc_as_local
import random
import string


def generate_class_code(length: int = 8) -> str:
    """
    生成唯一的班级邀请码

    班级码用于让学生加入班级，教师将班级码分享给学生，
    学生输入班级码后可以加入班级。

    参数：
        length: 班级码长度，默认 8 位

    返回：
        str: 由大写字母和数字组成的随机字符串

    示例：
        generate_class_code()  # 可能返回 "ABCD1234"
        generate_class_code(6)  # 可能返回 "XYZ789"
    """
    # 定义可用字符：大写字母 + 数字
    characters = string.ascii_uppercase + string.digits

    # 生成随机字符串
    class_code = ''.join(random.choices(characters, k=length))

    # 检查是否重复（几乎不可能，但为了保险）
    if Class.query.filter_by(class_code=class_code).first():
        return generate_class_code(length)

    return class_code


class Class(db.Model):
    """
    班级模型

    对应数据库表：classes

    字段说明：
    ---------
    - id: 主键
    - name: 班级名称
    - class_code: 班级邀请码（用于学生加入）
    - description: 班级描述
    - teacher_id: 关联的教师ID
    - created_at: 创建时间
    """
    __tablename__ = 'classes'

    # ========== 字段定义 ==========
    id = db.Column(
        db.Integer,
        primary_key=True,
        comment='班级ID'
    )
    """主键，自增 ID"""

    name = db.Column(
        db.String(100),
        nullable=False,
        comment='班级名称'
    )
    """
    班级名称，如：
    - "2023级计算机科学1班"
    - "Python编程入门"
    - "Web开发课程"
    """

    class_code = db.Column(
        db.String(20),
        nullable=False,
        unique=True,
        index=True,
        comment='班级邀请码'
    )
    """
    班级邀请码，唯一标识符

    用途：
    - 学生通过输入班级码加入班级
    - 生成二维码分享给学生

    生成方式：
    - 使用 generate_class_code() 函数自动生成
    - 格式：6-8 位大写字母和数字组合
    """

    description = db.Column(
        db.Text,
        comment='班级描述'
    )
    """
    班级描述信息，可选

    示例：
    - "这是2023级计算机科学专业的必修课程"
    - "本课程讲解 Python 编程基础"
    """

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey('teachers.id', ondelete='CASCADE'),
        nullable=False,
        comment='教师ID'
    )
    """
    关联的教师ID（外键）

    参数说明：
    - db.ForeignKey('teachers.id'): 引用 teachers 表的 id 字段
    - ondelete='CASCADE': 级联删除，当教师被删除时，班级也被删除
    """

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        comment='创建时间'
    )
    """班级创建时间"""

    # ========== 关系定义 ==========
    # students：由 Student.classes 的 secondary + backref='students' 自动挂到本模型
    assessments = db.relationship(
        'Assessment',
        backref='school_class',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    """本班级下的随堂测试（Assessment.class_id → classes.id）"""

    # ========== 方法定义 ==========
    def __repr__(self) -> str:
        return f'<Class {self.name}>'

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'class_code': self.class_code,
            'description': self.description or '',
            'teacher_id': self.teacher_id,
            'created_at': format_stored_utc_as_local(self.created_at),
        }

    def get_student_count(self) -> int:
        """获取班级学生人数"""
        return self.students.count()

    def get_assessment_count(self) -> int:
        """获取班级测试数量"""
        return self.assessments.count()


class ClassStudent(db.Model):
    """
    班级-学生关联模型

    这是一个关联表（Association Table），用于实现学生和班级的多对多关系。

    对应数据库表：class_students

    字段说明：
    ---------
    - id: 主键
    - class_id: 班级ID（外键）
    - student_id: 学生ID（外键）
    - joined_at: 加入时间
    - status: 关联状态（正常/已退出）
    """
    __tablename__ = 'class_students'

    # ========== 字段定义 ==========
    id = db.Column(
        db.Integer,
        primary_key=True,
        comment='关联ID'
    )
    """主键，自增 ID"""

    class_id = db.Column(
        db.Integer,
        db.ForeignKey('classes.id', ondelete='CASCADE'),
        nullable=False,
        comment='班级ID'
    )
    """关联的班级 ID"""

    student_id = db.Column(
        db.Integer,
        db.ForeignKey('students.id', ondelete='CASCADE'),
        nullable=False,
        comment='学生ID'
    )
    """关联的学生 ID"""

    joined_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        comment='加入时间'
    )
    """学生加入班级的时间"""

    status = db.Column(
        db.SmallInteger,
        default=1,
        comment='状态: 1-正常, 0-已退出'
    )
    """
    关联状态
    - 1: 正常（学生在班级中）
    - 0: 已退出（学生已退出班级）
    """

    # ========== 关系定义 ==========
    # 这里不需要定义 relationship，因为这是关联表

    # ========== 方法定义 ==========
    def __repr__(self) -> str:
        return f'<ClassStudent Class {self.class_id} - Student {self.student_id}>'

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'class_id': self.class_id,
            'student_id': self.student_id,
            'joined_at': format_stored_utc_as_local(self.joined_at),
            'status': self.status
        }

    # ========== 类方法 ==========
    @classmethod
    def join_class(cls, class_id: int, student_id: int) -> 'ClassStudent':
        """
        学生加入班级

        参数：
            class_id: 班级 ID
            student_id: 学生 ID

        返回：
            ClassStudent 对象

        异常：
            如果学生已经在班级中，返回现有的关联记录
        """
        # 检查是否已经存在关联
        existing = cls.query.filter_by(
            class_id=class_id,
            student_id=student_id,
            status=1
        ).first()

        if existing:
            return existing

        # 创建新的关联
        class_student = cls(
            class_id=class_id,
            student_id=student_id,
            status=1
        )

        db.session.add(class_student)
        db.session.commit()

        return class_student

    @classmethod
    def leave_class(cls, class_id: int, student_id: int) -> bool:
        """
        学生退出班级

        参数：
            class_id: 班级 ID
            student_id: 学生 ID

        返回：
            bool: 操作是否成功
        """
        # 查找关联记录
        class_student = cls.query.filter_by(
            class_id=class_id,
            student_id=student_id
        ).first()

        if not class_student:
            return False

        # 更新状态为已退出
        class_student.status = 0
        db.session.commit()

        return True
