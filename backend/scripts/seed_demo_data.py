"""
演示数据种子脚本（直接写库）
============================

生成：4 名教师、40 名学生、2 个班级（高数、英语）、10 份测验（每份 10~20 题）、
     每名学生对每份测验的随机作答记录。

用法（在 backend 目录下）::

    python scripts/seed_demo_data.py

默认会先删除 username/class_code/测验标题带此前缀的旧数据，再插入。
所有演示账号密码均为：demo123456

前缀可通过环境变量 SEED_TAG 修改（默认 seed_demo）。
"""

from __future__ import annotations

import logging
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from werkzeug.security import generate_password_hash

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
os.chdir(BACKEND_ROOT)

TAG = os.environ.get("SEED_TAG", "seed_demo")
PWD = "demo123456"
PWD_HASH = generate_password_hash(PWD)

OPTIONS = ["A", "B", "C", "D"]


def main() -> None:
    from app import create_app
    from extensions import db
    from models.user import Teacher, Student
    from models.class_model import Class, ClassStudent
    from models.assessment import Assessment, Question, Answer

    app = create_app("development")
    with app.app_context():
        cleanup(db, Teacher, Student, Class, ClassStudent, Assessment, Question, Answer)
        db.session.commit()

        teachers = []
        for i in range(1, 5):
            u = f"{TAG}_t{i}"
            t = Teacher(
                username=u,
                password_hash=PWD_HASH,
                email=f"{u}@demo.local",
                real_name=f"演示教师{i}",
            )
            db.session.add(t)
            teachers.append(t)
        db.session.flush()

        students = []
        for i in range(1, 41):
            u = f"{TAG}_s{i:02d}"
            s = Student(
                username=u,
                password_hash=PWD_HASH,
                email=f"{u}@demo.local",
                real_name=f"演示学生{i:02d}",
                student_id=f"D{2026}{i:04d}",
            )
            db.session.add(s)
            students.append(s)
        db.session.flush()

        c_math = Class(
            name="高等数学（演示）",
            class_code=f"{TAG.upper()}_GS01",
            description="高数班",
            teacher_id=teachers[0].id,
        )
        c_eng = Class(
            name="大学英语（演示）",
            class_code=f"{TAG.upper()}_EN01",
            description="英语班",
            teacher_id=teachers[1].id,
        )
        db.session.add_all([c_math, c_eng])
        db.session.flush()
        math_code, eng_code = c_math.class_code, c_eng.class_code

        for st in students:
            db.session.add(
                ClassStudent(class_id=c_math.id, student_id=st.id, status=1)
            )
            db.session.add(
                ClassStudent(class_id=c_eng.id, student_id=st.id, status=1)
            )
        db.session.flush()

        now = datetime.utcnow()
        assessments: list[Assessment] = []
        class_cycle = [c_math, c_eng]
        titles_math = [
            "极限与连续小测",
            "导数应用测验",
            "积分基础",
            "级数入门",
            "综合练习一",
        ]
        titles_eng = [
            "Unit 1 Vocabulary",
            "Grammar Focus",
            "Reading A",
            "Listening B",
            "Writing 基础",
        ]

        for idx in range(10):
            cls = class_cycle[idx % 2]
            if cls.id == c_math.id:
                title = f"[{TAG}] {titles_math[idx // 2 % len(titles_math)]}"
            else:
                title = f"[{TAG}] {titles_eng[idx // 2 % len(titles_eng)]}"

            days_ago = 20 - idx * 2
            start = now - timedelta(days=days_ago, hours=2)
            end = start + timedelta(days=14)
            dur = random.randint(30, 90)

            a = Assessment(
                class_id=cls.id,
                title=title,
                description=f"演示数据测验 #{idx + 1}",
                start_time=start,
                end_time=end,
                duration_minutes=dur,
                max_attempts=1,
                show_correct_after_submit=True,
                is_published=True,
            )
            db.session.add(a)
            assessments.append(a)
        db.session.flush()

        all_questions: list[tuple[Assessment, list[Question]]] = []
        for a in assessments:
            nq = random.randint(10, 20)
            qs: list[Question] = []
            for qi in range(1, nq + 1):
                correct = random.choice(OPTIONS)
                q = Question(
                    assessment_id=a.id,
                    question_type=1,
                    content=f"[{TAG}] 第{qi}题：请选择正确答案（测验「{a.title[:16]}…」）",
                    option_a="选项 A",
                    option_b="选项 B",
                    option_c="选项 C",
                    option_d="选项 D",
                    correct_answer=correct,
                    score=random.choice([5, 5, 8, 10]),
                )
                db.session.add(q)
                qs.append(q)
            all_questions.append((a, qs))
        db.session.flush()

        rng = random.Random(42)
        for a, qs in all_questions:
            base_correct_rate = rng.uniform(0.45, 0.92)
            for st in students:
                span_h = max(1, int((a.end_time - a.start_time).total_seconds() // 3600))
                submit_base = a.start_time + timedelta(
                    hours=rng.randint(1, min(72, span_h)),
                )
                for q in qs:
                    is_ok = rng.random() < base_correct_rate
                    if is_ok:
                        selected = q.correct_answer
                    else:
                        wrong = [x for x in OPTIONS if x != q.correct_answer]
                        selected = rng.choice(wrong)
                    jitter = rng.randint(0, 3600)
                    sub_at = min(submit_base + timedelta(seconds=jitter), a.end_time)
                    ans = Answer(
                        assessment_id=a.id,
                        question_id=q.id,
                        student_id=st.id,
                        selected_option=selected,
                        is_correct=(selected.strip().upper() == q.correct_answer.strip().upper()),
                        submitted_at=sub_at,
                        response_time_seconds=rng.randint(5, 180),
                        attempt_number=1,
                    )
                    db.session.add(ans)

        n_assess = len(assessments)
        db.session.commit()
        print("完成。演示数据已写入数据库。")
        print(f"  教师登录: {TAG}_t1 ~ {TAG}_t4  密码: {PWD}")
        print(f"  学生登录: {TAG}_s01 ~ {TAG}_s40  密码: {PWD}")
        print(f"  班级码: {math_code}（高数）  {eng_code}（英语）")
        print(f"  测验数: {n_assess}，每份 10~20 题，40 名学生均有作答。")


def cleanup(db, Teacher, Student, Class, ClassStudent, Assessment, Question, Answer) -> None:
    """删除同 TAG 前缀的历史演示数据。"""
    prefix_tag = f"[{TAG}]"
    ids_a = [
        r[0]
        for r in db.session.query(Assessment.id).filter(Assessment.title.like(f"{prefix_tag}%")).all()
    ]
    if ids_a:
        Answer.query.filter(Answer.assessment_id.in_(ids_a)).delete(synchronize_session=False)
        Question.query.filter(Question.assessment_id.in_(ids_a)).delete(synchronize_session=False)
        Assessment.query.filter(Assessment.id.in_(ids_a)).delete(synchronize_session=False)

    codes = [f"{TAG.upper()}_GS01", f"{TAG.upper()}_EN01"]
    ids_c = [r[0] for r in db.session.query(Class.id).filter(Class.class_code.in_(codes)).all()]
    if ids_c:
        ClassStudent.query.filter(ClassStudent.class_id.in_(ids_c)).delete(
            synchronize_session=False
        )
        Class.query.filter(Class.id.in_(ids_c)).delete(synchronize_session=False)

    Student.query.filter(Student.username.like(f"{TAG}_s%")).delete(synchronize_session=False)
    Teacher.query.filter(Teacher.username.like(f"{TAG}_t%")).delete(synchronize_session=False)


if __name__ == "__main__":
    main()
