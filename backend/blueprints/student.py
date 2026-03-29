from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models.user import Student, Teacher
from models.class_model import Class, ClassStudent
from models.assessment import Assessment, Question, Answer
from models.checkin import Checkin, calculate_distance

from utils.auth import get_current_user
from utils.datetime_display import (
    format_stored_utc_as_local,
    local_date_to_utc_naive_range,
    local_today,
)
from utils.response import success_response, error_response

student_bp = Blueprint('student', __name__)



@student_bp.route('/classes', methods=['GET'])
@jwt_required()
def get_student_classes():
    try:
        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        # 注意：需要通过 ClassStudent 关联表查询
        class_students = ClassStudent.query.filter_by(
            student_id=student.id,
            status=1
        ).all()

        class_list = []
        for cs in class_students:
            class_obj = Class.query.get(cs.class_id)
            if class_obj:
                teacher = Teacher.query.get(class_obj.teacher_id)
                class_list.append({
                    'id': class_obj.id,
                    'name': class_obj.name,
                    'class_code': class_obj.class_code,
                    'description': class_obj.description or '',
                    'teacher': {
                        'id': teacher.id,
                        'real_name': teacher.real_name,
                        'username': teacher.username
                    } if teacher else None,
                    'created_at': format_stored_utc_as_local(class_obj.created_at),
                })

        return success_response({'classes': class_list})

    except Exception as e:
        current_app.logger.error(f'获取班级列表失败: {str(e)}')
        return error_response('获取班级列表失败', 500)


@student_bp.route('/classes/join', methods=['POST'])
@jwt_required()
def join_class():
    try:
        data = request.get_json()

        if not data:
            return error_response('请求体不能为空', 400)

        class_code = data.get('class_code', '').strip()

        if not class_code:
            return error_response('班级码不能为空', 400)

        class_obj = Class.query.filter_by(class_code=class_code).first()

        if not class_obj:
            return error_response('班级不存在', 404)

        student = get_current_user()

        existing = ClassStudent.query.filter_by(
            class_id=class_obj.id,
            student_id=student.id,
            status=1
        ).first()

        if existing:
            return error_response('您已经加入该班级', 400)

        class_student = ClassStudent(
            class_id=class_obj.id,
            student_id=student.id,
            status=1
        )

        db.session.add(class_student)
        db.session.commit()

        return success_response(
            data={
                'id': class_obj.id,
                'name': class_obj.name,
                'class_code': class_obj.class_code
            },
            message='成功加入班级'
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'加入班级失败: {str(e)}')
        return error_response('加入班级失败', 500)


@student_bp.route('/classes/<int:class_id>', methods=['DELETE'])
@jwt_required()
def leave_class(class_id):
    try:
        student = get_current_user()

        class_student = ClassStudent.query.filter_by(
            class_id=class_id,
            student_id=student.id
        ).first()

        if not class_student:
            return error_response('您未加入该班级', 400)

        class_student.status = 0
        db.session.commit()

        return success_response(None, '已退出班级')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'退出班级失败: {str(e)}')
        return error_response('退出班级失败', 500)



@student_bp.route('/assessments', methods=['GET'])
@jwt_required()
def get_available_assessments():
    try:
        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        student_classes = ClassStudent.query.filter_by(
            student_id=student.id,
            status=1
        ).all()

        class_ids = [cs.class_id for cs in student_classes]

        if not class_ids:
            return success_response({'available': [], 'completed': []})

        now = datetime.utcnow()
        assessments = Assessment.query.filter(
            Assessment.class_id.in_(class_ids)
        ).all()

        available = []
        completed = []

        for assessment in assessments:
            assessment_info = {
                'id': assessment.id,
                'title': assessment.title,
                'class_name': Class.query.get(assessment.class_id).name if Class.query.get(assessment.class_id) else '未知班级',
                'start_time': format_stored_utc_as_local(assessment.start_time),
                'end_time': format_stored_utc_as_local(assessment.end_time),
                'question_count': assessment.get_question_count(),
                'is_published': assessment.is_published
            }

            # 计算剩余时间
            if assessment.is_published:
                if now < assessment.start_time:
                    # 未开始
                    time_remaining = int((assessment.start_time - now).total_seconds())
                    assessment_info['time_remaining'] = max(0, time_remaining)
                    assessment_info['status'] = 'not_started'
                    available.append(assessment_info)

                elif now <= assessment.end_time:
                    # 进行中
                    time_remaining = int((assessment.end_time - now).total_seconds())
                    assessment_info['time_remaining'] = max(0, time_remaining)
                    assessment_info['status'] = 'in_progress'
                    available.append(assessment_info)

                else:
                    # 已结束
                    assessment_info['status'] = 'completed'
                    completed.append(assessment_info)
            else:
                # 未发布（草稿）
                continue

        for comp in completed:
            score_info = assessment = Assessment.query.get(comp['id'])
            if score_info:
                score = score_info.get_score(student.id)
                if score:
                    comp['score'] = score['total_score']
                    comp['max_score'] = score['max_score']

        return success_response({
            'available': available,
            'completed': completed
        })

    except Exception as e:
        current_app.logger.error(f'获取测试列表失败: {str(e)}')
        return error_response('获取测试列表失败', 500)


