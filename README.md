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


CREATE TABLE tickets.approve_level (
    id serial4 PRIMARY KEY,
    ticket_id int4 NOT NULL,
    level int4 NOT NULL,
    user_id int4 NOT NULL,
    status_id int4 NOT NULL,  -- pending / waiting / approved / rejected
    approved_at timestamp NULL,
    remark text NULL,
    CONSTRAINT uq_ticket_level UNIQUE (ticket_id, level)
);



ALTER TABLE tickets.status
ADD COLUMN status_group varchar(30) NOT NULL DEFAULT 'general';


ALTER TABLE tickets.approve_level
ADD CONSTRAINT fk_ap_ticket
FOREIGN KEY (ticket_id)
REFERENCES tickets.tickets(id)
ON DELETE CASCADE;

ALTER TABLE tickets.approve_level
ADD CONSTRAINT fk_ap_user
FOREIGN KEY (user_id)
REFERENCES tickets.users(id)
ON DELETE RESTRICT;

ALTER TABLE tickets.approve_level
ADD CONSTRAINT fk_ap_status
FOREIGN KEY (status_id)
REFERENCES tickets.status(id)
ON DELETE RESTRICT;
