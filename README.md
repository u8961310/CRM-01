# 學校 CRM 系統

快速查到「這位家長是誰、談過什麼、下一步是什麼」。

## 技術架構

- **後端**：FastAPI + SQLAlchemy 2.0 (async) + Alembic
- **資料庫**：PostgreSQL (asyncpg)
- **認證**：JWT (httponly cookie) + bcrypt
- **前端**：Jinja2 + Bootstrap 5
- **套件管理**：UV / Python 3.12+

## 功能

- 家長管理（新增、編輯、搜尋、刪除）
- 學生管理（新增、編輯、關聯家長）
- 溝通紀錄（電話、面談、LINE、Email）
- 待辦事項（指派、到期日、完成標記）
- 家長詳情頁 — 一頁看完家長資訊、關聯學生、所有溝通紀錄與待辦
- 說明會管理（建立場次、報名登記、CSV 匯入、Email 通知）
- 角色權限控管（管理員 / 教師 / 櫃台）

## 角色權限

| 功能 | 管理員 | 教師 | 櫃台 |
|------|--------|------|------|
| 管理使用者 | V | | |
| 查看所有家長/學生 | V | V | V |
| 新增/編輯家長/學生 | V | V | V |
| 刪除家長/學生 | V | | |
| 新增/查看溝通紀錄 | V | V | V |
| 管理待辦 | V（全部） | V（自己的） | V（自己的） |
| 管理說明會 | V | V | V |
| 刪除說明會 | V | | |

## 快速開始

```bash
# 1. 安裝依賴
uv sync

# 2. 啟動 PostgreSQL（WSL 環境）
sudo service postgresql start
sudo -u postgres createdb school_crm
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"

# 3. 執行資料庫遷移
uv run alembic upgrade head

# 4. 建立預設管理員帳號
uv run python scripts/seed.py

# 5. 啟動開發伺服器
uv run fastapi dev app/main.py
```

啟動後開啟：
- `http://localhost:8000/login` — 登入頁面
- `http://localhost:8000/docs` — Swagger API 文件

預設管理員帳號：`admin` / `admin123`

## 專案結構

```
app/
├── main.py              # FastAPI 進入點
├── config.py            # 環境變數設定
├── database.py          # 非同步資料庫連線
├── dependencies.py      # 認證與權限依賴注入
├── models/              # SQLAlchemy 資料模型
├── schemas/             # Pydantic 請求/回應格式
├── routers/             # API 路由
│   ├── auth.py          # 登入 / 註冊
│   ├── parents.py       # 家長 CRUD
│   ├── students.py      # 學生 CRUD
│   ├── communications.py # 溝通紀錄
│   ├── follow_ups.py    # 待辦事項
│   ├── info_sessions.py # 說明會 CRUD + 報名 + Email
│   └── pages.py         # 前端頁面路由
├── services/
│   ├── auth.py          # JWT + 密碼雜湊
│   ├── email.py         # Email 通知（placeholder）
│   └── parent_detail.py # 家長全貌查詢
└── templates/           # Jinja2 HTML 模板
```

## API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/auth/login` | 登入 |
| POST | `/api/auth/register` | 註冊（管理員限定） |
| GET | `/api/parents` | 家長列表（支援 `?q=` 搜尋） |
| POST | `/api/parents` | 新增家長 |
| GET | `/api/parents/{id}` | 家長詳情（含學生、紀錄、待辦） |
| PUT | `/api/parents/{id}` | 更新家長 |
| DELETE | `/api/parents/{id}` | 刪除家長（管理員限定） |
| GET | `/api/students` | 學生列表 |
| POST | `/api/students` | 新增學生 |
| GET | `/api/communications` | 溝通紀錄（支援 `?parent_id=`） |
| POST | `/api/communications` | 新增溝通紀錄 |
| GET | `/api/follow-ups` | 待辦列表（支援 `?mine=true&pending=true`） |
| POST | `/api/follow-ups` | 新增待辦 |
| PATCH | `/api/follow-ups/{id}` | 更新待辦（標記完成） |
| GET | `/api/info-sessions` | 說明會列表 |
| POST | `/api/info-sessions` | 新增說明會 |
| GET | `/api/info-sessions/{id}` | 說明會詳情（含報名名單） |
| PUT | `/api/info-sessions/{id}` | 更新說明會 |
| DELETE | `/api/info-sessions/{id}` | 刪除說明會（管理員限定） |
| POST | `/api/info-sessions/{id}/registrations` | 新增報名 |
| DELETE | `/api/info-sessions/{id}/registrations/{reg_id}` | 刪除報名 |
| POST | `/api/info-sessions/{id}/registrations/import` | CSV 匯入報名 |
| POST | `/api/info-sessions/{id}/send-email` | 發送通知 Email |

## 環境變數

在 `.env` 檔案中設定：

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/school_crm
SECRET_KEY=change-me-in-production

# SMTP（選配，用於說明會通知信）
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password
SMTP_FROM=noreply@example.com
```
