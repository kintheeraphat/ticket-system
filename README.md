เพื่อเก็บรายชื่อไลบรารี (packages)
 pip list --format=freeze > requirements.txt

เมื่อต้องการติดตั้งจากไฟล์นี้ในเครื่องอื่น
pip install -r requirements.txt

https://drive.google.com/drive/folders/1V4RsHf4nDFhCfjrTDBIOz0V3ZRWYxXVA ******form****

https://docs.google.com/spreadsheets/d/1tdKwYhlCbjCwmUgEuRTdGbYSpdimX1xBWiIp3aGQq-I/edit?gid=1037710724#gid=1037710724 *****ชีต****

DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432
DB_SCHEMA=tickets


-- 1) ลบ Foreign Key ก่อน
ALTER TABLE tickets.approve_line
DROP CONSTRAINT fk_approve_line_ticket_type;

-- 2) ลบ column ticket_type_id
ALTER TABLE tickets.approve_line
DROP COLUMN ticket_type_id;

-- 1) เพิ่ม column category_id
ALTER TABLE tickets.approve_line
ADD COLUMN category_id int4 NULL;

-- 2) เพิ่ม Foreign Key constraint
ALTER TABLE tickets.approve_line
ADD CONSTRAINT fk_approve_line_category
FOREIGN KEY (category_id)
REFERENCES tickets.category(id);