@student_bp.route('/assessments/<int:assessment_id>', methods=['GET'])
@jwt_required()
def get_assessment_details(assessment_id):
    try:
        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        assessment = Assessment.query.get(assessment_id)

        if not assessment:
            return error_response('测试不存在', 404)

        class_student = ClassStudent.query.filter_by(
            class_id=assessment.class_id,
            student_id=student.id,
            status=1
        ).first()

        if not class_student:
            return error_response('您未加入该班级', 403)

        if not assessment.is_published:
            return error_response('测试尚未发布', 403)

        now = datetime.utcnow()
        if now < assessment.start_time:
            return error_response('测试尚未开始', 403)

        if now > assessment.end_time:
            return error_response('测试已结束', 403)

        questions = []
        for question in assessment.questions.all():
            questions.append({
                'id': question.id,
                'question_type': question.question_type,
                'content': question.content,
                'options': question.get_options(),
                'score': float(question.score)
            })

        return success_response({
            'assessment': assessment.to_dict(),
            'questions': questions
        })

    except Exception as e:
        current_app.logger.error(f'获取测试详情失败: {str(e)}')
        return error_response('获取测试详情失败', 500)


@student_bp.route('/assessments/<int:assessment_id>/submit', methods=['POST'])
@jwt_required()
def submit_assessment(assessment_id):
    try:
        data = request.get_json()

        if not data:
            return error_response('请求体不能为空', 400)

        answers = data.get('answers', [])

        if not answers:
            return error_response('Answers field is required', 400)

        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        assessment = Assessment.query.get(assessment_id)

        if not assessment:
            return error_response('测试不存在', 404)

        class_student = ClassStudent.query.filter_by(
            class_id=assessment.class_id,
            student_id=student.id,
            status=1
        ).first()

        if not class_student:
            return error_response('您未加入该班级', 403)

        now = datetime.utcnow()
        if now > assessment.end_time:
            return error_response('测试已结束', 403)

        attempt_count = Answer.query.filter_by(
            assessment_id=assessment_id,
            student_id=student.id
        ).count()

        if attempt_count >= assessment.max_attempts:
            return error_response(f'已达到最大尝试次数（{assessment.max_attempts}次）', 403)

        result = Answer.submit_assessment(
            assessment_id=assessment_id,
            student_id=student.id,
            answers=answers
        )

        response_data = {
            'total': result['total'],
            'correct': result['correct'],
            'score': result['score']
        }

        if assessment.show_correct_after_submit:
            # 如果允许，返回正确答案
            question_details = []
            for ans in answers:
                question = Question.query.get(ans['question_id'])
                if question:
                    question_details.append({
                        'question_id': ans['question_id'],
                        'correct_answer': question.correct_answer,
                        'selected_option': ans['selected_option'],
                        'is_correct': question.is_correct(ans['selected_option'])
                    })
            response_data['question_details'] = question_details

        return success_response(
            data=response_data,
            message='提交成功'
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'提交测试失败: {str(e)}')
        return error_response('提交测试失败', 500)


@student_bp.route('/assessments/<int:assessment_id>/result', methods=['GET'])
@jwt_required()
def get_assessment_result(assessment_id):
    try:
        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        assessment = Assessment.query.get(assessment_id)

        if not assessment:
            return error_response('测试不存在', 404)

        answers = db.session.query(
            Answer,
            Question.content
        ).join(
            Question, Answer.question_id == Question.id
        ).filter(
            Answer.assessment_id == assessment_id,
            Answer.student_id == student.id
        ).all()

        if not answers:
            return error_response('您尚未提交此测试', 404)

        total_score = 0
        correct_count = 0
        answer_list = []

        for ans, content in answers:
            score = float(ans.question.score) if ans.is_correct else 0
            total_score += score
            if ans.is_correct:
                correct_count += 1

            answer_list.append({
                'question_id': ans.question_id,
                'content': content,
                'selected_option': ans.selected_option,
                'correct_answer': ans.question.correct_answer,
                'is_correct': ans.is_correct,
                'score': score
            })

        max_score = sum(float(q.score) for q in assessment.questions.all())

        submitted_at = max(ans.submitted_at for ans, _ in answers)

        return success_response({
            'assessment': {
                'id': assessment.id,
                'title': assessment.title
            },
            'score': round(total_score, 2),
            'max_score': round(max_score, 2),
            'correct_count': correct_count,
            'wrong_count': len(answers) - correct_count,
            'submitted_at': format_stored_utc_as_local(submitted_at),
            'show_correct_after_submit': assessment.show_correct_after_submit,
            'answers': answer_list
        })

    except Exception as e:
        current_app.logger.error(f'获取测试结果失败: {str(e)}')
        return error_response('获取测试结果失败', 500)



