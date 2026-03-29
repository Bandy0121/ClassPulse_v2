from flask import Blueprint, request, current_app
from datetime import datetime, timedelta
from flask_jwt_extended import jwt_required

from extensions import db
from models.user import Teacher, Student
from models.class_model import Class, ClassStudent, generate_class_code
from models.assessment import Assessment, Question, Answer
from models.checkin import Checkin

from utils.auth import get_current_user
from utils.datetime_display import (
    format_stored_utc_as_local,
    parse_client_datetime_to_utc_naive,
)
from utils.response import success_response, error_response

teacher_bp = Blueprint('teacher', __name__)


def _require_teacher():
    user = get_current_user()
    if user is None:
        return None, error_response(
            '请先登录或登录已失效', code=401, http_status=401
        )
    if not isinstance(user, Teacher):
        return None, error_response('需要教师账号', code=403, http_status=403)
    return user, None


@teacher_bp.route('/classes', methods=['GET'])
@jwt_required()
def get_teacher_classes():
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        classes = Class.query.filter_by(teacher_id=teacher.id).all()

        class_list = []
        for cls in classes:
            class_list.append({
                'id': cls.id,
                'name': cls.name,
                'class_code': cls.class_code,
                'description': cls.description or '',
                'student_count': cls.get_student_count(),
                'created_at': format_stored_utc_as_local(cls.created_at),
            })

        return success_response({'classes': class_list})

    except Exception as e:
        current_app.logger.error(f'获取班级列表失败: {str(e)}')
        return error_response(
            '获取班级列表失败', code=500, http_status=500
        )


@teacher_bp.route('/classes', methods=['POST'])
@jwt_required()
def create_class():
    try:
        data = request.get_json()

        if not data:
            return error_response('请求体不能为空', 400)

        name = data.get('name', '').strip()
        description = data.get('description', '').strip()

        if not name:
            return error_response('班级名称不能为空', 400)

        teacher, err = _require_teacher()
        if err:
            return err

        class_code = generate_class_code()

        new_class = Class(
            name=name,
            class_code=class_code,
            description=description,
            teacher_id=teacher.id
        )

        db.session.add(new_class)
        db.session.commit()

        return success_response(
            data=new_class.to_dict(),
            message='班级创建成功',
            code=201
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'创建班级失败: {str(e)}')
        return error_response('创建班级失败', code=500, http_status=500)


@teacher_bp.route('/classes/<int:class_id>', methods=['GET'])
@jwt_required()
def get_class_detail(class_id):
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        class_obj = Class.query.filter_by(
            id=class_id,
            teacher_id=teacher.id
        ).first()

        if not class_obj:
            return error_response('班级不存在或无权限访问', 404)

        class_info = class_obj.to_dict()
        class_info['student_count'] = class_obj.get_student_count()
        class_info['assessment_count'] = class_obj.get_assessment_count()

        students = []
        class_students = ClassStudent.query.filter_by(
            class_id=class_id,
            status=1
        ).all()

        for cs in class_students:
            student = Student.query.get(cs.student_id)
            if student:
                students.append({
                    'id': student.id,
                    'username': student.username,
                    'real_name': student.real_name,
                    'student_id': student.student_id,
                    'joined_at': format_stored_utc_as_local(cs.joined_at),
                })

        assessments = []
        for assessment in class_obj.assessments.all():
            assessments.append({
                'id': assessment.id,
                'title': assessment.title,
                'start_time': format_stored_utc_as_local(assessment.start_time),
                'end_time': format_stored_utc_as_local(assessment.end_time),
                'is_published': assessment.is_published,
                'question_count': assessment.get_question_count()
            })

        return success_response({
            'class_info': class_info,
            'students': students,
            'assessments': assessments
        })

    except Exception as e:
        current_app.logger.error(f'获取班级详情失败: {str(e)}')
        return error_response(
            '获取班级详情失败',
            code=500,
            http_status=500
        )


