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


-- tickets.approve_line definition

-- Drop table

-- DROP TABLE tickets.approve_line;

CREATE TABLE tickets.approve_line (
	id serial4 NOT NULL,
	ticket_type_id int4 NULL,
	"level" int4 NULL,
	user_id int4 NULL,
	team_id int4 NULL,
	CONSTRAINT approve_line_pkey PRIMARY KEY (id),
	CONSTRAINT uq_flow UNIQUE (ticket_type_id, level),
	CONSTRAINT fk_al_ticket_type FOREIGN KEY (ticket_type_id) REFERENCES tickets.ticket_type(id),
	CONSTRAINT fk_al_user FOREIGN KEY (user_id) REFERENCES tickets.users(id),
	CONSTRAINT fk_approve_line_ticket_type FOREIGN KEY (ticket_type_id) REFERENCES tickets.ticket_type(id),
	CONSTRAINT fk_approve_line_user FOREIGN KEY (user_id) REFERENCES tickets.users(id) ON DELETE CASCADE
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
