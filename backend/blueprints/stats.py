"""
统计蓝图 - 处理各种统计相关的操作
=================================

本蓝图提供以下接口：
- 测试统计：正确率分析、学生成绩分布
- 个人统计：学生个人学习情况分析

使用方式：
    from blueprints.stats import stats_bp
    app.register_blueprint(stats_bp, url_prefix='/api/stats')

API 前缀：/api/stats
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from flask_jwt_extended import jwt_required

# 导入扩展和模型
from extensions import db
from models.user import Teacher, Student
from models.class_model import Class, ClassStudent
from models.assessment import Assessment, Question, Answer
from models.checkin import Checkin

# 导入工具函数
from utils.auth import get_current_user
from utils.datetime_display import (
    format_stored_utc_as_local,
    local_date_to_utc_naive_range,
    local_today,
)
from utils.response import success_response, error_response

# 创建蓝图（url 前缀仅在 app.register_blueprint 中指定）
stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/student/statistics', methods=['GET'])
@jwt_required()
def get_student_statistics():
    """
    获取学生的个人统计数据

    包含：
    - 总签到次数
    - 参与的测试数量
    - 各科目的平均成绩

    请求方式：GET
    请求路径：/api/stats/student/statistics

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "success",
        "data": {
            "overview": {
                "total_checkins": 20,
                "total_assessments": 5,
                "completed_assessments": 4,
                "average_score": 85.5
            },
            "subjects": [
                {
                    "class_name": "2023级计算机科学1班",
                    "average_score": 88.0,
                    "assessment_count": 2
                }
            ],
            "weekly_activity": [
                {"date": "2024-01-15", "checkins": 1, "assessments": 1},
                {"date": "2024-01-16", "checkins": 1, "assessments": 0}
            ]
        }
    }
    """
    try:
        # 1. 获取当前学生
        student = get_current_user()

        if not student:
            return error_response('用户不存在', 404)

        # 2. 获取签到统计
        total_checkins = Checkin.query.filter_by(
            student_id=student.id,
            status=1
        ).count()

        # 3. 获取测试参与统计
        total_assessments = db.session.query(
            db.func.count(db.distinct(Answer.assessment_id))
        ).filter_by(student_id=student.id).scalar()

        completed_assessments = total_assessments

        # 4. 计算平均成绩
        answers = Answer.query.filter_by(student_id=student.id).all()
        if answers:
            total_score = sum(
                float(ans.question.score) for ans in answers if ans.is_correct
            )
            max_score = sum(float(ans.question.score) for ans in answers)
            average_score = round((total_score / max_score * 100) if max_score > 0 else 0, 1)
        else:
            average_score = 0

        # 5. 获取各班级统计
        student_classes = ClassStudent.query.filter_by(
            student_id=student.id,
            status=1
        ).all()

        subjects = []
        for cs in student_classes:
            class_obj = Class.query.get(cs.class_id)
            if class_obj:
                # 获取该班级测试的平均分
                class_answers = Answer.query.join(Assessment).filter(
                    Answer.student_id == student.id,
                    Assessment.class_id == class_obj.id
                ).all()

                if class_answers:
                    class_total = sum(float(ans.question.score) for ans in class_answers if ans.is_correct)
                    class_max = sum(float(ans.question.score) for ans in class_answers)
                    class_avg = round((class_total / class_max * 100) if class_max > 0 else 0, 1)
                else:
                    class_avg = 0

                subjects.append({
                    'class_name': class_obj.name,
                    'average_score': class_avg,
                    'assessment_count': Assessment.query.filter_by(class_id=class_obj.id).count()
                })

        # 6. 获取最近7天的活动记录（按东八区自然日聚合）
        weekly_activity = []
        for i in range(7):
            day = local_today() - timedelta(days=i)
            date_start, date_end = local_date_to_utc_naive_range(day)

            day_checkins = Checkin.query.filter(
                Checkin.student_id == student.id,
                Checkin.timestamp >= date_start,
                Checkin.timestamp <= date_end
            ).count()

            day_assessments = db.session.query(
                db.func.count(db.distinct(Answer.assessment_id))
            ).filter(
                Answer.student_id == student.id,
                Answer.submitted_at >= date_start,
                Answer.submitted_at <= date_end
            ).scalar()

            weekly_activity.append({
                'date': day.strftime('%Y-%m-%d'),
                'checkins': day_checkins,
                'assessments': day_assessments or 0
            })

        # 按日期倒序
        weekly_activity.reverse()

        return success_response({
            'overview': {
                'total_checkins': total_checkins,
                'total_assessments': total_assessments,
                'completed_assessments': completed_assessments,
                'average_score': average_score
            },
            'subjects': subjects,
            'weekly_activity': weekly_activity
        })

    except Exception as e:
        current_app.logger.error(f'获取学生统计失败: {str(e)}')
        return error_response('获取学生统计失败', 500)


@stats_bp.route('/teacher/class/<int:class_id>/statistics', methods=['GET'])
@jwt_required()
def get_class_statistics(class_id):
    """
    获取班级综合统计信息

    包含：
    - 签到统计（签到率）
    - 测试统计（平均分、及格率）
    - 学生表现分布

    请求方式：GET
    请求路径：/api/stats/teacher/class/<class_id>/statistics

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
                "student_count": 30
            },
            "checkin_stats": {
                "total": 100,
                "checked_in": 85,
                "rate": 85.0
            },
            "assessment_stats": {
                "total": 5,
                "completed": 4,
                "average_score": 82.5,
                "pass_rate": 90.0
            },
            "score_distribution": [
                {"range": "90-100", "count": 10, "percentage": 33.3},
                {"range": "80-89", "count": 12, "percentage": 40.0},
                {"range": "70-79", "count": 5, "percentage": 16.7},
                {"range": "0-69", "count": 3, "percentage": 10.0}
            ]
        }
    }
    """
    try:
        # 1. 获取当前教师
        teacher = get_current_user()

        # 2. 验证班级所有权
        class_obj = Class.query.filter_by(
            id=class_id,
            teacher_id=teacher.id
        ).first()

        if not class_obj:
            return error_response('班级不存在或无权限访问', 404)

        # 3. 班级信息
        student_count = ClassStudent.query.filter_by(
            class_id=class_id,
            status=1
        ).count()

        # 4. 签到统计
        total_checkins = Checkin.query.filter_by(
            class_id=class_id,
            status=1
        ).count()

        # 获取唯一签到学生数
        checked_in_students = db.session.query(
            db.func.count(db.distinct(Checkin.student_id))
        ).filter_by(class_id=class_id, status=1).scalar()

        checkin_rate = round((checked_in_students / student_count * 100) if student_count > 0 else 0, 1)

        # 本班今日（东八区）签到人次（同一学生同一天在同一班至多 1 次）
        today_lo, today_hi = local_date_to_utc_naive_range(local_today())
        today_checkins = Checkin.query.filter(
            Checkin.class_id == class_id,
            Checkin.status == 1,
            Checkin.timestamp >= today_lo,
            Checkin.timestamp <= today_hi,
        ).count()
        today_rate = round(
            (today_checkins / student_count * 100) if student_count > 0 else 0,
            1,
        )

        # 近 14 天（东八区）按日统计本班签到人次
        checkin_by_day = []
        for i in range(13, -1, -1):
            d = local_today() - timedelta(days=i)
            lo, hi = local_date_to_utc_naive_range(d)
            cnt = Checkin.query.filter(
                Checkin.class_id == class_id,
                Checkin.status == 1,
                Checkin.timestamp >= lo,
                Checkin.timestamp <= hi,
            ).count()
            checkin_by_day.append({'date': d.strftime('%Y-%m-%d'), 'count': cnt})

        # 5. 测试统计
        assessments = Assessment.query.filter_by(class_id=class_id).all()
        assessment_count = len(assessments)

        # 计算平均分和及格率
        all_scores = []
        for assessment in assessments:
            # 获取该测试所有学生的成绩
            student_scores = db.session.query(
                db.func.sum(db.case((Answer.is_correct == True, Question.score), else_=0))
            ).select_from(Answer).join(
                Question, Question.id == Answer.question_id
            ).filter(
                Answer.assessment_id == assessment.id
            ).group_by(Answer.student_id).all()

            for (score,) in student_scores:
                if score:
                    all_scores.append(float(score))

        if all_scores:
            avg_score = round(sum(all_scores) / len(all_scores), 1)
            pass_count = sum(1 for s in all_scores if s >= 60)
            pass_rate = round((pass_count / len(all_scores) * 100), 1)
        else:
            avg_score = 0
            pass_rate = 0

        # 6. 成绩分布
        def get_score_range(score):
            if score >= 90:
                return "90-100"
            elif score >= 80:
                return "80-89"
            elif score >= 70:
                return "70-79"
            elif score >= 60:
                return "60-69"
            else:
                return "0-59"

        ranges = ["90-100", "80-89", "70-79", "60-69", "0-59"]
        range_counts = {r: 0 for r in ranges}

        for score in all_scores:
            range_key = get_score_range(score)
            range_counts[range_key] += 1

        score_distribution = []
        for r in ranges:
            count = range_counts[r]
            percentage = round((count / len(all_scores) * 100) if all_scores else 0, 1)
            score_distribution.append({
                'range': r,
                'count': count,
                'percentage': percentage
            })

        return success_response({
            'class_info': {
                'id': class_obj.id,
                'name': class_obj.name,
                'student_count': student_count
            },
            'checkin_stats': {
                'total': total_checkins,
                'checked_in': checked_in_students,
                'rate': checkin_rate,
                'today_count': today_checkins,
                'today_rate': today_rate,
                'by_day': checkin_by_day,
            },
            'assessment_stats': {
                'total': assessment_count,
                'completed': len(all_scores),
                'average_score': avg_score,
                'pass_rate': pass_rate
            },
            'score_distribution': score_distribution
        })

    except Exception as e:
        current_app.logger.error(f'获取班级统计失败: {str(e)}')
        return error_response('获取班级统计失败', 500)


@stats_bp.route('/teacher/class/<int:class_id>/weekly-report', methods=['GET'])
@jwt_required()
def get_class_weekly_report(class_id):
    """
    获取班级周报

    包含：
    - 本周签到统计
    - 本周测试情况
    - 学生表现趋势

    请求方式：GET
    请求路径：/api/stats/teacher/class/<class_id>/weekly-report

    请求头：
    Authorization: Bearer <JWT Token>

    响应格式：
    {
        "code": 200,
        "message": "success",
        "data": {
            "week": "2024-01-15 至 2024-01-21",
            "checkin_trend": [
                {"day": "周一", "count": 28, "rate": 93.3},
                {"day": "周二", "count": 29, "rate": 96.7},
                ...
            ],
            "assessment_trend": [
                {"date": "2024-01-15", "title": "第一单元测试", "average": 85.0},
                ...
            ]
        }
    }
    """
    try:
        # 1. 获取当前教师
        teacher = get_current_user()

        # 2. 验证班级所有权
        class_obj = Class.query.filter_by(
            id=class_id,
            teacher_id=teacher.id
        ).first()

        if not class_obj:
            return error_response('班级不存在或无权限访问', 404)

        student_count = ClassStudent.query.filter_by(
            class_id=class_id,
            status=1
        ).count()

        # 3. 获取本周数据（东八区周一至周日）
        today = local_today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_range_lo, _ = local_date_to_utc_naive_range(week_start)
        _, week_range_hi = local_date_to_utc_naive_range(week_end)

        # 生成本周每天的统计
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        checkin_trend = []

        for i in range(7):
            day = week_start + timedelta(days=i)
            day_start, day_end = local_date_to_utc_naive_range(day)

            day_checkins = Checkin.query.filter(
                Checkin.class_id == class_id,
                Checkin.timestamp >= day_start,
                Checkin.timestamp <= day_end,
                Checkin.status == 1
            ).count()

            rate = round((day_checkins / student_count * 100) if student_count > 0 else 0, 1)
            checkin_trend.append({
                'day': days[i],
                'count': day_checkins,
                'rate': rate
            })

        # 4. 获取本周测试
        week_assessments = Assessment.query.filter(
            Assessment.class_id == class_id,
            Assessment.created_at >= week_range_lo,
            Assessment.created_at <= week_range_hi
        ).all()

        assessment_trend = []
        for assessment in week_assessments:
            # 计算平均分
            scores = db.session.query(
                db.func.sum(db.case((Answer.is_correct == True, Question.score), else_=0))
            ).select_from(Answer).join(
                Question, Question.id == Answer.question_id
            ).filter(
                Answer.assessment_id == assessment.id
            ).group_by(Answer.student_id).all()

            if scores:
                avg = round(sum(float(s[0]) for s in scores) / len(scores), 1)
            else:
                avg = 0

            assessment_trend.append({
                'date': format_stored_utc_as_local(
                    assessment.created_at, fmt='%Y-%m-%d'
                ),
                'title': assessment.title,
                'average': avg
            })

        return success_response({
            'week': f"{week_start.strftime('%Y-%m-%d')} 至 {week_end.strftime('%Y-%m-%d')}",
            'checkin_trend': checkin_trend,
            'assessment_trend': assessment_trend
        })

    except Exception as e:
        current_app.logger.error(f'获取周报失败: {str(e)}')
        return error_response('获取周报失败', 500)