@teacher_bp.route('/classes/<int:class_id>', methods=['PUT'])
@jwt_required()
def update_class(class_id):
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        class_obj = Class.query.filter_by(
            id=class_id,
            teacher_id=teacher.id
        ).first()

        if not class_obj:
            return error_response('班级不存在或无权限访问', 404)

        data = request.get_json()
        if not data:
            return error_response('请求体不能为空', 400)

        name = data.get('name', '').strip()
        description = data.get('description', '').strip()

        if not name:
            return error_response('班级名称不能为空', 400)

        class_obj.name = name
        class_obj.description = description
        db.session.commit()

        return success_response(data=class_obj.to_dict(), message='班级更新成功')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'更新班级失败: {str(e)}')
        return error_response('更新班级失败', code=500, http_status=500)


@teacher_bp.route('/classes/<int:class_id>', methods=['DELETE'])
@jwt_required()
def delete_class(class_id):
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        class_obj = Class.query.filter_by(
            id=class_id,
            teacher_id=teacher.id
        ).first()

        if not class_obj:
            return error_response('班级不存在或无权限访问', 404)

        db.session.delete(class_obj)
        db.session.commit()

        return success_response(None, '班级已删除')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除班级失败: {str(e)}')
        return error_response('删除班级失败', code=500, http_status=500)


@teacher_bp.route('/classes/<int:class_id>/checkins', methods=['GET'])
@jwt_required()
def get_class_checkins_list(class_id):
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        class_obj = Class.query.filter_by(
            id=class_id,
            teacher_id=teacher.id
        ).first()

        if not class_obj:
            return error_response('班级不存在或无权限访问', 404)

        rows = []
        checkins = (
            Checkin.query.filter_by(class_id=class_id, status=1)
            .order_by(Checkin.timestamp.desc())
            .all()
        )
        for c in checkins:
            st = Student.query.get(c.student_id)
            rows.append({
                'real_name': st.real_name if st else '',
                'username': st.username if st else '',
                'student_no': st.student_id if st else '',
                'timestamp': format_stored_utc_as_local(c.timestamp),
                'location_hash': c.location_hash or '',
                'ip_address': c.ip_address or '',
            })

        return success_response({'checkins': rows})

    except Exception as e:
        current_app.logger.error(f'获取签到记录失败: {str(e)}')
        return error_response('获取签到记录失败', code=500, http_status=500)


@teacher_bp.route('/classes/<int:class_id>/assessments', methods=['GET'])
@jwt_required()
def get_class_assessments(class_id):
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        class_obj = Class.query.filter_by(
            id=class_id,
            teacher_id=teacher.id
        ).first()

        if not class_obj:
            return error_response('班级不存在或无权限访问', 404)

        assessments = []
        for a in class_obj.assessments.order_by(Assessment.created_at.desc()).all():
            assessments.append({
                'id': a.id,
                'title': a.title,
                'description': a.description or '',
                'start_time': format_stored_utc_as_local(a.start_time),
                'end_time': format_stored_utc_as_local(a.end_time),
                'duration_minutes': a.duration_minutes,
                'max_attempts': a.max_attempts,
                'is_published': a.is_published,
                'question_count': a.get_question_count(),
                'created_at': format_stored_utc_as_local(a.created_at),
            })

        return success_response({'assessments': assessments})

    except Exception as e:
        current_app.logger.error(f'获取测试列表失败: {str(e)}')
        return error_response('获取测试列表失败', code=500, http_status=500)


