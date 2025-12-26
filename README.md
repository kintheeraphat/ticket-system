# 🎫 Ticket & Approval System

เอกสารนี้ใช้เป็น **คู่มือการทำงานร่วมกัน (2 คน)** สำหรับโปรเจคระบบ Ticket / Request / Approval System

---

## 👥 Team

* Developer A: ____________________
* Developer B: ____________________

> 📌 กติกา: ทุกงานต้องผ่าน Git และ **SQL Migration Script** เท่านั้น ห้ามแก้ไข Database สด

---

## 🧱 Tech Stack

* Backend: **Django (No ORM)** / หรือ Framework ที่ตกลงกัน
* Database: **PostgreSQL**
* Data Access: **Raw SQL / Stored Procedure / View**
* Diagram: dbdiagram.io (DBML)
* Version Control: Git (GitHub / GitLab)

---

## 📁 Project Structure

ticket-system/
├── backend/
│   ├── sql/
│   │   ├── migrations/
│   │   ├── seeds/
│   │   └── views/
│   ├── apps/
│   │   ├── users/
│   │   ├── tickets/
│   │   ├── workflow/
│   │   └── notification/
│   ├── db.py
│   └── manage.py
├── docs/
│   ├── database_schema.dbml
│   └── database_schema.png
├── .env.example
├── .gitignore
└── README.md

---

## 🌿 Git Workflow (สำคัญมาก)

### Branch Structure

* `main` → Stable / ใช้งานได้
* `dev` → รวมงานก่อนขึ้น main
* `feature/*` → งานแต่ละคน

### การเริ่มงานใหม่

```bash
git checkout dev
git pull
git checkout -b feature/ชื่อฟีเจอร์
```

### การส่งงาน

```bash
git add .
git commit -m "[feature] รายละเอียดที่ทำ"
git push origin feature/ชื่อฟีเจอร์
```

จากนั้นเปิด **Pull Request → dev**

---

## 🗄️ Database Rules (NO ORM)

### ❌ ห้าม

* ใช้ ORM
* แก้ Database สด
* เปลี่ยนโครงสร้าง DB โดยไม่มีไฟล์ SQL

### ✅ ต้องทำ

* ทุกการเปลี่ยนแปลง DB ต้องเป็น **SQL Script**
* 1 การเปลี่ยนแปลง = 1 ไฟล์ Migration

โครงสร้างไฟล์:

sql/migrations/
├── 001_create_base_tables.sql
├── 002_add_ticket_workflow.sql
├── 003_add_notification.sql

---

## ▶️ การรัน Migration

```bash
psql -U postgres -d ticket_dev -f sql/migrations/001_create_base_tables.sql
```

> ทุกคนต้องรัน migration ตามลำดับเลข

---

## 📐 Database Schema

* Schema กลางอยู่ที่ `docs/database_schema.dbml`
* ทุกครั้งที่แก้ table / field ต้องแก้ schema พร้อม SQL

---

## 🌱 Seed / Initial Data

ข้อมูลตั้งต้นต้องอยู่ใน `sql/seeds/`

001_roles.sql
002_ticket_category.sql
003_ticket_type.sql

รันด้วย:

```bash
psql -U postgres -d ticket_dev -f sql/seeds/001_roles.sql
```

---

## 🔐 Environment Variables

ใช้ไฟล์ `.env` (ห้าม commit)

```env
DB_NAME=ticket_dev
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

---

## 🧾 SQL & Coding Rules

* ใช้ชื่อ table / column ภาษาอังกฤษ
* ใช้ snake_case
* ห้าม SELECT *
* ทุก action สำคัญต้อง insert log / history
* Transaction ต้องใช้ BEGIN / COMMIT

---

## 🔄 Ticket Working Flow

1. INSERT Ticket
2. INSERT Workflow Steps
3. Approver UPDATE status ทีละ step
4. INSERT History ทุกครั้งที่เปลี่ยนสถานะ
5. ปิด Ticket

---

## 📊 Definition of Done (DoD)

* [ ] SQL Script มี
* [ ] Run ได้จริง
* [ ] ไม่มี Breaking Change
* [ ] Commit Message ชัดเจน
* [ ] Schema อัปเดตแล้ว

---

## 🆘 กติกาทีม

* แก้ DB ต้องแจ้งอีกฝ่ายก่อน
* SQL ใหญ่ → Review ก่อน Merge
* ห้ามแก้โครงสร้างโดยไม่อัปเดต Schema

---

## 🏁 เป้าหมายโปรเจค

> ระบบ Ticket & Approval ที่ควบคุมด้วย SQL จริง
> Audit ได้ / Scale ได้ / ใช้งานในองค์กรได้จริง

---

✍️ Last Update: ____________________
เพื่อเก็บรายชื่อไลบรารี (packages)
 pip list --format=freeze > requirements.txt

เมื่อต้องการติดตั้งจากไฟล์นี้ในเครื่องอื่น
pip install -r requirements.txt
