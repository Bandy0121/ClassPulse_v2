from extensions import db
from datetime import datetime
from typing import Optional, Dict, Any, List

from utils.datetime_display import format_stored_utc_as_local


class Assessment(db.Model):
    __tablename__ = 'assessments'

    id = db.Column(
        db.Integer,
        primary_key=True,
        comment='测试ID'
    )

    class_id = db.Column(
        db.Integer,
        db.ForeignKey('classes.id', ondelete='CASCADE'),
        nullable=False,
        comment='班级ID'
    )
    title = db.Column(
        db.String(200),
        nullable=False,
        comment='测试标题'
    )
    description = db.Column(
        db.Text,
        comment='测试描述'
    )
    start_time = db.Column(
        db.DateTime,
        nullable=False,
        comment='开始时间'
    )
    end_time = db.Column(
        db.DateTime,
        nullable=False,
        comment='结束时间'
    )
    duration_minutes = db.Column(
        db.Integer,
        default=5,
        comment='持续时间(分钟)'
    )
    max_attempts = db.Column(
        db.SmallInteger,
        default=1,
        comment='最大尝试次数'
    )
    show_correct_after_submit = db.Column(
        db.Boolean,
        default=True,
        comment='提交后是否显示正确答案'
    )
    is_published = db.Column(
        db.Boolean,
        default=False,
        comment='是否已发布'
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        comment='创建时间'
    )

    questions = db.relationship(
        'Question',
        backref='assessment',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    answers = db.relationship(
        'Answer',
        backref='assessment',
        lazy='dynamic'
    )

    def __repr__(self) -> str:
        return f'<Assessment {self.title}>'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'class_id': self.class_id,
            'title': self.title,
            'description': self.description or '',
            'start_time': format_stored_utc_as_local(self.start_time),
            'end_time': format_stored_utc_as_local(self.end_time),
            'duration_minutes': self.duration_minutes,
            'max_attempts': self.max_attempts,
            'show_correct_after_submit': self.show_correct_after_submit,
            'is_published': self.is_published,
            'created_at': format_stored_utc_as_local(self.created_at),
        }

    def get_question_count(self) -> int:
        return self.questions.count()

    def get_student_count(self) -> int:
        return db.session.query(db.func.count(db.distinct(Answer.student_id)))\
            .filter(Answer.assessment_id == self.id)\
            .scalar()

    def is_available(self) -> bool:
        """
        测试是否可用（在时间范围内且已发布）

        返回：
            bool: 测试是否可参与
        """
        if not self.is_published:
            return False

        now = datetime.utcnow()
        if now < self.start_time or now > self.end_time:
            return False

        return True

    def get_score(self, student_id: int) -> Optional[Dict[str, Any]]:
        """
        获取学生的测试得分

        参数：
            student_id: 学生 ID

        返回：
            dict 或 None:
            {
                'total_score': 总分,
                'max_score': 满分,
                'correct_count': 正确题数,
                'wrong_count': 错误题数,
                'submitted_at': 提交时间
            }
        """
        # 计算该学生的答案
        result = db.session.query(
            db.func.sum(Answer.is_correct).label('correct_count'),
            db.func.count(Answer.id).label('total_count'),
            db.func.max(Answer.submitted_at).label('submitted_at')
        ).filter(
            Answer.assessment_id == self.id,
            Answer.student_id == student_id
        ).first()

        if not result or result.total_count == 0:
            return None

        # 计算得分（假设每题 1 分，可以扩展为加权计算）
        total_score = result.correct_count
        max_score = result.total_count

        return {
            'total_score': total_score,
            'max_score': max_score,
            'correct_count': result.correct_count,
            'wrong_count': result.total_count - result.correct_count,
            'submitted_at': format_stored_utc_as_local(result.submitted_at),
        }


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(
        db.Integer,
        primary_key=True,
        comment='题目ID'
    )

    assessment_id = db.Column(
        db.Integer,
        db.ForeignKey('assessments.id', ondelete='CASCADE'),
        nullable=False,
        comment='测试ID'
    )
    question_type = db.Column(
        db.SmallInteger,
        default=1,
        comment='题型: 1-单选, 2-多选'
    )
    content = db.Column(
        db.Text,
        nullable=False,
        comment='题目内容'
    )
    option_a = db.Column(
        db.String(500),
        nullable=False,
        comment='选项A'
    )

    option_b = db.Column(
        db.String(500),
        nullable=False,
        comment='选项B'
    )

    option_c = db.Column(
        db.String(500),
        comment='选项C'
    )

    option_d = db.Column(
        db.String(500),
        comment='选项D'
    )

    correct_answer = db.Column(
        db.String(50),
        nullable=False,
        comment='正确答案'
    )
    score = db.Column(
        db.DECIMAL(5, 2),
        default=10.00,
        comment='分值'
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        comment='创建时间'
    )

    answers = db.relationship(
        'Answer',
        backref='question',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<Question {self.id} - {self.content[:30]}...>'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'assessment_id': self.assessment_id,
            'question_type': self.question_type,
            'content': self.content,
            'option_a': self.option_a,
            'option_b': self.option_b,
            'option_c': self.option_c,
            'option_d': self.option_d,
            'correct_answer': self.correct_answer,
            'score': float(self.score) if self.score else 0,
            'created_at': format_stored_utc_as_local(self.created_at),
        }

    def get_options(self) -> Dict[str, str]:
        """
        获取所有选项

        返回：
            dict: 选项字典，如 {'A': '选项A内容', 'B': '选项B内容', ...}
        """
        options = {
            'A': self.option_a,
            'B': self.option_b
        }
        if self.option_c:
            options['C'] = self.option_c
        if self.option_d:
            options['D'] = self.option_d
        return options

    def is_correct(self, selected: str) -> bool:
        """
        判断答案是否正确

        参数：
            selected: 学生选择的答案（如 "A" 或 "A,B"）

        返回：
            bool: 是否正确
        """
        # 统一格式：去掉空格，转大写
        selected = selected.strip().upper()
        correct = self.correct_answer.strip().upper()

        return selected == correct


