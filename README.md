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

pip install XlsxWriter==3.0.9

SELECT *
FROM tickets.user_permissions up
JOIN tickets.permissions p ON p.id = up.permission_id
WHERE up.user_id = 1;

https://gamma.app/docs/Django-PostgreSQL-3kvzdumwl1t69na?mode=doc
ALTER TABLE tickets.stock_dispatch_log
DROP CONSTRAINT fk_dispatch_borrow;

ALTER TABLE tickets.stock_dispatch_log
ADD COLUMN borrow_id int;

ALTER TABLE tickets.stock_dispatch_log
ADD CONSTRAINT fk_dispatch_borrow
FOREIGN KEY (borrow_id)
REFERENCES tickets.borrow_requests(id)
ON DELETE CASCADE;



ALTER TABLE tickets.tickets
ADD COLUMN reject_remark TEXT,
ADD COLUMN reject_by INT,
ADD COLUMN reject_at TIMESTAMP;