@student_bp.route('/checkin', methods=['POST'])
@jwt_required()
def checkin():
    try:
        data = request.get_json()

        if not data:
            return error_response('请求体不能为空', 400)

        class_id = data.get('class_id')

        if not class_id:
            return error_response('class_id 是必填字段', 400)

        try:
            class_id = int(class_id)
        except (TypeError, ValueError):
            return error_response('class_id 无效', 400)

        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        class_student = ClassStudent.query.filter_by(
            class_id=class_id,
            student_id=student.id,
            status=1
        ).first()

        if not class_student:
            return error_response('您未加入该班级', 403)

        today = local_today()
        day_start, day_end = local_date_to_utc_naive_range(today)
        existing_today_same_class = Checkin.query.filter(
            Checkin.student_id == student.id,
            Checkin.class_id == class_id,
            Checkin.status == 1,
            Checkin.timestamp >= day_start,
            Checkin.timestamp <= day_end,
        ).first()

        if existing_today_same_class:
            return error_response('您今日已在该班级签到，请明日再试', 400)

        latitude = data.get('latitude')
        longitude = data.get('longitude')
        ip_address = data.get('ip_address')

        location_hash = None
        if latitude and longitude:
            location_hash = f"{round(float(latitude), 2)},{round(float(longitude), 2)}"

        checkin = Checkin(
            class_id=class_id,
            student_id=student.id,
            latitude=latitude,
            longitude=longitude,
            location_hash=location_hash,
            ip_address=ip_address,
            status=1
        )

        db.session.add(checkin)
        db.session.commit()

        return success_response(
            data={
                'id': checkin.id,
                'class_id': checkin.class_id,
                'timestamp': format_stored_utc_as_local(checkin.timestamp),
            },
            message='签到成功'
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'签到失败: {str(e)}')
        return error_response('签到失败', 500)


@student_bp.route('/checkin/history', methods=['GET'])
@jwt_required()
def get_checkin_history():
    try:
        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        checkins = Checkin.query.filter_by(
            student_id=student.id,
            status=1
        ).order_by(Checkin.timestamp.desc()).all()

        checkin_list = []
        for checkin in checkins:
            class_obj = Class.query.get(checkin.class_id)
            checkin_list.append({
                'id': checkin.id,
                'class_id': checkin.class_id,
                'class_name': class_obj.name if class_obj else '未知班级',
                'timestamp': format_stored_utc_as_local(checkin.timestamp),
                'location_hash': checkin.location_hash,
                'ip_address': checkin.ip_address
            })

        return success_response({'checkins': checkin_list})

    except Exception as e:
        current_app.logger.error(f'获取签到历史失败: {str(e)}')
        return error_response('获取签到历史失败', 500)



@student_bp.route('/history', methods=['GET'])
@jwt_required()
def get_student_history():
    try:
        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        answers = Answer.query.filter_by(student_id=student.id).distinct().all()

        assessment_ids = list(set(ans.assessment_id for ans in answers))

        history = []
        for aid in assessment_ids:
            assessment = Assessment.query.get(aid)
            if assessment:
                # 获取该学生的答题情况
                student_answers = db.session.query(
                    Answer,
                    Question.score
                ).join(Question, Answer.question_id == Question.id)\
                 .filter(Answer.assessment_id == aid, Answer.student_id == student.id).all()

                total_score = sum(
                    float(q_score) for ans, q_score in student_answers if ans.is_correct
                )
                max_score = sum(float(q_score) for _, q_score in student_answers)
                correct_count = sum(1 for ans, _ in student_answers if ans.is_correct)
                submitted_at = max(ans.submitted_at for ans, _ in student_answers)

                history.append({
                    'assessment_id': aid,
                    'title': assessment.title,
                    'class_name': Class.query.get(assessment.class_id).name if Class.query.get(assessment.class_id) else '未知班级',
                    'score': round(total_score, 2),
                    'max_score': round(max_score, 2),
                    'correct_count': correct_count,
                    'wrong_count': len(student_answers) - correct_count,
                    '_submitted_at': submitted_at,
                })

        # 按提交时间排序（用 UTC naive 时刻，再格式化为东八区展示）
        history.sort(key=lambda x: x['_submitted_at'], reverse=True)
        for row in history:
            row['submitted_at'] = format_stored_utc_as_local(row.pop('_submitted_at'))

        return success_response({'history': history})

    except Exception as e:
        current_app.logger.error(f'获取历史记录失败: {str(e)}')
        return error_response('获取历史记录失败', 500)
