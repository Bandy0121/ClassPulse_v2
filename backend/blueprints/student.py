"""
学生端蓝图 - 处理学生相关的所有操作
===================================

本蓝图提供以下接口：
- 班级操作：加入班级、退出班级、查询班级
- 测试操作：查看测试、提交答案、查看结果
- 签到操作：课堂签到
- 历史记录：查询测试历史

使用方式：
    from blueprints.student import student_bp
    app.register_blueprint(student_bp, url_prefix='/api/student')

API 前缀：/api/student
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity

# 导入扩展和模型
from extensions import db
from models.user import Student, Teacher
from models.class_model import Class, ClassStudent
from models.assessment import Assessment, Question, Answer
from models.checkin import Checkin, calculate_distance

# 导入工具函数
from utils.auth import get_current_user
from utils.datetime_display import (
    format_stored_utc_as_local,
    local_date_to_utc_naive_range,
    local_today,
)
from utils.response import success_response, error_response

# 创建蓝图（url 前缀仅在 app.register_blueprint 中指定）
student_bp = Blueprint('student', __name__)


# ==================== 班级操作接口 ====================

@student_bp.route('/classes', methods=['GET'])
@jwt_required()
def get_student_classes():
    """
    获取学生加入的所有班级

    请求方式：GET
    请求路径：/api/student/classes

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "success",
        "data": {
            "classes": [
                {
                    "id": 1,
                    "name": "2023级计算机科学1班",
                    "class_code": "ABCD1234",
                    "description": "必修课程",
                    "teacher": {
                        "id": 1,
                        "real_name": "张老师",
                        "username": "teacher123"
                    },
                    "created_at": "2024-01-15 10:00:00"
                }
            ]
        }
    }
    """
    try:
        # 1. 获取当前学生
        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        # 2. 获取学生加入的班级
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
    """
    学生加入班级

    请求方式：POST
    请求路径：/api/student/classes/join

    请求头：
    Authorization: Bearer <JWT Token>

    请求体（JSON）：
    {
        "class_code": "ABCD1234"  // 班级邀请码（必填）
    }

    响应格式：
    {
        "code": 200,
        "message": "成功加入班级",
        "data": {
            "id": 1,
            "name": "2023级计算机科学1班",
            "class_code": "ABCD1234"
        }
    }

    错误响应：
    - 400: 班级不存在或已加入
    - 404: 班级不存在
    """
    try:
        # 1. 获取请求数据
        data = request.get_json()

        if not data:
            return error_response('请求体不能为空', 400)

        # 2. 提取班级码
        class_code = data.get('class_code', '').strip()

        if not class_code:
            return error_response('班级码不能为空', 400)

        # 3. 查找班级
        class_obj = Class.query.filter_by(class_code=class_code).first()

        if not class_obj:
            return error_response('班级不存在', 404)

        # 4. 获取当前学生
        student = get_current_user()

        # 5. 检查是否已加入班级
        existing = ClassStudent.query.filter_by(
            class_id=class_obj.id,
            student_id=student.id,
            status=1
        ).first()

        if existing:
            return error_response('您已经加入该班级', 400)

        # 6. 加入班级
        class_student = ClassStudent(
            class_id=class_obj.id,
            student_id=student.id,
            status=1
        )

        db.session.add(class_student)
        db.session.commit()

        # 7. 返回成功响应
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
    """
    学生退出班级

    请求方式：DELETE
    请求路径：/api/student/classes/<class_id>

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "已退出班级",
        "data": null
    }
    """
    try:
        # 1. 获取当前学生
        student = get_current_user()

        # 2. 检查班级是否存在且学生已加入
        class_student = ClassStudent.query.filter_by(
            class_id=class_id,
            student_id=student.id
        ).first()

        if not class_student:
            return error_response('您未加入该班级', 400)

        # 3. 更新状态为已退出
        class_student.status = 0
        db.session.commit()

        return success_response(None, '已退出班级')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'退出班级失败: {str(e)}')
        return error_response('退出班级失败', 500)


# ==================== 测试操作接口 ====================

@student_bp.route('/assessments', methods=['GET'])
@jwt_required()
def get_available_assessments():
    """
    获取学生可以参与的测试列表

    包括：
    - 未开始的测试（显示倒计时）
    - 进行中的测试
    - 已完成的测试（显示成绩）

    请求方式：GET
    请求路径：/api/student/assessments

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "success",
        "data": {
            "available": [      // 可参与的测试
                {
                    "id": 1,
                    "title": "第一单元测试",
                    "class_name": "2023级计算机科学1班",
                    "start_time": "2024-01-15 10:00:00",
                    "end_time": "2024-01-15 11:00:00",
                    "time_remaining": 3600,  // 剩余时间（秒）
                    "question_count": 10
                }
            ],
            "completed": [      // 已完成的测试
                {
                    "id": 2,
                    "title": "随堂小测",
                    "class_name": "2023级计算机科学1班",
                    "score": 90,
                    "max_score": 100
                }
            ]
        }
    }
    """
    try:
        # 1. 获取当前学生
        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        # 2. 获取学生加入的班级
        student_classes = ClassStudent.query.filter_by(
            student_id=student.id,
            status=1
        ).all()

        class_ids = [cs.class_id for cs in student_classes]

        if not class_ids:
            return success_response({'available': [], 'completed': []})

        # 3. 获取所有测试
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

        # 4. 获取已完成测试的成绩
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
    """
    获取测试详细信息和题目

    请求方式：GET
    请求路径：/api/student/assessments/<assessment_id>

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "success",
        "data": {
            "assessment": {
                "id": 1,
                "title": "第一单元测试",
                "description": "第一单元内容测试",
                "start_time": "2024-01-15 10:00:00",
                "end_time": "2024-01-15 11:00:00",
                "max_attempts": 1,
                "show_correct_after_submit": true
            },
            "questions": [
                {
                    "id": 1,
                    "question_type": 1,
                    "content": "1+1等于几？",
                    "options": {
                        "A": "1",
                        "B": "2",
                        "C": "3",
                        "D": "4"
                    },
                    "score": 10
                }
            ]
        }
    }
    """
    try:
        # 1. 获取当前学生
        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        # 2. 获取测试
        assessment = Assessment.query.get(assessment_id)

        if not assessment:
            return error_response('测试不存在', 404)

        # 3. 检查学生是否在班级中
        class_student = ClassStudent.query.filter_by(
            class_id=assessment.class_id,
            student_id=student.id,
            status=1
        ).first()

        if not class_student:
            return error_response('您未加入该班级', 403)

        # 4. 检查测试是否已发布
        if not assessment.is_published:
            return error_response('测试尚未发布', 403)

        # 5. 检查测试时间
        now = datetime.utcnow()
        if now < assessment.start_time:
            return error_response('测试尚未开始', 403)

        if now > assessment.end_time:
            return error_response('测试已结束', 403)

        # 6. 获取题目列表
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
    """
    提交测试答案

    请求方式：POST
    请求路径：/api/student/assessments/<assessment_id>/submit

    请求头：
    Authorization: Bearer <JWT Token>

    请求体（JSON）：
    {
        "answers": [
            {
                "question_id": 1,
                "selected_option": "B",
                "response_time": 15  // 答题耗时（秒，可选）
            },
            {
                "question_id": 2,
                "selected_option": "A,C",
                "response_time": 30
            }
        ]
    }

    响应格式：
    {
        "code": 200,
        "message": "提交成功",
        "data": {
            "total": 10,
            "correct": 9,
            "score": 90.0,
            "show_correct_after_submit": true
        }
    }
    """
    try:
        # 1. 获取请求数据
        data = request.get_json()

        if not data:
            return error_response('请求体不能为空', 400)

        answers = data.get('answers', [])

        if not answers:
            return error_response('Answers field is required', 400)

        # 2. 获取当前学生
        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        # 3. 获取测试
        assessment = Assessment.query.get(assessment_id)

        if not assessment:
            return error_response('测试不存在', 404)

        # 4. 检查学生是否在班级中
        class_student = ClassStudent.query.filter_by(
            class_id=assessment.class_id,
            student_id=student.id,
            status=1
        ).first()

        if not class_student:
            return error_response('您未加入该班级', 403)

        # 5. 检查测试时间
        now = datetime.utcnow()
        if now > assessment.end_time:
            return error_response('测试已结束', 403)

        # 6. 检查尝试次数
        attempt_count = Answer.query.filter_by(
            assessment_id=assessment_id,
            student_id=student.id
        ).count()

        if attempt_count >= assessment.max_attempts:
            return error_response(f'已达到最大尝试次数（{assessment.max_attempts}次）', 403)

        # 7. 提交答案
        result = Answer.submit_assessment(
            assessment_id=assessment_id,
            student_id=student.id,
            answers=answers
        )

        # 8. 返回结果
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
    """
    获取测试结果

    请求方式：GET
    请求路径：/api/student/assessments/<assessment_id>/result

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "success",
        "data": {
            "assessment": {
                "id": 1,
                "title": "第一单元测试"
            },
            "score": 90,
            "max_score": 100,
            "correct_count": 9,
            "wrong_count": 1,
            "submitted_at": "2024-01-15 10:30:00",
            "show_correct_after_submit": true,
            "answers": [
                {
                    "question_id": 1,
                    "content": "1+1等于几？",
                    "selected_option": "B",
                    "correct_answer": "B",
                    "is_correct": true,
                    "score": 10
                }
            ]
        }
    }
    """
    try:
        # 1. 获取当前学生
        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        # 2. 获取测试
        assessment = Assessment.query.get(assessment_id)

        if not assessment:
            return error_response('测试不存在', 404)

        # 3. 获取学生的答题记录
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

        # 4. 计算总分
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

        # 5. 计算满分
        max_score = sum(float(q.score) for q in assessment.questions.all())

        # 6. 获取提交时间（最后一次提交）
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


# ==================== 签到接口 ====================

@student_bp.route('/checkin', methods=['POST'])
@jwt_required()
def checkin():
    """
    学生课堂签到

    请求方式：POST
    请求路径：/api/student/checkin

    请求头：
    Authorization: Bearer <JWT Token>

    请求体（JSON）：
    {
        "class_id": 1,                    // 班级ID（必填）
        "latitude": 39.9042,              // 纬度（可选）
        "longitude": 116.4074,            // 经度（可选）
        "ip_address": "192.168.1.100"     // IP地址（可选）
    }

    响应格式：
    {
        "code": 200,
        "message": "签到成功",
        "data": {
            "id": 1,
            "class_id": 1,
            "timestamp": "2024-01-15 10:00:00"
        }
    }
    """
    try:
        # 1. 获取请求数据
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

        # 2. 获取当前学生
        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        # 3. 检查学生是否在班级中
        class_student = ClassStudent.query.filter_by(
            class_id=class_id,
            student_id=student.id,
            status=1
        ).first()

        if not class_student:
            return error_response('您未加入该班级', 403)

        # 4. 同一班级、每个自然日（东八区）仅允许签到一次；当天可在其他班级分别签到
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

        # 5. 提取参数
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        ip_address = data.get('ip_address')

        # 6. 生成位置哈希（若提供了坐标）
        location_hash = None
        if latitude and longitude:
            # 简单的哈希算法：保留两位小数
            location_hash = f"{round(float(latitude), 2)},{round(float(longitude), 2)}"

        # 7. 写入签到
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

        # 8. 返回成功响应
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
    """
    获取签到历史记录

    请求方式：GET
    请求路径：/api/student/checkin/history

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "success",
        "data": {
            "checkins": [
                {
                    "id": 1,
                    "class_id": 1,
                    "class_name": "2023级计算机科学1班",
                    "timestamp": "2024-01-15 10:00:00",
                    "location_hash": "39.90,116.40"
                }
            ]
        }
    }
    """
    try:
        # 1. 获取当前学生
        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        # 2. 获取签到记录
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


# ==================== 历史记录接口 ====================

@student_bp.route('/history', methods=['GET'])
@jwt_required()
def get_student_history():
    """
    获取学生的所有测试历史

    请求方式：GET
    请求路径：/api/student/history

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "success",
        "data": {
            "history": [
                {
                    "assessment_id": 1,
                    "title": "第一单元测试",
                    "class_name": "2023级计算机科学1班",
                    "score": 90,
                    "max_score": 100,
                    "correct_count": 9,
                    "wrong_count": 1,
                    "submitted_at": "2024-01-15 10:30:00"
                }
            ]
        }
    }
    """
    try:
        # 1. 获取当前学生
        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        # 2. 获取学生的答题记录
        answers = Answer.query.filter_by(student_id=student.id).distinct().all()

        # 3. 收集测试ID
        assessment_ids = list(set(ans.assessment_id for ans in answers))

        # 4. 获取测试详情
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
