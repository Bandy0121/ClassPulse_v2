"""
教师端蓝图 - 处理教师相关的所有操作
===================================

本蓝图提供以下接口：
- 班级管理：创建、查询、更新、删除班级
- 测试管理：创建、发布、查询测试
- 数据统计：查看测试统计、学生成绩

使用方式：
    from blueprints.teacher import teacher_bp
    app.register_blueprint(teacher_bp, url_prefix='/api/teacher')

API 前缀：/api/teacher
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from flask_jwt_extended import jwt_required, get_jwt_identity

# 导入扩展和模型
from extensions import db
from models.user import Teacher, Student
from models.class_model import Class, ClassStudent, generate_class_code
from models.assessment import Assessment, Question, Answer
from models.checkin import Checkin

# 导入工具函数
from utils.auth import get_current_user
from utils.datetime_display import (
    format_stored_utc_as_local,
    parse_client_datetime_to_utc_naive,
)
from utils.response import success_response, error_response

# 创建蓝图（url 前缀仅在 app.register_blueprint 中指定，避免与注册前缀重复拼接）
teacher_bp = Blueprint('teacher', __name__)


def _require_teacher():
    """
    解析当前登录用户为教师。

    Returns:
        (Teacher, None) 成功；(None, error_response 元组) 失败。
    """
    user = get_current_user()
    if user is None:
        return None, error_response(
            '请先登录或登录已失效', code=401, http_status=401
        )
    if not isinstance(user, Teacher):
        return None, error_response('需要教师账号', code=403, http_status=403)
    return user, None


# ==================== 班级管理接口 ====================

@teacher_bp.route('/classes', methods=['GET'])
@jwt_required()
def get_teacher_classes():
    """
    获取教师的所有班级

    请求方式：GET
    请求路径：/api/teacher/classes

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
                    "description": "这是2023级计算机科学专业的必修课程",
                    "student_count": 30,
                    "created_at": "2024-01-15 10:00:00"
                }
            ]
        }
    }
    """
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        # 2. 获取教师的所有班级
        classes = Class.query.filter_by(teacher_id=teacher.id).all()

        # 3. 转换为字典列表
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
    """
    创建新班级

    请求方式：POST
    请求路径：/api/teacher/classes

    请求头：
    Authorization: Bearer <JWT Token>

    请求体（JSON）：
    {
        "name": "2023级计算机科学1班",    // 班级名称（必填）
        "description": "必修课程"        // 班级描述（可选）
    }

    响应格式：
    {
        "code": 201,
        "message": "班级创建成功",
        "data": {
            "id": 1,
            "name": "2023级计算机科学1班",
            "class_code": "ABCD1234",
            "description": "必修课程",
            "created_at": "2024-01-15 10:00:00"
        }
    }
    """
    try:
        # 1. 获取请求数据
        data = request.get_json()

        if not data:
            return error_response('请求体不能为空', 400)

        # 2. 提取和验证字段
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()

        if not name:
            return error_response('班级名称不能为空', 400)

        teacher, err = _require_teacher()
        if err:
            return err

        # 4. 生成班级邀请码
        class_code = generate_class_code()

        # 5. 创建班级
        new_class = Class(
            name=name,
            class_code=class_code,
            description=description,
            teacher_id=teacher.id
        )

        db.session.add(new_class)
        db.session.commit()

        # 6. 返回成功响应
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
    """
    获取班级详细信息

    请求方式：GET
    请求路径：/api/teacher/classes/<class_id>

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "success",
        "data": {
            "class_info": {
                "id": 1,
                "name": "2023级计算机科学1班",
                "class_code": "ABCD1234",
                "description": "必修课程",
                "student_count": 30,
                "assessment_count": 5
            },
            "students": [
                {
                    "id": 1,
                    "username": "student1",
                    "real_name": "张三",
                    "student_id": "2023001234",
                    "joined_at": "2024-01-15 10:00:00"
                }
            ],
            "assessments": [
                {
                    "id": 1,
                    "title": "第一单元测试",
                    "start_time": "2024-01-15 10:00:00",
                    "end_time": "2024-01-15 11:00:00",
                    "is_published": true,
                    "question_count": 10
                }
            ]
        }
    }
    """
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        # 2. 验证班级所有权
        class_obj = Class.query.filter_by(
            id=class_id,
            teacher_id=teacher.id
        ).first()

        if not class_obj:
            return error_response('班级不存在或无权限访问', 404)

        # 3. 获取班级信息
        class_info = class_obj.to_dict()
        class_info['student_count'] = class_obj.get_student_count()
        class_info['assessment_count'] = class_obj.get_assessment_count()

        # 4. 获取学生列表
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

        # 5. 获取测试列表
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


@teacher_bp.route('/classes/<int:class_id>/checkins', methods=['GET'])
@jwt_required()
def get_class_checkins_list(class_id: int):
    """获取班级签到记录列表（教师）。"""
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

        rows = Checkin.query.filter_by(
            class_id=class_id,
            status=1
        ).order_by(Checkin.timestamp.desc()).all()

        out = []
        for c in rows:
            st = Student.query.get(c.student_id)
            out.append({
                'id': c.id,
                'student_id': c.student_id,
                'real_name': st.real_name if st else '',
                'username': st.username if st else '',
                'student_no': st.student_id if st else '',
                'timestamp': format_stored_utc_as_local(c.timestamp),
                'location_hash': c.location_hash,
                'ip_address': c.ip_address
            })

        return success_response({'checkins': out})
    except Exception as e:
        current_app.logger.error(f'获取签到记录失败: {str(e)}')
        return error_response(
            '获取签到记录失败', code=500, http_status=500
        )


@teacher_bp.route('/classes/<int:class_id>', methods=['PUT'])
@jwt_required()
def update_class(class_id):
    """
    更新班级信息

    请求方式：PUT
    请求路径：/api/teacher/classes/<class_id>

    请求头：
    Authorization: Bearer <JWT Token>

    请求体（JSON）：
    {
        "name": "2023级计算机科学2班",    // 新班级名称（必填）
        "description": "选修课程"         // 新描述（可选）
    }

    响应格式：
    {
        "code": 200,
        "message": "班级更新成功",
        "data": {
            "id": 1,
            "name": "2023级计算机科学2班",
            "description": "选修课程"
        }
    }
    """
    try:
        # 1. 获取请求数据
        data = request.get_json()

        if not data:
            return error_response('请求体不能为空', 400)

        teacher, err = _require_teacher()
        if err:
            return err
        class_obj = Class.query.filter_by(
            id=class_id,
            teacher_id=teacher.id
        ).first()

        if not class_obj:
            return error_response('班级不存在或无权限访问', 404)

        # 3. 更新字段
        if 'name' in data:
            class_obj.name = data['name'].strip()
        if 'description' in data:
            class_obj.description = data['description'].strip()

        db.session.commit()

        # 4. 返回成功响应
        return success_response(
            data=class_obj.to_dict(),
            message='班级更新成功'
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'更新班级失败: {str(e)}')
        return error_response('更新班级失败', code=500, http_status=500)


@teacher_bp.route('/classes/<int:class_id>', methods=['DELETE'])
@jwt_required()
def delete_class(class_id):
    """
    删除班级

    注意：删除班级时，相关的测试和学生关联也会被级联删除。

    请求方式：DELETE
    请求路径：/api/teacher/classes/<class_id>

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "班级已删除",
        "data": null
    }
    """
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

        # 2. 删除班级
        db.session.delete(class_obj)
        db.session.commit()

        return success_response(None, '班级已删除')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除班级失败: {str(e)}')
        return error_response('删除班级失败', code=500, http_status=500)


# ==================== 测试管理接口 ====================

@teacher_bp.route('/classes/<int:class_id>/assessments', methods=['GET'])
@jwt_required()
def get_class_assessments(class_id):
    """
    获取班级的所有测试

    请求方式：GET
    请求路径：/api/teacher/classes/<class_id>/assessments

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "success",
        "data": {
            "assessments": [
                {
                    "id": 1,
                    "title": "第一单元测试",
                    "description": "第一单元内容测试",
                    "start_time": "2024-01-15 10:00:00",
                    "end_time": "2024-01-15 11:00:00",
                    "duration_minutes": 30,
                    "max_attempts": 1,
                    "is_published": true,
                    "question_count": 10,
                    "created_at": "2024-01-14 15:00:00"
                }
            ]
        }
    }
    """
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        # 2. 验证班级所有权
        class_obj = Class.query.filter_by(
            id=class_id,
            teacher_id=teacher.id
        ).first()

        if not class_obj:
            return error_response('班级不存在或无权限访问', 404)

        # 3. 获取测试列表
        assessments = class_obj.assessments.all()

        assessment_list = []
        for assessment in assessments:
            assessment_list.append(assessment.to_dict())
            assessment_list[-1]['question_count'] = assessment.get_question_count()

        return success_response({'assessments': assessment_list})

    except Exception as e:
        current_app.logger.error(f'获取测试列表失败: {str(e)}')
        return error_response(
            '获取测试列表失败', code=500, http_status=500
        )


@teacher_bp.route('/classes/<int:class_id>/assessments', methods=['POST'])
@jwt_required()
def create_assessment(class_id):
    """
    创建新测试

    请求方式：POST
    请求路径：/api/teacher/classes/<class_id>/assessments

    请求头：
    Authorization: Bearer <JWT Token>

    请求体（JSON）：
    {
        "title": "第一单元测试",            // 测试标题（必填）
        "description": "第一单元内容测试",  // 测试描述（可选）
        "start_time": "2024-01-15 10:00", // 开始时间（必填，ISO 8601 或 YYYY-MM-DD HH:mm:ss）
        "duration_minutes": 30,           // 考试时长/分钟（未传 end_time 时必填，至少 1）
        "end_time": "2024-01-15 11:00",   // 结束时间（可选；不传则按开始时间 + duration_minutes 计算）
        "max_attempts": 1,                // 最大尝试次数（可选，默认 1）
        "show_correct_after_submit": true // 提交后显示答案（可选，默认 true）
    }

    响应格式：
    {
        "code": 201,
        "message": "测试创建成功",
        "data": {
            "id": 1,
            "title": "第一单元测试",
            "is_published": false,
            "created_at": "2024-01-14 15:00:00"
        }
    }
    """
    try:
        # 1. 获取请求数据
        data = request.get_json()

        if not data:
            return error_response('请求体不能为空', 400)

        teacher, err = _require_teacher()
        if err:
            return err
        class_obj = Class.query.filter_by(
            id=class_id,
            teacher_id=teacher.id
        ).first()

        if not class_obj:
            return error_response('班级不存在或无权限访问', 404)

        # 3. 提取和验证字段
        title = data.get('title', '').strip()

        if not title:
            return error_response('测试标题不能为空', 400)

        try:
            duration_minutes = int(data.get('duration_minutes', 5))
        except (TypeError, ValueError):
            return error_response('考试时长须为正整数（分钟）', 400)
        if duration_minutes < 1:
            return error_response('考试时长至少为 1 分钟', 400)

        try:
            start_time = parse_client_datetime_to_utc_naive(data.get('start_time'))
        except ValueError:
            return error_response('开始时间格式不正确', 400)

        end_raw = data.get('end_time')
        if end_raw:
            try:
                end_time = parse_client_datetime_to_utc_naive(end_raw)
            except ValueError:
                return error_response('结束时间格式不正确', 400)
            if end_time <= start_time:
                return error_response('结束时间必须晚于开始时间', 400)
        else:
            end_time = start_time + timedelta(minutes=duration_minutes)

        # 4. 创建测试
        assessment = Assessment(
            class_id=class_id,
            title=title,
            description=data.get('description', '').strip(),
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            max_attempts=data.get('max_attempts', 1),
            show_correct_after_submit=data.get('show_correct_after_submit', True),
            is_published=False  # 新创建的测试默认为草稿状态
        )

        db.session.add(assessment)
        db.session.commit()

        # 5. 返回成功响应
        return success_response(
            data={
                'id': assessment.id,
                'title': assessment.title,
                'is_published': False,
                'created_at': format_stored_utc_as_local(assessment.created_at),
            },
            message='测试创建成功',
            code=201
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'创建测试失败: {str(e)}')
        return error_response('创建测试失败', code=500, http_status=500)


@teacher_bp.route('/assessments/<int:assessment_id>/questions', methods=['POST'])
@jwt_required()
def add_question(assessment_id):
    """
    添加题目到测试

    请求方式：POST
    请求路径：/api/teacher/assessments/<assessment_id>/questions

    请求头：
    Authorization: Bearer <JWT Token>

    请求体（JSON）：
    {
        "question_type": 1,           // 题型：1-单选，2-多选（必填）
        "content": "1+1等于几？",      // 题目内容（必填）
        "option_a": "1",              // 选项A（必填）
        "option_b": "2",              // 选项B（必填）
        "option_c": "3",              // 选项C（可选）
        "option_d": "4",              // 选项D（可选）
        "correct_answer": "B",        // 正确答案（必填）
        "score": 10.0                 // 分值（可选，默认 10）
    }

    响应格式：
    {
        "code": 201,
        "message": "题目添加成功",
        "data": {
            "id": 1,
            "assessment_id": 1,
            "question_type": 1,
            "content": "1+1等于几？",
            "correct_answer": "B",
            "score": 10.0
        }
    }
    """
    try:
        # 1. 获取请求数据
        data = request.get_json()

        if not data:
            return error_response('请求体不能为空', 400)

        teacher, err = _require_teacher()
        if err:
            return err

        # 3. 验证测试所有权
        assessment = (
            Assessment.query.filter(Assessment.id == assessment_id)
            .join(Class, Class.id == Assessment.class_id)
            .filter(Class.teacher_id == teacher.id)
            .first()
        )

        if not assessment:
            return error_response('测试不存在或无权限访问', 404)

        # 4. 提取和验证字段
        content = data.get('content', '').strip()
        if not content:
            return error_response('题目内容不能为空', 400)

        correct_answer = data.get('correct_answer', '').strip().upper()
        if not correct_answer:
            return error_response('正确答案不能为空', 400)

        # 5. 创建题目
        question = Question(
            assessment_id=assessment_id,
            question_type=data.get('question_type', 1),
            content=content,
            option_a=data.get('option_a', '').strip(),
            option_b=data.get('option_b', '').strip(),
            option_c=data.get('option_c', '').strip(),
            option_d=data.get('option_d', '').strip(),
            correct_answer=correct_answer,
            score=data.get('score', 10.0)
        )

        db.session.add(question)
        db.session.commit()

        # 6. 返回成功响应
        return success_response(
            data=question.to_dict(),
            message='题目添加成功',
            code=201
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'添加题目失败: {str(e)}')
        return error_response('添加题目失败', code=500, http_status=500)


@teacher_bp.route('/assessments/<int:assessment_id>/publish', methods=['PUT'])
@jwt_required()
def publish_assessment(assessment_id):
    """
    发布或取消发布测试

    请求方式：PUT
    请求路径：/api/teacher/assessments/<assessment_id>/publish

    请求头：
    Authorization: Bearer <JWT Token>

    请求体（JSON）：
    {
        "publish": true  // true-发布，false-取消发布
    }

    响应格式：
    {
        "code": 200,
        "message": "测试已发布",
        "data": {
            "id": 1,
            "title": "第一单元测试",
            "is_published": true
        }
    }
    """
    try:
        # 1. 获取请求数据
        data = request.get_json()

        if not data:
            return error_response('请求体不能为空', 400)

        teacher, err = _require_teacher()
        if err:
            return err

        # 3. 验证测试所有权
        assessment = (
            Assessment.query.filter(Assessment.id == assessment_id)
            .join(Class, Class.id == Assessment.class_id)
            .filter(Class.teacher_id == teacher.id)
            .first()
        )

        if not assessment:
            return error_response('测试不存在或无权限访问', 404)

        # 4. 获取发布状态
        publish = data.get('publish', True)

        # 5. 更新发布状态
        assessment.is_published = publish
        db.session.commit()

        # 6. 返回成功响应
        return success_response(
            data={
                'id': assessment.id,
                'title': assessment.title,
                'is_published': assessment.is_published
            },
            message='测试已发布' if publish else '测试已取消发布'
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'发布测试失败: {str(e)}')
        return error_response('发布测试失败', code=500, http_status=500)


@teacher_bp.route('/assessments/<int:assessment_id>', methods=['DELETE'])
@jwt_required()
def delete_assessment(assessment_id):
    """
    删除测试

    注意：删除测试会同时删除所有题目和学生答案。

    请求方式：DELETE
    请求路径：/api/teacher/assessments/<assessment_id>

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "测试已删除",
        "data": null
    }
    """
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        # 2. 验证测试所有权
        assessment = (
            Assessment.query.filter(Assessment.id == assessment_id)
            .join(Class, Class.id == Assessment.class_id)
            .filter(Class.teacher_id == teacher.id)
            .first()
        )

        if not assessment:
            return error_response('测试不存在或无权限访问', 404)

        # 3. 删除测试
        db.session.delete(assessment)
        db.session.commit()

        return success_response(None, '测试已删除')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除测试失败: {str(e)}')
        return error_response('删除测试失败', code=500, http_status=500)


# ==================== 数据统计接口 ====================

@teacher_bp.route('/assessments/<int:assessment_id>/statistics', methods=['GET'])
@jwt_required()
def get_assessment_statistics(assessment_id):
    """
    获取测试统计信息

    包含：
    - 每道题的正确率
    - 学生总体表现

    请求方式：GET
    请求路径：/api/teacher/assessments/<assessment_id>/statistics

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "success",
        "data": {
            "assessment_info": {
                "id": 1,
                "title": "第一单元测试",
                "total_students": 30,
                "submitted_students": 28
            },
            "question_statistics": [
                {
                    "question_id": 1,
                    "content": "1+1等于几？",
                    "total_attempts": 28,
                    "correct_count": 25,
                    "correct_rate": 89.29
                }
            ],
            "student_summary": [
                {
                    "student_id": 1,
                    "username": "student1",
                    "real_name": "张三",
                    "score": 90,
                    "max_score": 100,
                    "correct_count": 9,
                    "wrong_count": 1
                }
            ]
        }
    }
    """
    try:
        teacher, err = _require_teacher()
        if err:
            return err

        # 2. 验证测试所有权
        assessment = (
            Assessment.query.filter(Assessment.id == assessment_id)
            .join(Class, Class.id == Assessment.class_id)
            .filter(Class.teacher_id == teacher.id)
            .first()
        )

        if not assessment:
            return error_response('测试不存在或无权限访问', 404)

        # 3. 获取测试基本信息
        assessment_info = {
            'id': assessment.id,
            'title': assessment.title,
            'total_students': assessment.get_student_count()
        }

        # 4. 获取题目统计
        # 查询每个题目的答题情况
        question_stats = db.session.query(
            Question.id.label('question_id'),
            Question.content,
            Question.score,
            db.func.count(Answer.id).label('total_attempts'),
            db.func.sum(db.case((Answer.is_correct == True, 1), else_=0)).label('correct_count')
        ).outerjoin(
            Answer, Answer.question_id == Question.id
        ).filter(
            Question.assessment_id == assessment_id
        ).group_by(Question.id).all()

        question_statistics = []
        for qs in question_stats:
            total = qs.total_attempts if qs.total_attempts else 0
            correct = qs.correct_count if qs.correct_count else 0
            correct_rate = round((correct / total * 100) if total > 0 else 0, 2)

            question_statistics.append({
                'question_id': qs.question_id,
                'content': qs.content,
                'total_attempts': total,
                'correct_count': correct,
                'correct_rate': correct_rate,
                'score': float(qs.score)
            })

        # 5. 获取学生表现（得分在 Question.score，不在 Answer 表）
        student_agg = db.session.query(
            Student.id.label('student_id'),
            Student.username,
            Student.real_name,
            db.func.sum(
                db.case((Answer.is_correct == True, Question.score), else_=0)
            ).label('score'),
            db.func.sum(
                db.case((Answer.is_correct == True, 1), else_=0)
            ).label('correct_count'),
            db.func.count(Answer.id).label('answered_count')
        ).join(
            Answer, Answer.student_id == Student.id
        ).join(
            Question, Question.id == Answer.question_id
        ).filter(
            Answer.assessment_id == assessment_id
        ).group_by(
            Student.id, Student.username, Student.real_name
        ).all()

        max_score = sum(float(q.score) for q in assessment.questions.all())

        student_summary = []
        for sp in student_agg:
            answered = int(sp.answered_count or 0)
            correct = int(sp.correct_count or 0)
            wrong_count = answered - correct
            student_summary.append({
                'student_id': sp.student_id,
                'username': sp.username,
                'real_name': sp.real_name,
                'score': round(float(sp.score or 0), 2),
                'max_score': round(max_score, 2),
                'correct_count': correct,
                'wrong_count': wrong_count
            })

        return success_response({
            'assessment_info': assessment_info,
            'question_statistics': question_statistics,
            'student_summary': student_summary
        })

    except Exception as e:
        current_app.logger.error(f'获取统计信息失败: {str(e)}')
        return error_response(
            '获取统计信息失败',
            code=500,
            http_status=500
        )


@teacher_bp.route('/assessments/<int:assessment_id>/student/<int:student_id>/detail', methods=['GET'])
@jwt_required()
def get_student_answer_detail(assessment_id, student_id):
    """
    获取特定学生在指定测试中的详细答题情况

    包含：
    - 每道题的答题情况（是否正确、选择的答案、正确答案）

    请求方式：GET
    请求路径：/api/teacher/assessments/<assessment_id>/student/<student_id>/detail

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "success",
        "data": {
            "student_info": {
                "id": 1,
                "username": "student1",
                "real_name": "张三",
                "score": 90,
                "max_score": 100
            },
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
        teacher, err = _require_teacher()
        if err:
            return err

        # 2. 验证测试所有权
        assessment = (
            Assessment.query.filter(Assessment.id == assessment_id)
            .join(Class, Class.id == Assessment.class_id)
            .filter(Class.teacher_id == teacher.id)
            .first()
        )

        if not assessment:
            return error_response('测试不存在或无权限访问', 404)

        # 3. 获取学生信息
        student = Student.query.get(student_id)

        if not student:
            return error_response('学生不存在', 404)

        # 4. 获取学生的答题详情
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

        # 计算总分
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

        # 查询满分
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
