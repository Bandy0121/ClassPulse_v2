from extensions import db
from datetime import datetime
from typing import Optional, Dict, Any

from utils.datetime_display import format_stored_utc_as_local


class Checkin(db.Model):
    __tablename__ = 'checkins'

    id = db.Column(
        db.Integer,
        primary_key=True,
        comment='签到ID'
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
    latitude = db.Column(
        db.DECIMAL(10, 6),
        comment='纬度'
    )
    longitude = db.Column(
        db.DECIMAL(10, 6),
        comment='经度'
    )
    location_hash = db.Column(
        db.String(100),
        comment='位置哈希'
    )
    ip_address = db.Column(
        db.String(45),
        comment='IP地址'
    )
    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        comment='签到时间'
    )

    status = db.Column(
        db.SmallInteger,
        default=1,
        comment='状态: 1-正常, 0-无效'
    )
    # 通过 Class 和 Student 的 backref 已经有反向引用

    def __repr__(self) -> str:
        return f'<Checkin Student {self.student_id} - Class {self.class_id}>'

    def to_dict(self) -> Dict[str, Any]:
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



def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
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