@teacher_bp.route('/classes/<int:class_id>/assessments', methods=['POST'])
@jwt_required()
def create_assessment(class_id):
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        class_obj = Class.query.filter_by(
            id=class_id,
            teacher_id=teacher.id
        ).first()

        if not class_obj:
            return error_response('班级不存在或无权限访问', 404)

        data = request.get_json()
        if not data:
            return error_response('请求体不能为空', 400)

        title = (data.get('title') or '').strip()
        if not title:
            return error_response('标题不能为空', 400)

        try:
            start_time = parse_client_datetime_to_utc_naive(data.get('start_time'))
        except (ValueError, TypeError):
            return error_response('开始时间格式无效', 400)

        duration = int(data.get('duration_minutes') or 0)
        if duration < 1:
            return error_response('考试时长至少 1 分钟', 400)

        end_time = data.get('end_time')
        if end_time:
            try:
                end_time = parse_client_datetime_to_utc_naive(end_time)
            except (ValueError, TypeError):
                return error_response('结束时间格式无效', 400)
        else:
            end_time = start_time + timedelta(minutes=duration)

        assessment = Assessment(
            class_id=class_id,
            title=title,
            description=(data.get('description') or '').strip(),
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration,
            max_attempts=int(data.get('max_attempts') or 1),
            show_correct_after_submit=bool(data.get('show_correct_after_submit', True)),
            is_published=False,
        )
        db.session.add(assessment)
        db.session.commit()

        return success_response(
            data={'id': assessment.id, **assessment.to_dict()},
            message='测试创建成功',
            code=201,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'创建测试失败: {str(e)}')
        return error_response('创建测试失败', code=500, http_status=500)


@teacher_bp.route('/assessments/<int:assessment_id>/questions', methods=['POST'])
@jwt_required()
def add_question(assessment_id):
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        assessment = (
            Assessment.query.filter(Assessment.id == assessment_id)
            .join(Class, Class.id == Assessment.class_id)
            .filter(Class.teacher_id == teacher.id)
            .first()
        )

        if not assessment:
            return error_response('测试不存在或无权限访问', 404)

        data = request.get_json()
        if not data:
            return error_response('请求体不能为空', 400)

        content = (data.get('content') or '').strip()
        option_a = (data.get('option_a') or '').strip()
        option_b = (data.get('option_b') or '').strip()
        correct = (data.get('correct_answer') or '').strip().upper()

        if not content or not option_a or not option_b or not correct:
            return error_response('题干、选项与正确答案不能为空', 400)

        q = Question(
            assessment_id=assessment_id,
            question_type=int(data.get('question_type') or 1),
            content=content,
            option_a=option_a,
            option_b=option_b,
            option_c=(data.get('option_c') or '').strip() or None,
            option_d=(data.get('option_d') or '').strip() or None,
            correct_answer=correct,
            score=float(data.get('score') or 10),
        )
        db.session.add(q)
        db.session.commit()

        return success_response(data=q.to_dict(), message='题目添加成功', code=201)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'添加题目失败: {str(e)}')
        return error_response('添加题目失败', code=500, http_status=500)


@teacher_bp.route('/assessments/<int:assessment_id>/publish', methods=['PUT'])
@jwt_required()
def publish_assessment(assessment_id):
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        assessment = (
            Assessment.query.filter(Assessment.id == assessment_id)
            .join(Class, Class.id == Assessment.class_id)
            .filter(Class.teacher_id == teacher.id)
            .first()
        )

        if not assessment:
            return error_response('测试不存在或无权限访问', 404)

        data = request.get_json()
        if not data or 'publish' not in data:
            return error_response('请求体缺少 publish 字段', 400)

        assessment.is_published = bool(data['publish'])
        db.session.commit()

        return success_response(
            data=assessment.to_dict(),
            message='测试已发布' if assessment.is_published else '已取消发布',
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'发布测试失败: {str(e)}')
        return error_response('发布测试失败', code=500, http_status=500)


@teacher_bp.route('/assessments/<int:assessment_id>', methods=['DELETE'])
@jwt_required()
def delete_assessment(assessment_id):
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        assessment = (
            Assessment.query.filter(Assessment.id == assessment_id)
            .join(Class, Class.id == Assessment.class_id)
            .filter(Class.teacher_id == teacher.id)
            .first()
        )

        if not assessment:
            return error_response('测试不存在或无权限访问', 404)

        db.session.delete(assessment)
        db.session.commit()

        return success_response(None, '测试已删除')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除测试失败: {str(e)}')
        return error_response('删除测试失败', code=500, http_status=500)