class Answer(db.Model):
    __tablename__ = 'answers'

    id = db.Column(
        db.Integer,
        primary_key=True,
        comment='答案ID'
    )

    assessment_id = db.Column(
        db.Integer,
        db.ForeignKey('assessments.id', ondelete='CASCADE'),
        nullable=False,
        comment='测试ID'
    )

    question_id = db.Column(
        db.Integer,
        db.ForeignKey('questions.id', ondelete='CASCADE'),
        nullable=False,
        comment='题目ID'
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey('students.id', ondelete='CASCADE'),
        nullable=False,
        comment='学生ID'
    )

    selected_option = db.Column(
        db.String(50),
        nullable=False,
        comment='选择的答案'
    )
    is_correct = db.Column(
        db.Boolean,
        default=False,
        comment='是否正确'
    )
    submitted_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        comment='提交时间'
    )

    response_time_seconds = db.Column(
        db.Integer,
        comment='答题耗时(秒)'
    )
    attempt_number = db.Column(
        db.SmallInteger,
        default=1,
        comment='尝试次数'
    )
    # 通过 Question 和 Assessment 的 backref 已经有反向引用

    def __repr__(self) -> str:
        return f'<Answer Student {self.student_id} - Question {self.question_id}>'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'assessment_id': self.assessment_id,
            'question_id': self.question_id,
            'student_id': self.student_id,
            'selected_option': self.selected_option,
            'is_correct': self.is_correct,
            'submitted_at': format_stored_utc_as_local(self.submitted_at),
            'response_time_seconds': self.response_time_seconds,
            'attempt_number': self.attempt_number
        }

    @classmethod
    def submit_answer(
        cls,
        assessment_id: int,
        question_id: int,
        student_id: int,
        selected_option: str,
        response_time: int = 0,
        attempt: int = 1
    ) -> 'Answer':
        """
        提交答案

        这是一个类方法，方便在其他地方调用

        参数：
            assessment_id: 测试 ID
            question_id: 题目 ID
            student_id: 学生 ID
            selected_option: 选择的答案
            response_time: 答题耗时（秒）
            attempt: 尝试次数

        返回：
            Answer: 提交的答案对象
        """
        # 计算是否正确
        question = Question.query.get(question_id)
        if not question:
            raise ValueError('题目不存在')

        is_correct = question.is_correct(selected_option)

        # 创建答案记录
        answer = cls(
            assessment_id=assessment_id,
            question_id=question_id,
            student_id=student_id,
            selected_option=selected_option,
            is_correct=is_correct,
            response_time_seconds=response_time,
            attempt_number=attempt
        )

        db.session.add(answer)
        db.session.commit()

        return answer

    @classmethod
    def submit_assessment(
        cls,
        assessment_id: int,
        student_id: int,
        answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        提交整个测试的答案

        参数：
            assessment_id: 测试 ID
            student_id: 学生 ID
            answers: 答案列表，每个元素是 {
                'question_id': 题目ID,
                'selected_option': 选择的答案,
                'response_time': 答题耗时（可选）
            }

        返回：
            dict: 提交结果 {
                'total': 题目总数,
                'correct': 正确数,
                'score': 得分
            }
        """
        total = len(answers)
        correct = 0
        total_score = 0

        for ans in answers:
            question_id = ans['question_id']
            selected_option = ans['selected_option']
            response_time = ans.get('response_time', 0)

            # 获取题目信息
            question = Question.query.get(question_id)
            if not question:
                continue

            # 判断答案是否正确
            is_correct = question.is_correct(selected_option)
            if is_correct:
                correct += 1
                total_score += float(question.score)

            # 提交答案
            cls.submit_answer(
                assessment_id=assessment_id,
                question_id=question_id,
                student_id=student_id,
                selected_option=selected_option,
                response_time=response_time
            )

        return {
            'total': total,
            'correct': correct,
            'score': total_score
        }
