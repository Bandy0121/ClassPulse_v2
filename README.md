# ClassPulse 项目手册

## 目录
1. [项目介绍](#项目介绍)
2. [功能说明](#功能说明)
3. [技术架构](#技术架构)
4. [系统设计](#系统设计)
5. [部署说明](#部署说明)
6. [使用指南](#使用指南)

---

## 项目介绍

ClassPulse 是一个学生课堂测试反馈系统，旨在提高课堂教学互动性。系统通过数字化的方式实现：
- **随堂测试**：教师可以快速创建和发布测试，学生在线作答
- **课堂签到**：支持位置签到，自动记录出勤情况
- **数据可视化**：实时显示测试统计，帮助教师了解教学效果

---

## 功能说明

### 教师端功能

#### 1. 账号管理
- **注册**：教师使用邮箱注册账号
- **登录**：使用用户名和密码登录系统
- **个人资料**：查看和管理个人信息

#### 2. 班级管理
- **创建班级**：创建新的课程班级，生成专属班级码
- **查看班级**：查看班级基本信息和学生列表
- **管理班级**：编辑班级信息或删除班级
- **学生管理**：查看 students 加入班级的记录

#### 3. 随堂测试
- **创建测试**：添加测试标题、描述、设置时间
- **编辑题目**：支持单选题和多选题，可设置选项和分值
- **发布测试**：设置测试开始和结束时间后发布
- **查看统计**：实时查看测试数据和学生成绩

#### 4. 数据统计
- **正确率分析**：查看每道题目的正确率（柱状图展示）
- **学生成绩**：查看每个学生的具体对错情况
- **成绩分布**：查看成绩的分布情况（90+、80-89等）
- **签到统计**：查看班级的签到率和记录

### 学生端功能

#### 1. 账号管理
- **注册**：学生使用学号注册账号
- **登录**：登录系统查看个人信息
- **个人信息**：查看姓名、学号等基本信息

#### 2. 班级管理
- **加入班级**：输入班级码加入教师创建的班级
- **查看班级**：查看所在班级的教师和课程信息
- **退出班级**：主动退出不再学习的班级

#### 3. 随堂测试
- **查看测试**：查看待开始、进行中和已完成的测试
- **参与测试**：在规定时间内答题并提交
- **查看结果**：提交后查看测试得分和正确答案
- **测试历史**：查看所有历史测试记录

#### 4. 课堂签到
- **签到功能**：在课堂期间进行位置签到
- **签到记录**：查看自己的签到历史记录

---

## 技术架构

### 前后端分离架构

```
┌─────────────────────────────────────────────────────────────┐
│                       客户端层 (Frontend)                   │
│                   Vue 3 + Element Plus                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  教师端页面   │  │  学生端页面   │  │   公共页面   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/HTTPS (REST API)
                            │
┌─────────────────────────────────────────────────────────────┐
│                       服务层 (Backend)                      │
│                    Flask + SQLAlchemy                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  认证服务    │  │  业务服务    │  │  统计服务    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ SQL
                            │
┌─────────────────────────────────────────────────────────────┐
│                       数据层 (Database)                     │
│                       MySQL                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ 用户表       │  │ 测试表       │  │ 签到表       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue 3 | 前端框架，使用Composition API |
| 前端 | Element Plus | UI 组件库 |
| 前端 | ECharts | 数据可视化图表 |
| 前端 | Vue Router | 路由管理 |
| 前端 | Pinia | 状态管理 |
| 前端 | Axios | HTTP 客户端 |
| 后端 | Flask | Python Web 框架 |
| 后端 | SQLAlchemy | ORM 框架 |
| 后端 | Flask-JWT-Extended | JWT 认证 |
| 数据库 | MySQL | 关系型数据库 |
| 构建工具 | Vite | 前端构建工具 |

---

## 系统设计

### 数据库设计

#### 核心表结构

**1. teachers (教师表)**
```sql
- id: 教师ID (主键)
- username: 用户名 (唯一)
- password_hash: 密码哈希
- email: 邮箱 (唯一)
- real_name: 真实姓名
- created_at: 创建时间
```

**2. students (学生表)**
```sql
- id: 学生ID (主键)
- username: 用户名 (唯一)
- password_hash: 密码哈希
- email: 邮箱 (唯一)
- real_name: 真实姓名
- student_id: 学号 (唯一)
- created_at: 创建时间
```

**3. classes (班级表)**
```sql
- id: 班级ID (主键)
- name: 班级名称
- class_code: 班级邀请码 (唯一)
- description: 班级描述
- teacher_id: 教师ID (外键)
- created_at: 创建时间
```

**4. class_students (班级-学生关联表)**
```sql
- id: 关联ID (主键)
- class_id: 班级ID (外键)
- student_id: 学生ID (外键)
- joined_at: 加入时间
- status: 关联状态 (1-正常, 0-已退出)
```

**5. assessments (随堂测试表)**
```sql
- id: 测试ID (主键)
- class_id: 班级ID (外键)
- title: 测试标题
- description: 测试描述
- start_time: 开始时间
- end_time: 结束时间
- duration_minutes: 考试时长
- max_attempts: 最大尝试次数
- show_correct_after_submit: 提交后显示答案
- is_published: 是否已发布
- created_at: 创建时间
```

**6. questions (题目表)**
```sql
- id: 题目ID (主键)
- assessment_id: 测试ID (外键)
- question_type: 题型 (1-单选, 2-多选)
- content: 题目内容
- option_a/b/c/d: 选项内容
- correct_answer: 正确答案
- score: 分值
- created_at: 创建时间
```

**7. answers (答案表)**
```sql
- id: 答案ID (主键)
- assessment_id: 测试ID (外键)
- question_id: 题目ID (外键)
- student_id: 学生ID (外键)
- selected_option: 选择的答案
- is_correct: 是否正确
- submitted_at: 提交时间
- response_time_seconds: 答题耗时
- attempt_number: 尝试次数
```

**8. checkins (签到表)**
```sql
- id: 签到ID (主键)
- class_id: 班级ID (外键)
- student_id: 学生ID (外键)
- latitude: 纬度
- longitude: 经度
- location_hash: 位置哈希
- ip_address: IP地址
- timestamp: 签到时间
- status: 状态 (1-正常, 0-无效)
```

### API 设计

#### 统一响应格式
```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

#### 认证相关 API
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/teacher/register | 教师注册 |
| POST | /api/auth/teacher/login | 教师登录 |
| POST | /api/auth/student/register | 学生注册 |
| POST | /api/auth/student/login | 学生登录 |
| POST | /api/auth/logout | 退出登录 |
| POST | /api/auth/refresh | 刷新令牌 |

#### 教师端 API
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/teacher/classes | 获取班级列表 |
| POST | /api/teacher/classes | 创建班级 |
| GET | /api/teacher/classes/:id | 获取班级详情 |
| PUT | /api/teacher/classes/:id | 更新班级 |
| DELETE | /api/teacher/classes/:id | 删除班级 |
| POST | /api/teacher/classes/:id/assessments | 创建测试 |
| GET | /api/teacher/classes/:id/assessments | 获取测试列表 |
| POST | /api/teacher/assessments/:id/questions | 添加题目 |
| PUT | /api/teacher/assessments/:id/publish | 发布测试 |
| GET | /api/teacher/assessments/:id/statistics | 测试统计 |

#### 学生端 API
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/student/classes | 获取班级列表 |
| POST | /api/student/classes/join | 加入班级 |
| DELETE | /api/student/classes/:id | 退出班级 |
| GET | /api/student/assessments | 获取测试列表 |
| GET | /api/student/assessments/:id | 获取测试详情 |
| POST | /api/student/assessments/:id/submit | 提交答案 |
| GET | /api/student/assessments/:id/result | 查看结果 |
| POST | /api/student/checkin | 课堂签到 |
| GET | /api/student/history | 测试历史 |

### 认证机制

#### JWT (JSON Web Token)
系统使用 JWT 进行用户认证：

1. **登录时**：验证用户凭据，生成 JWT 令牌
2. **令牌结构**：
   ```json
   {
     "user_id": 1,
     "user_type": "teacher"
   }
   ```
3. **令牌过期**：访问令牌 2 小时过期，刷新令牌 7 天过期
4. **请求认证**：前端在请求头中添加 `Authorization: Bearer <token>`
5. **后端验证**：验证令牌签名和过期时间

#### 角色验证
- 教师只能访问 `/teacher/*` 路径
- 学生只能访问 `/student/*` 路径
- 未登录用户重定向到登录页面

---

## 部署说明

### 环境要求

**后端**
- Python 3.8+
- MySQL 5.7+
- pip (Python 包管理器)

**前端**
- Node.js 16+
- npm 或 yarn

### 后端部署

#### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

#### 2. 配置数据库
```sql
-- 创建数据库
CREATE DATABASE classpulse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 3. 配置环境变量
创建 `.env` 文件：
```bash
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/classpulse
FLASK_ENV=development
```

#### 4. 运行后端
```bash
# 开发环境
flask run --host=0.0.0.0 --port=5000

# 生产环境
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 前端部署

#### 1. 安装依赖
```bash
cd frontend
npm install
```

#### 2. 配置环境变量
创建 `.env` 文件：
```bash
VITE_API_BASE_URL=/api
```

#### 3. 开发运行
```bash
npm run dev
```

#### 4. 生产构建
```bash
npm run build
# 构建产物在 dist 目录
```

---

## 使用指南

### 教师使用流程

#### 1. 首次使用 - 注册账号
1. 访问教师登录页面
2. 点击"立即注册"
3. 填写用户名、密码、邮箱、真实姓名
4. 提交注册

#### 2. 创建班级
1. 登录后进入教师仪表盘
2. 点击"创建班级"按钮
3. 填写班级名称和描述
4. 系统生成专属班级码

#### 3. 发布随堂测试
1. 进入对应班级页面
2. 点击"创建测试"
3. 填写测试标题、描述、设置时间
4. 添加题目（支持单选、多选）
5. 点击"发布"按钮

#### 4. 查看统计
1. 进入测试详情页面
2. 查看每题正确率（图表）
3. 查看学生成绩表格
4. 下载学生答题详情

#### 5. 课堂签到
1. 在测试页面发起签到
2. 学生在规定时间内签到
3. 查看签到统计

### 学生使用流程

#### 1. 首次使用 - 注册账号
1. 访问学生登录页面
2. 点击"立即注册"
3. 填写用户名、密码、邮箱、学号
4. 提交注册

#### 2. 加入班级
1. 登录后进入学生页面
2. 输入教师提供的班级码
3. 点击"加入班级"

#### 3. 参与测试
1. 查看"待测试"列表
2. 点击测试进入答题页面
3. 在规定时间内完成答题
4. 提交答案

#### 4. 查看成绩
1. 提交后查看得分
2. 查看每题对错
3. 查看正确答案解析
4. 在"历史记录"中查看所有测试

#### 5. 课堂签到
1. 收到签到通知
2. 打开签到页面
3. 授权地理位置
4. 完成签到

---

## 代码结构

**后端**
- 遵循 PEP 8 编码规范
- 使用类型注解
- 函数和类需要文档字符串

**前端**

- Vue 3 Composition API
- 使用 ESLint 和 Prettier
- 组件需要 props 类型定义

### 项目结构

```
ClassPulse/
├── backend/
│   ├── app.py              # Flask 主应用
│   ├── config.py           # 配置文件
│   ├── requirements.txt    # Python 依赖
│   ├── models/             # 数据模型
│   ├── blueprints/         # API 蓝图
│   └── utils/              # 工具函数
├── frontend/
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 公共组件
│   │   ├── router/         # 路由配置
│   │   ├── stores/         # 状态管理
│   │   └── api/            # API 客户端
│   └── package.json
└── README.md
```