@teacher_bp.route('/assessments/<int:assessment_id>/statistics', methods=['GET'])
@jwt_required()
def get_assessment_statistics(assessment_id):
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        assessment = (
            Assessment.query.filter(Assessment.id == assessment_id)
            .join(Class, Class.id == Assessment.class_id)
            .filter(Class.teacher_id == teacher.id)
            .first()
        )

        if not assessment:
            return error_response('测试不存在或无权限访问', 404)

        class_obj = Class.query.get(assessment.class_id)
        total_students = class_obj.get_student_count() if class_obj else 0

        submitted_students = (
            db.session.query(db.func.count(db.distinct(Answer.student_id)))
            .filter(Answer.assessment_id == assessment_id)
            .scalar()
        ) or 0

        question_statistics = []
        for q in assessment.questions.all():
            total_attempts = Answer.query.filter_by(question_id=q.id).count()
            correct_count = Answer.query.filter_by(
                question_id=q.id, is_correct=True
            ).count()
            rate = (
                round(correct_count / total_attempts * 100, 2)
                if total_attempts
                else 0.0
            )
            question_statistics.append({
                'question_id': q.id,
                'content': q.content,
                'total_attempts': total_attempts,
                'correct_count': correct_count,
                'correct_rate': rate,
            })

        student_summary = []
        sid_rows = (
            db.session.query(Answer.student_id)
            .filter(Answer.assessment_id == assessment_id)
            .distinct()
            .all()
        )
        for (sid,) in sid_rows:
            st = Student.query.get(sid)
            sc = assessment.get_score(sid)
            if not sc:
                continue
            student_summary.append({
                'student_id': sid,
                'username': st.username if st else '',
                'real_name': st.real_name if st else '',
                'score': sc['total_score'],
                'max_score': sc['max_score'],
                'correct_count': sc['correct_count'],
                'wrong_count': sc['wrong_count'],
            })

        return success_response({
            'assessment_info': {
                'id': assessment.id,
                'title': assessment.title,
                'total_students': total_students,
                'submitted_students': submitted_students,
            },
            'question_statistics': question_statistics,
            'student_summary': student_summary,
        })

    except Exception as e:
        current_app.logger.error(f'获取统计失败: {str(e)}')
        return error_response('获取统计失败', code=500, http_status=500)


@teacher_bp.route(
    '/assessments/<int:assessment_id>/student/<int:student_id>/detail',
    methods=['GET'],
)
@jwt_required()
def get_student_assessment_detail(assessment_id, student_id):
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        assessment = (
            Assessment.query.filter(Assessment.id == assessment_id)
            .join(Class, Class.id == Assessment.class_id)
            .filter(Class.teacher_id == teacher.id)
            .first()
        )

        if not assessment:
            return error_response('测试不存在或无权限访问', 404)

        student = Student.query.get(student_id)

        if not student:
            return error_response('学生不存在', 404)

        answers = db.session.query(
            Answer,
            Question.content,
            Question.score,
            Question.correct_answer
        ).join(
            Question, Answer.question_id == Question.id
        ).filter(
            Answer.assessment_id == assessment_id,
            Answer.student_id == student_id
        ).all()

        total_score = 0
        answer_list = []

        for ans, content, score, correct_answer in answers:
            total_score += float(score) if ans.is_correct else 0

            answer_list.append({
                'question_id': ans.question_id,
                'content': content,
                'selected_option': ans.selected_option,
                'correct_answer': correct_answer,
                'is_correct': ans.is_correct,
                'score': float(score) if ans.is_correct else 0
            })

        max_score = sum(float(q.score) for q in assessment.questions.all())

        return success_response({
            'student_info': {
                'id': student.id,
                'username': student.username,
                'real_name': student.real_name,
                'score': round(total_score, 2),
                'max_score': round(max_score, 2)
            },
            'answers': answer_list
        })

    except Exception as e:
        current_app.logger.error(f'获取学生答题详情失败: {str(e)}')
        return error_response(
            '获取学生答题详情失败', code=500, http_status=500
        )
