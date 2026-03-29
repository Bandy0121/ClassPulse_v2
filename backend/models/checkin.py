"""
签到模型 - 定义课堂签到记录
==========================

本文件定义了签到模型：
- Checkin: 签到记录

签到功能说明：
-------------
签到用于记录学生在特定班级的出勤情况。
通常在课程开始时，教师会发起签到，学生在规定时间内完成签到。

签到方式：
1. 地理位置签到：要求学生在指定范围内（如教室附近）
2. GPS 签到：记录精确的经纬度
3. IP 签到：记录学生的 IP 地址
"""

from extensions import db
from datetime import datetime
from typing import Optional, Dict, Any

from utils.datetime_display import format_stored_utc_as_local


class Checkin(db.Model):
    """
    签到记录模型

    对应数据库表：checkins

    字段说明：
    ---------
    - id: 主键
    - class_id: 班级ID
    - student_id: 学生ID
    - latitude: 纬度
    - longitude: 经度
    - location_hash: 位置哈希（简化定位）
    - ip_address: IP 地址
    - timestamp: 签到时间
    - status: 签到状态
    """
    __tablename__ = 'checkins'

    # ========== 字段定义 ==========
    id = db.Column(
        db.Integer,
        primary_key=True,
        comment='签到ID'
    )
    """主键，自增 ID"""

    class_id = db.Column(
        db.Integer,
        db.ForeignKey('classes.id', ondelete='CASCADE'),
        nullable=False,
        comment='班级ID'
    )
    """
    所属班级的 ID

    关系：
    - 一个班级可以有多个签到记录
    - 删除班级时，相关签到记录也会被删除
    """

    student_id = db.Column(
        db.Integer,
        db.ForeignKey('students.id', ondelete='CASCADE'),
        nullable=False,
        comment='学生ID'
    )
    """
    签到的学生 ID
    """

    latitude = db.Column(
        db.DECIMAL(10, 6),
        comment='纬度'
    )
    """
    学生的纬度坐标
    例如：39.9042（北京的纬度）

    精度说明：
    - DECIMAL(10, 6) 表示最多 10 位数字，其中 6 位小数
    - 6 位小数可以精确到约 0.1 米
    """

    longitude = db.Column(
        db.DECIMAL(10, 6),
        comment='经度'
    )
    """
    学生的经度坐标
    例如：116.4074（北京的经度）
    """

    location_hash = db.Column(
        db.String(100),
        comment='位置哈希'
    )
    """
    位置哈希值（简化定位）

    用途：
    - 用于快速查找同一位置的签到
    - 可以使用简单的哈希算法（如保留前几位小数）
    - 便于实现"在同一个地方签到"的功能

    示例哈希算法：
    def generate_location_hash(lat, lng, precision=2):
        return f"{round(lat, precision)},{round(lng, precision)}"
    """

    ip_address = db.Column(
        db.String(45),
        comment='IP地址'
    )
    """
    学生的 IP 地址

    说明：
    - IPv4: "192.168.1.100" (最多 15 位)
    - IPv6: "2001:0db8:85a3::8a2e:0370:7334" (最多 39 位)
    - 设置为 45 位以兼容 IPv6
    """

    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        comment='签到时间'
    )
    """学生签到的时间"""

    status = db.Column(
        db.SmallInteger,
        default=1,
        comment='状态: 1-正常, 0-无效'
    )
    """
    签到状态
    - 1: 正常（通过验证的签到）
    - 0: 无效（被老师标记为无效的签到）

    无效签到的可能原因：
    - 地理位置不在允许范围内
    - 重复签到
    - IP 地址异常
    """

    # ========== 关系定义 ==========
    # 通过 Class 和 Student 的 backref 已经有反向引用

    # ========== 方法定义 ==========
    def __repr__(self) -> str:
        return f'<Checkin Student {self.student_id} - Class {self.class_id}>'

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'class_id': self.class_id,
            'student_id': self.student_id,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'location_hash': self.location_hash,
            'ip_address': self.ip_address,
            'timestamp': format_stored_utc_as_local(self.timestamp),
            'status': self.status
        }

    def get_location(self) -> Optional[Dict[str, float]]:
        """
        获取地理位置坐标

        返回：
            dict 或 None: {'latitude': ..., 'longitude': ...}
        """
        if self.latitude and self.longitude:
            return {
                'latitude': float(self.latitude),
                'longitude': float(self.longitude)
            }
        return None

    @classmethod
    def create_checkin(
        cls,
        class_id: int,
        student_id: int,
        latitude: float = None,
        longitude: float = None,
        location_hash: str = None,
        ip_address: str = None
    ) -> 'Checkin':
        """
        创建新的签到记录

        这是一个类方法，方便在其他地方调用

        参数：
            class_id: 班级 ID
            student_id: 学生 ID
            latitude: 纬度（可选）
            longitude: 经度（可选）
            location_hash: 位置哈希（可选）
            ip_address: IP 地址（可选）

        返回：
            Checkin: 创建的签到对象
        """
        checkin = cls(
            class_id=class_id,
            student_id=student_id,
            latitude=latitude,
            longitude=longitude,
            location_hash=location_hash,
            ip_address=ip_address,
            status=1
        )

        db.session.add(checkin)
        db.session.commit()

        return checkin

    @classmethod
    def get_class_statistics(cls, class_id: int, start_time: datetime = None, end_time: datetime = None) -> Dict[str, Any]:
        """
        获取班级签到统计

        参数：
            class_id: 班级 ID
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）

        返回：
            dict: 统计信息 {
                'total_students': 班级总人数,
                'checked_in': 签到人数,
                'total_checkins': 签到次数,
                'students': 学生签到详情列表
            }
        """
        from models.class_model import ClassStudent

        # 获取班级总人数（正常在班的学生）
        total_students = ClassStudent.query.filter_by(
            class_id=class_id,
            status=1
        ).count()

        # 构建查询
        query = cls.query.filter_by(class_id=class_id, status=1)

        if start_time:
            query = query.filter(cls.timestamp >= start_time)
        if end_time:
            query = query.filter(cls.timestamp <= end_time)

        # 获取签到次数和人数
        stats = query.with_entities(
            db.func.count(cls.id).label('total_checkins'),
            db.func.count(db.distinct(cls.student_id)).label('checked_in')
        ).first()

        # 获取每个学生的签到详情
        student_checkins = db.session.query(
            cls.student_id,
            db.func.count(cls.id).label('count'),
            db.func.max(cls.timestamp).label('last_checkin')
        ).filter_by(class_id=class_id, status=1)

        if start_time:
            student_checkins = student_checkins.filter(cls.timestamp >= start_time)
        if end_time:
            student_checkins = student_checkins.filter(cls.timestamp <= end_time)

        student_checkins = student_checkins.group_by(cls.student_id).all()

        students = []
        for sc in student_checkins:
            students.append({
                'student_id': sc.student_id,
                'checkin_count': sc.count,
                'last_checkin': format_stored_utc_as_local(sc.last_checkin),
            })

        return {
            'total_students': total_students,
            'checked_in': stats.checked_in if stats else 0,
            'total_checkins': stats.total_checkins if stats else 0,
            'students': students
        }


# ========== 辅助函数 ==========

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    计算两个经纬度之间的距离（单位：米）

    使用 Haversine 公式计算球面距离

    参数：
        lat1, lng1: 第一个点的经纬度
        lat2, lng2: 第二个点的经纬度

    返回：
        float: 距离（米）

    示例：
        # 计算两个地点之间的距离
        distance = calculate_distance(
            39.9042, 116.4074,  # 北京
            31.2304, 121.4737   # 上海
        )
        print(f"距离: {distance} 米")  # 约 1067 公里
    """
    from math import radians, sin, cos, sqrt, atan2

    # 地球半径（单位：米）
    R = 6371000

    # 将角度转换为弧度
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])

    # Haversine 公式
    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance
