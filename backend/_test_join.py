from app import create_app
from models.assessment import Assessment
from models.class_model import Class

app = create_app('development')
with app.app_context():
    try:
        q = Assessment.query.filter_by(id=1).join(Class).filter_by(teacher_id=1).first()
        print("old ok", q)
    except Exception as e:
        print("old ERR", type(e).__name__, e)
    try:
        q2 = (
            Assessment.query.join(Class, Class.id == Assessment.class_id)
            .filter(Assessment.id == 1, Class.teacher_id == 1)
            .first()
        )
        print("new ok", q2)
    except Exception as e:
        print("new ERR", type(e).__name__, e)
