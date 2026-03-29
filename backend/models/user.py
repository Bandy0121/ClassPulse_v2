from extensions import db
from datetime import datetime
from typing import Optional, Dict, Any

from utils.datetime_display import format_stored_utc_as_local


class Teacher(db.Model):
    __tablename__ = 'teachers'

    id = db.Column(
        db.Integer,
        primary_key=True,
        comment='教师ID'
    )

    username = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
        index=True,
        comment='用户名'
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False,
        comment='密码哈希'
    )
    email = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
        index=True,
        comment='邮箱'
    )

    real_name = db.Column(
        db.String(50),
        nullable=False,
        comment='真实姓名'
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        comment='创建时间'
    )

    classes = db.relationship(
        'Class',
        backref='teacher',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
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
    __tablename__ = 'students'

    id = db.Column(
        db.Integer,
        primary_key=True,
        comment='学生ID'
    )

    username = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
        index=True,
        comment='用户名'
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False,
        comment='密码哈希'
    )

    email = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
        index=True,
        comment='邮箱'
    )

    real_name = db.Column(
        db.String(50),
        nullable=False,
        comment='真实姓名'
    )

    student_id = db.Column(
        db.String(20),
        nullable=False,
        unique=True,
        index=True,
        comment='学号'
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        comment='创建时间'
    )

    classes = db.relationship(
        'Class',
        secondary='class_students',
        backref=db.backref('students', lazy='dynamic'),
        lazy='dynamic'
    )
    answers = db.relationship(
        'Answer',
        backref='student',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    checkins = db.relationship(
        'Checkin',
        backref='student',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<Student {self.username}({self.student_id})>'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'real_name': self.real_name,
            'student_id': self.student_id,
            'created_at': format_stored_utc_as_local(self.created_at),
        }

    def check_password(self, password: str) -> bool:
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
