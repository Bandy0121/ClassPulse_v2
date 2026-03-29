from extensions import db
from datetime import datetime
from typing import Optional, Dict, Any

from utils.datetime_display import format_stored_utc_as_local
import random
import string


def generate_class_code(length: int = 8) -> str:
    # 定义可用字符：大写字母 + 数字
    characters = string.ascii_uppercase + string.digits

    # 生成随机字符串
    class_code = ''.join(random.choices(characters, k=length))

    # 检查是否重复（几乎不可能，但为了保险）
    if Class.query.filter_by(class_code=class_code).first():
        return generate_class_code(length)

    return class_code


class Class(db.Model):
    __tablename__ = 'classes'

    id = db.Column(
        db.Integer,
        primary_key=True,
        comment='班级ID'
    )

    name = db.Column(
        db.String(100),
        nullable=False,
        comment='班级名称'
    )
    class_code = db.Column(
        db.String(20),
        nullable=False,
        unique=True,
        index=True,
        comment='班级邀请码'
    )
    description = db.Column(
        db.Text,
        comment='班级描述'
    )
    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey('teachers.id', ondelete='CASCADE'),
        nullable=False,
        comment='教师ID'
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        comment='创建时间'
    )

    # students：由 Student.classes 的 secondary + backref='students' 自动挂到本模型
    assessments = db.relationship(
        'Assessment',
        backref='school_class',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<Class {self.name}>'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'class_code': self.class_code,
            'description': self.description or '',
            'teacher_id': self.teacher_id,
            'created_at': format_stored_utc_as_local(self.created_at),
        }

    def get_student_count(self) -> int:
        return self.students.count()

    def get_assessment_count(self) -> int:
        return self.assessments.count()


class ClassStudent(db.Model):
    __tablename__ = 'class_students'

    id = db.Column(
        db.Integer,
        primary_key=True,
        comment='关联ID'
    )

    class_id = db.Column(
        db.Integer,
        db.ForeignKey('classes.id', ondelete='CASCADE'),
        nullable=False,
        comment='班级ID'
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey('students.id', ondelete='CASCADE'),
        nullable=False,
        comment='学生ID'
    )

    joined_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        comment='加入时间'
    )

    status = db.Column(
        db.SmallInteger,
        default=1,
        comment='状态: 1-正常, 0-已退出'
    )
    # 这里不需要定义 relationship，因为这是关联表

    def __repr__(self) -> str:
        return f'<ClassStudent Class {self.class_id} - Student {self.student_id}>'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'class_id': self.class_id,
            'student_id': self.student_id,
            'joined_at': format_stored_utc_as_local(self.joined_at),
            'status': self.status
        }

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
