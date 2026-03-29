"""
用户模型 - 定义教师和学生用户
============================

本文件定义了两个用户模型：
- Teacher: 教师用户
- Student: 学生用户

数据库表结构说明：
----------------
1. teachers 表：存储教师用户信息
2. students 表：存储学生用户信息

两个表的结构类似，但学生表增加了学号字段（student_id）。
"""

from extensions import db
from datetime import datetime
from typing import Optional, Dict, Any

from utils.datetime_display import format_stored_utc_as_local


class Teacher(db.Model):
    """
    教师用户模型

    对应数据库表：teachers

    字段说明：
    ---------
    - id: 主键， tự动递增
    - username: 用户名，唯一，不能为空
    - password_hash: 密码哈希值（不存储明文密码）
    - email: 邮箱，唯一，不能为空
    - real_name: 真实姓名
    - created_at: 创建时间

    关系说明：
    ---------
    - classes: 一个教师可以创建多个班级（一对多关系）
    """
    __tablename__ = 'teachers'  # 指定数据库表名

    # ========== 字段定义 ==========
    id = db.Column(
        db.Integer,
        primary_key=True,
        comment='教师ID'
    )
    """主键，自增 ID"""

    username = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
        index=True,
        comment='用户名'
    )
    """用户名，必须唯一，用于登录"""

    password_hash = db.Column(
        db.String(255),
        nullable=False,
        comment='密码哈希'
    )
    """密码的哈希值（使用 werkzeug.security 生成）

    注意：永远不要存储明文密码！
    生成哈希：password_hash = generate_password_hash(password)
    验证密码：check_password_hash(password_hash, password)
    """

    email = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
        index=True,
        comment='邮箱'
    )
    """邮箱地址，必须唯一，用于找回密码"""

    real_name = db.Column(
        db.String(50),
        nullable=False,
        comment='真实姓名'
    )
    """教师的真实姓名"""

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        comment='创建时间'
    )
    """账户创建时间"""

    # ========== 关系定义 ==========
    classes = db.relationship(
        'Class',
        backref='teacher',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    """
    关联到 Class 模型（一个教师多个班级）

    参数说明：
    - 'Class': 关联的模型类名
    - backref='teacher': 在 Class 模型中自动创建 teacher 属性
    - lazy='dynamic': 延迟加载，返回查询对象而不是列表
    - cascade='all, delete-orphan': 级联删除

    使用示例：
        # 获取教师的所有班级
        teacher = Teacher.query.get(1)
        my_classes = teacher.classes.all()

        # 通过班级获取教师
        class_obj = Class.query.get(1)
        teacher = class_obj.teacher
    """

    # ========== 方法定义 ==========
    def __repr__(self) -> str:
        """
        对象的字符串表示

        在打印或调试时显示：<Teacher username>
        """
        return f'<Teacher {self.username}>'

    def to_dict(self) -> Dict[str, Any]:
        """
        将模型转换为字典格式

        通常用于返回给前端 API

        返回：
            字典，包含所有需要的字段
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'real_name': self.real_name,
            'created_at': format_stored_utc_as_local(self.created_at),
        }

    def check_password(self, password: str) -> bool:
        """
        检查密码是否正确

        参数：
            password: 用户输入的明文密码

        返回：
            bool: 密码是否匹配
        """
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)


class Student(db.Model):
    """
    学生用户模型

    对应数据库表：students

    字段说明：
    ---------
    - id: 主键，自增
    - username: 用户名，唯一
    - password_hash: 密码哈希
    - email: 邮箱，唯一
    - real_name: 真实姓名
    - student_id: 学号，唯一
    - created_at: 创建时间

    关系说明：
    ---------
    - classes: 一个学生可以加入多个班级（多对多，通过 ClassStudent 关联）
    - answers: 学生提交的答案（一对多）
    - checkins: 学生的签到记录（一对多）
    """
    __tablename__ = 'students'

    # ========== 字段定义 ==========
    id = db.Column(
        db.Integer,
        primary_key=True,
        comment='学生ID'
    )
    """主键，自增 ID"""

    username = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
        index=True,
        comment='用户名'
    )
    """用户名，用于登录"""

    password_hash = db.Column(
        db.String(255),
        nullable=False,
        comment='密码哈希'
    )
    """密码哈希值"""

    email = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
        index=True,
        comment='邮箱'
    )
    """邮箱地址"""

    real_name = db.Column(
        db.String(50),
        nullable=False,
        comment='真实姓名'
    )
    """学生的真实姓名"""

    student_id = db.Column(
        db.String(20),
        nullable=False,
        unique=True,
        index=True,
        comment='学号'
    )
    """学生的学号（学校分配的唯一标识）

    注意：学号通常由学校分配，格式可能为：
    - 2023001234（年级+序号）
    - 123456（简单的数字序号）
    """

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        comment='创建时间'
    )
    """账户创建时间"""

    # ========== 关系定义 ==========
    classes = db.relationship(
        'Class',
        secondary='class_students',
        backref=db.backref('students', lazy='dynamic'),
        lazy='dynamic'
    )
    """
    关联到 Class 模型（多对多关系）

    说明：
    - secondary='class_students': 指定关联表
    - backref=db.backref(...): 在 Class 模型中创建反向引用
    - lazy='dynamic': 延迟加载

    使用示例：
        student = Student.query.get(1)
        my_classes = student.classes.all()
    """

    answers = db.relationship(
        'Answer',
        backref='student',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    """学生提交的所有答案"""

    checkins = db.relationship(
        'Checkin',
        backref='student',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    """学生的签到记录"""

    # ========== 方法定义 ==========
    def __repr__(self) -> str:
        return f'<Student {self.username}({self.student_id})>'

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'real_name': self.real_name,
            'student_id': self.student_id,
            'created_at': format_stored_utc_as_local(self.created_at),
        }

    def check_password(self, password: str) -> bool:
        """检查密码"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
