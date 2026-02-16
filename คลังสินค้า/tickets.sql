--
-- PostgreSQL database dump
--

\restrict pKbByFqgnLOZn1fq1BSjWl9JrHESljrI4RbRrcevInOPO8XPHhlDtdrYuYDz15u

-- Dumped from database version 18.0
-- Dumped by pg_dump version 18.0

-- Started on 2026-02-16 10:52:42

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 405 (class 1259 OID 19360)
-- Name: permissions; Type: TABLE; Schema: tickets; Owner: postgres
--

CREATE TABLE tickets.permissions (
    id integer NOT NULL,
    code character varying(100) NOT NULL,
    url_name character varying(100) NOT NULL,
    description text,
    create_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE tickets.permissions OWNER TO postgres;

--
-- TOC entry 404 (class 1259 OID 19359)
-- Name: permissions_id_seq; Type: SEQUENCE; Schema: tickets; Owner: postgres
--

CREATE SEQUENCE tickets.permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE tickets.permissions_id_seq OWNER TO postgres;

--
-- TOC entry 5449 (class 0 OID 0)
-- Dependencies: 404
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: tickets; Owner: postgres
--

ALTER SEQUENCE tickets.permissions_id_seq OWNED BY tickets.permissions.id;


--
-- TOC entry 407 (class 1259 OID 19375)
-- Name: user_permissions; Type: TABLE; Schema: tickets; Owner: postgres
--

CREATE TABLE tickets.user_permissions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL,
    allow boolean DEFAULT true,
    create_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE tickets.user_permissions OWNER TO postgres;

--
-- TOC entry 406 (class 1259 OID 19374)
-- Name: user_permissions_id_seq; Type: SEQUENCE; Schema: tickets; Owner: postgres
--

CREATE SEQUENCE tickets.user_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE tickets.user_permissions_id_seq OWNER TO postgres;

--
-- TOC entry 5450 (class 0 OID 0)
-- Dependencies: 406
-- Name: user_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: tickets; Owner: postgres
--

ALTER SEQUENCE tickets.user_permissions_id_seq OWNED BY tickets.user_permissions.id;


--
-- TOC entry 5278 (class 2604 OID 19363)
-- Name: permissions id; Type: DEFAULT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.permissions ALTER COLUMN id SET DEFAULT nextval('tickets.permissions_id_seq'::regclass);


--
-- TOC entry 5280 (class 2604 OID 19378)
-- Name: user_permissions id; Type: DEFAULT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.user_permissions ALTER COLUMN id SET DEFAULT nextval('tickets.user_permissions_id_seq'::regclass);


--
-- TOC entry 5441 (class 0 OID 19360)
-- Dependencies: 405
-- Data for Name: permissions; Type: TABLE DATA; Schema: tickets; Owner: postgres
--

INSERT INTO tickets.permissions VALUES (2, 'dashboard', 'dashboard', 'หน้า Dashboard', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (5, 'tickets_list', 'tickets_list', 'รายการ Tickets', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (6, 'tickets_detail_erp', 'tickets_detail_erp', 'รายละเอียด ERP', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (7, 'tickets_detail_vpn', 'tickets_detail_vpn', 'รายละเอียด VPN', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (8, 'tickets_detail_repairs', 'tickets_detail_repairs', 'รายละเอียด Repairs', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (9, 'tickets_detail_report', 'tickets_detail_report', 'รายละเอียด Report', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (10, 'tickets_detail_newapp', 'tickets_detail_newapp', 'รายละเอียด New App', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (11, 'active_promotion_detail', 'active_promotion_detail', 'รายละเอียด Promotion', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (12, 'create', 'create', 'สร้าง Ticket', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (13, 'erp_perm', 'erp_perm', 'สร้าง ERP Permission', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (14, 'repairs_form', 'repairs_form', 'สร้าง Repairs', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (15, 'adjust_form', 'adjust_form', 'สร้าง Adjust', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (16, 'app_form', 'app_form', 'สร้าง App', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (17, 'report_form', 'report_form', 'สร้าง Report', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (18, 'active_promotion_form', 'active_promotion_form', 'สร้าง Active Promotion', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (19, 'vpn', 'vpn', 'สร้าง VPN', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (20, 'borrows', 'borrows', 'สร้าง Borrow', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (21, 'ticket_success', 'ticket_success', 'หน้าสำเร็จหลังสร้าง Ticket', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (22, 'setting_team', 'setting_team', 'ตั้งค่า Team', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (23, 'team_adduser', 'team_adduser', 'เพิ่มสมาชิก Team', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (24, 'team_removeuser', 'team_removeuser', 'ลบสมาชิก Team', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (25, 'add_approve_line', 'add_approve_line', 'เพิ่มสายอนุมัติ', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (26, 'approval_flow_detail', 'approval_flow_detail', 'รายละเอียด Approval Flow', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (27, 'manage_user', 'manage_user', 'จัดการผู้ใช้', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (28, 'delete_ticket', 'delete_ticket', 'ลบ Ticket', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (29, 'approve_ticket', 'approve_ticket', 'อนุมัติ Ticket', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (30, 'admin_complete_ticket', 'admin_complete_ticket', 'Admin ปิดงาน', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (31, 'tickets_accepting_work', 'tickets_accepting_work', 'งานรอรับ', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (32, 'admin_accept_work', 'admin_accept_work', 'Admin รับงาน', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (33, 'manage_permission', 'manage_permission', 'จัดการสิทธิ์หน้า', '2026-02-12 09:33:28.694192');


--
-- TOC entry 5443 (class 0 OID 19375)
-- Dependencies: 407
-- Data for Name: user_permissions; Type: TABLE DATA; Schema: tickets; Owner: postgres
--

INSERT INTO tickets.user_permissions VALUES (134, 13, 11, true, '2026-02-12 03:19:46.597191');
INSERT INTO tickets.user_permissions VALUES (135, 13, 18, true, '2026-02-12 03:19:46.597951');
INSERT INTO tickets.user_permissions VALUES (136, 13, 25, true, '2026-02-12 03:19:46.598394');
INSERT INTO tickets.user_permissions VALUES (137, 13, 15, true, '2026-02-12 03:19:46.600411');
INSERT INTO tickets.user_permissions VALUES (138, 13, 32, true, '2026-02-12 03:19:46.60161');
INSERT INTO tickets.user_permissions VALUES (139, 13, 30, true, '2026-02-12 03:19:46.602983');
INSERT INTO tickets.user_permissions VALUES (140, 13, 16, true, '2026-02-12 03:19:46.604308');
INSERT INTO tickets.user_permissions VALUES (141, 13, 26, true, '2026-02-12 03:19:46.605381');
INSERT INTO tickets.user_permissions VALUES (142, 13, 29, true, '2026-02-12 03:19:46.605841');
INSERT INTO tickets.user_permissions VALUES (143, 13, 20, true, '2026-02-12 03:19:46.606255');
INSERT INTO tickets.user_permissions VALUES (144, 13, 12, true, '2026-02-12 03:19:46.606527');
INSERT INTO tickets.user_permissions VALUES (145, 13, 2, true, '2026-02-12 03:19:46.606802');
INSERT INTO tickets.user_permissions VALUES (146, 13, 28, true, '2026-02-12 03:19:46.607079');
INSERT INTO tickets.user_permissions VALUES (147, 13, 13, true, '2026-02-12 03:19:46.607378');
INSERT INTO tickets.user_permissions VALUES (151, 13, 33, true, '2026-02-12 03:19:46.608442');
INSERT INTO tickets.user_permissions VALUES (152, 13, 27, true, '2026-02-12 03:19:46.608678');
INSERT INTO tickets.user_permissions VALUES (153, 13, 14, true, '2026-02-12 03:19:46.608913');
INSERT INTO tickets.user_permissions VALUES (154, 13, 17, true, '2026-02-12 03:19:46.609154');
INSERT INTO tickets.user_permissions VALUES (155, 13, 22, true, '2026-02-12 03:19:46.609415');
INSERT INTO tickets.user_permissions VALUES (156, 13, 23, true, '2026-02-12 03:19:46.609665');
INSERT INTO tickets.user_permissions VALUES (157, 13, 24, true, '2026-02-12 03:19:46.609894');
INSERT INTO tickets.user_permissions VALUES (158, 13, 21, true, '2026-02-12 03:19:46.610122');
INSERT INTO tickets.user_permissions VALUES (159, 13, 31, true, '2026-02-12 03:19:46.610343');
INSERT INTO tickets.user_permissions VALUES (160, 13, 6, true, '2026-02-12 03:19:46.610562');
INSERT INTO tickets.user_permissions VALUES (161, 13, 10, true, '2026-02-12 03:19:46.610786');
INSERT INTO tickets.user_permissions VALUES (162, 13, 8, true, '2026-02-12 03:19:46.611008');
INSERT INTO tickets.user_permissions VALUES (163, 13, 9, true, '2026-02-12 03:19:46.611257');
INSERT INTO tickets.user_permissions VALUES (164, 13, 7, true, '2026-02-12 03:19:46.611548');
INSERT INTO tickets.user_permissions VALUES (165, 13, 5, true, '2026-02-12 03:19:46.611846');
INSERT INTO tickets.user_permissions VALUES (166, 13, 19, true, '2026-02-12 03:19:46.612177');
INSERT INTO tickets.user_permissions VALUES (419, 1, 11, true, '2026-02-13 09:34:30.704084');
INSERT INTO tickets.user_permissions VALUES (420, 1, 18, true, '2026-02-13 09:34:30.705268');
INSERT INTO tickets.user_permissions VALUES (421, 1, 25, true, '2026-02-13 09:34:30.705854');
INSERT INTO tickets.user_permissions VALUES (422, 1, 15, true, '2026-02-13 09:34:30.706524');
INSERT INTO tickets.user_permissions VALUES (423, 1, 32, true, '2026-02-13 09:34:30.706913');
INSERT INTO tickets.user_permissions VALUES (424, 1, 30, true, '2026-02-13 09:34:30.707227');
INSERT INTO tickets.user_permissions VALUES (425, 1, 16, true, '2026-02-13 09:34:30.707524');
INSERT INTO tickets.user_permissions VALUES (426, 1, 26, true, '2026-02-13 09:34:30.707755');
INSERT INTO tickets.user_permissions VALUES (427, 1, 29, true, '2026-02-13 09:34:30.707981');
INSERT INTO tickets.user_permissions VALUES (428, 1, 20, true, '2026-02-13 09:34:30.708196');
INSERT INTO tickets.user_permissions VALUES (429, 1, 12, true, '2026-02-13 09:34:30.708416');
INSERT INTO tickets.user_permissions VALUES (430, 1, 2, true, '2026-02-13 09:34:30.70863');
INSERT INTO tickets.user_permissions VALUES (431, 1, 28, true, '2026-02-13 09:34:30.708848');
INSERT INTO tickets.user_permissions VALUES (432, 1, 13, true, '2026-02-13 09:34:30.709066');
INSERT INTO tickets.user_permissions VALUES (436, 1, 33, true, '2026-02-13 09:34:30.709957');
INSERT INTO tickets.user_permissions VALUES (437, 1, 27, true, '2026-02-13 09:34:30.710171');
INSERT INTO tickets.user_permissions VALUES (438, 1, 14, true, '2026-02-13 09:34:30.710387');
INSERT INTO tickets.user_permissions VALUES (439, 1, 17, true, '2026-02-13 09:34:30.710595');
INSERT INTO tickets.user_permissions VALUES (440, 1, 22, true, '2026-02-13 09:34:30.710808');
INSERT INTO tickets.user_permissions VALUES (441, 1, 23, true, '2026-02-13 09:34:30.711033');
INSERT INTO tickets.user_permissions VALUES (442, 1, 24, true, '2026-02-13 09:34:30.711242');
INSERT INTO tickets.user_permissions VALUES (443, 1, 21, true, '2026-02-13 09:34:30.711616');
INSERT INTO tickets.user_permissions VALUES (444, 1, 31, true, '2026-02-13 09:34:30.712026');
INSERT INTO tickets.user_permissions VALUES (445, 1, 6, true, '2026-02-13 09:34:30.712374');
INSERT INTO tickets.user_permissions VALUES (446, 1, 10, true, '2026-02-13 09:34:30.712681');
INSERT INTO tickets.user_permissions VALUES (447, 1, 8, true, '2026-02-13 09:34:30.713025');
INSERT INTO tickets.user_permissions VALUES (448, 1, 9, true, '2026-02-13 09:34:30.713339');
INSERT INTO tickets.user_permissions VALUES (449, 1, 7, true, '2026-02-13 09:34:30.713681');
INSERT INTO tickets.user_permissions VALUES (450, 1, 5, true, '2026-02-13 09:34:30.713988');
INSERT INTO tickets.user_permissions VALUES (451, 1, 19, true, '2026-02-13 09:34:30.714279');
INSERT INTO tickets.user_permissions VALUES (489, 3, 11, true, '2026-02-13 10:01:32.779594');
INSERT INTO tickets.user_permissions VALUES (490, 3, 18, true, '2026-02-13 10:01:32.780313');
INSERT INTO tickets.user_permissions VALUES (491, 3, 15, true, '2026-02-13 10:01:32.78068');
INSERT INTO tickets.user_permissions VALUES (492, 3, 16, true, '2026-02-13 10:01:32.781071');
INSERT INTO tickets.user_permissions VALUES (493, 3, 26, true, '2026-02-13 10:01:32.781594');
INSERT INTO tickets.user_permissions VALUES (494, 3, 20, true, '2026-02-13 10:01:32.782042');
INSERT INTO tickets.user_permissions VALUES (495, 3, 12, true, '2026-02-13 10:01:32.782474');
INSERT INTO tickets.user_permissions VALUES (496, 3, 28, true, '2026-02-13 10:01:32.782888');
INSERT INTO tickets.user_permissions VALUES (497, 3, 13, true, '2026-02-13 10:01:32.783284');
INSERT INTO tickets.user_permissions VALUES (498, 3, 27, true, '2026-02-13 10:01:32.783628');
INSERT INTO tickets.user_permissions VALUES (499, 3, 14, true, '2026-02-13 10:01:32.784059');
INSERT INTO tickets.user_permissions VALUES (500, 3, 17, true, '2026-02-13 10:01:32.784358');
INSERT INTO tickets.user_permissions VALUES (501, 3, 6, true, '2026-02-13 10:01:32.784748');
INSERT INTO tickets.user_permissions VALUES (502, 3, 10, true, '2026-02-13 10:01:32.785312');
INSERT INTO tickets.user_permissions VALUES (503, 3, 8, true, '2026-02-13 10:01:32.786278');
INSERT INTO tickets.user_permissions VALUES (504, 3, 9, true, '2026-02-13 10:01:32.787643');
INSERT INTO tickets.user_permissions VALUES (505, 3, 7, true, '2026-02-13 10:01:32.788184');
INSERT INTO tickets.user_permissions VALUES (506, 3, 5, true, '2026-02-13 10:01:32.788721');
INSERT INTO tickets.user_permissions VALUES (507, 3, 19, true, '2026-02-13 10:01:32.789253');
INSERT INTO tickets.user_permissions VALUES (558, 29, 11, true, '2026-02-16 03:10:44.597838');
INSERT INTO tickets.user_permissions VALUES (559, 29, 18, true, '2026-02-16 03:10:44.598555');
INSERT INTO tickets.user_permissions VALUES (560, 29, 25, true, '2026-02-16 03:10:44.598974');
INSERT INTO tickets.user_permissions VALUES (561, 29, 15, true, '2026-02-16 03:10:44.599351');
INSERT INTO tickets.user_permissions VALUES (562, 29, 16, true, '2026-02-16 03:10:44.599776');
INSERT INTO tickets.user_permissions VALUES (563, 29, 26, true, '2026-02-16 03:10:44.600266');
INSERT INTO tickets.user_permissions VALUES (564, 29, 29, true, '2026-02-16 03:10:44.600643');
INSERT INTO tickets.user_permissions VALUES (565, 29, 20, true, '2026-02-16 03:10:44.600948');
INSERT INTO tickets.user_permissions VALUES (566, 29, 12, true, '2026-02-16 03:10:44.601247');
INSERT INTO tickets.user_permissions VALUES (567, 29, 28, true, '2026-02-16 03:10:44.601548');
INSERT INTO tickets.user_permissions VALUES (568, 29, 13, true, '2026-02-16 03:10:44.601844');
INSERT INTO tickets.user_permissions VALUES (569, 29, 14, true, '2026-02-16 03:10:44.60214');
INSERT INTO tickets.user_permissions VALUES (570, 29, 17, true, '2026-02-16 03:10:44.602431');
INSERT INTO tickets.user_permissions VALUES (571, 29, 21, true, '2026-02-16 03:10:44.602721');
INSERT INTO tickets.user_permissions VALUES (200, 39, 11, true, '2026-02-12 03:20:51.68997');
INSERT INTO tickets.user_permissions VALUES (201, 39, 18, true, '2026-02-12 03:20:51.690957');
INSERT INTO tickets.user_permissions VALUES (202, 39, 25, true, '2026-02-12 03:20:51.691458');
INSERT INTO tickets.user_permissions VALUES (203, 39, 15, true, '2026-02-12 03:20:51.691917');
INSERT INTO tickets.user_permissions VALUES (204, 39, 32, true, '2026-02-12 03:20:51.692375');
INSERT INTO tickets.user_permissions VALUES (205, 39, 30, true, '2026-02-12 03:20:51.692835');
INSERT INTO tickets.user_permissions VALUES (206, 39, 16, true, '2026-02-12 03:20:51.693303');
INSERT INTO tickets.user_permissions VALUES (207, 39, 26, true, '2026-02-12 03:20:51.693574');
INSERT INTO tickets.user_permissions VALUES (208, 39, 29, true, '2026-02-12 03:20:51.693852');
INSERT INTO tickets.user_permissions VALUES (209, 39, 20, true, '2026-02-12 03:20:51.694216');
INSERT INTO tickets.user_permissions VALUES (210, 39, 12, true, '2026-02-12 03:20:51.694539');
INSERT INTO tickets.user_permissions VALUES (211, 39, 2, true, '2026-02-12 03:20:51.694787');
INSERT INTO tickets.user_permissions VALUES (212, 39, 28, true, '2026-02-12 03:20:51.69524');
INSERT INTO tickets.user_permissions VALUES (213, 39, 13, true, '2026-02-12 03:20:51.696123');
INSERT INTO tickets.user_permissions VALUES (217, 39, 33, true, '2026-02-12 03:20:51.698571');
INSERT INTO tickets.user_permissions VALUES (218, 39, 27, true, '2026-02-12 03:20:51.69907');
INSERT INTO tickets.user_permissions VALUES (219, 39, 14, true, '2026-02-12 03:20:51.699432');
INSERT INTO tickets.user_permissions VALUES (220, 39, 17, true, '2026-02-12 03:20:51.699724');
INSERT INTO tickets.user_permissions VALUES (221, 39, 22, true, '2026-02-12 03:20:51.700009');
INSERT INTO tickets.user_permissions VALUES (222, 39, 23, true, '2026-02-12 03:20:51.700303');
INSERT INTO tickets.user_permissions VALUES (223, 39, 24, true, '2026-02-12 03:20:51.700631');
INSERT INTO tickets.user_permissions VALUES (224, 39, 21, true, '2026-02-12 03:20:51.700953');
INSERT INTO tickets.user_permissions VALUES (572, 29, 6, true, '2026-02-16 03:10:44.603015');
INSERT INTO tickets.user_permissions VALUES (573, 29, 10, true, '2026-02-16 03:10:44.603242');
INSERT INTO tickets.user_permissions VALUES (574, 29, 8, true, '2026-02-16 03:10:44.603461');
INSERT INTO tickets.user_permissions VALUES (575, 29, 9, true, '2026-02-16 03:10:44.60368');
INSERT INTO tickets.user_permissions VALUES (576, 29, 7, true, '2026-02-16 03:10:44.603894');
INSERT INTO tickets.user_permissions VALUES (577, 29, 5, true, '2026-02-16 03:10:44.60411');
INSERT INTO tickets.user_permissions VALUES (578, 29, 19, true, '2026-02-16 03:10:44.604321');
INSERT INTO tickets.user_permissions VALUES (225, 39, 31, true, '2026-02-12 03:20:51.701204');
INSERT INTO tickets.user_permissions VALUES (226, 39, 6, true, '2026-02-12 03:20:51.701599');
INSERT INTO tickets.user_permissions VALUES (227, 39, 10, true, '2026-02-12 03:20:51.701887');
INSERT INTO tickets.user_permissions VALUES (228, 39, 8, true, '2026-02-12 03:20:51.702134');
INSERT INTO tickets.user_permissions VALUES (229, 39, 9, true, '2026-02-12 03:20:51.702403');
INSERT INTO tickets.user_permissions VALUES (230, 39, 7, true, '2026-02-12 03:20:51.702646');
INSERT INTO tickets.user_permissions VALUES (231, 39, 5, true, '2026-02-12 03:20:51.702907');
INSERT INTO tickets.user_permissions VALUES (232, 39, 19, true, '2026-02-12 03:20:51.703135');
INSERT INTO tickets.user_permissions VALUES (233, 11, 11, true, '2026-02-12 03:21:17.874181');
INSERT INTO tickets.user_permissions VALUES (234, 11, 18, true, '2026-02-12 03:21:17.875127');
INSERT INTO tickets.user_permissions VALUES (235, 11, 25, true, '2026-02-12 03:21:17.875575');
INSERT INTO tickets.user_permissions VALUES (236, 11, 15, true, '2026-02-12 03:21:17.875996');
INSERT INTO tickets.user_permissions VALUES (237, 11, 32, true, '2026-02-12 03:21:17.876388');
INSERT INTO tickets.user_permissions VALUES (238, 11, 30, true, '2026-02-12 03:21:17.876772');
INSERT INTO tickets.user_permissions VALUES (239, 11, 16, true, '2026-02-12 03:21:17.877348');
INSERT INTO tickets.user_permissions VALUES (240, 11, 26, true, '2026-02-12 03:21:17.877877');
INSERT INTO tickets.user_permissions VALUES (241, 11, 29, true, '2026-02-12 03:21:17.878583');
INSERT INTO tickets.user_permissions VALUES (242, 11, 20, true, '2026-02-12 03:21:17.879074');
INSERT INTO tickets.user_permissions VALUES (243, 11, 12, true, '2026-02-12 03:21:17.879488');
INSERT INTO tickets.user_permissions VALUES (244, 11, 2, true, '2026-02-12 03:21:17.879823');
INSERT INTO tickets.user_permissions VALUES (245, 11, 28, true, '2026-02-12 03:21:17.880146');
INSERT INTO tickets.user_permissions VALUES (246, 11, 13, true, '2026-02-12 03:21:17.88053');
INSERT INTO tickets.user_permissions VALUES (250, 11, 33, true, '2026-02-12 03:21:17.881794');
INSERT INTO tickets.user_permissions VALUES (251, 11, 27, true, '2026-02-12 03:21:17.882015');
INSERT INTO tickets.user_permissions VALUES (252, 11, 14, true, '2026-02-12 03:21:17.882359');
INSERT INTO tickets.user_permissions VALUES (253, 11, 17, true, '2026-02-12 03:21:17.882605');
INSERT INTO tickets.user_permissions VALUES (254, 11, 22, true, '2026-02-12 03:21:17.882856');
INSERT INTO tickets.user_permissions VALUES (255, 11, 23, true, '2026-02-12 03:21:17.883212');
INSERT INTO tickets.user_permissions VALUES (256, 11, 24, true, '2026-02-12 03:21:17.883457');
INSERT INTO tickets.user_permissions VALUES (257, 11, 21, true, '2026-02-12 03:21:17.88371');
INSERT INTO tickets.user_permissions VALUES (258, 11, 31, true, '2026-02-12 03:21:17.88395');
INSERT INTO tickets.user_permissions VALUES (259, 11, 6, true, '2026-02-12 03:21:17.884204');
INSERT INTO tickets.user_permissions VALUES (260, 11, 10, true, '2026-02-12 03:21:17.884454');
INSERT INTO tickets.user_permissions VALUES (261, 11, 8, true, '2026-02-12 03:21:17.884755');
INSERT INTO tickets.user_permissions VALUES (262, 11, 9, true, '2026-02-12 03:21:17.885028');
INSERT INTO tickets.user_permissions VALUES (263, 11, 7, true, '2026-02-12 03:21:17.885267');
INSERT INTO tickets.user_permissions VALUES (264, 11, 5, true, '2026-02-12 03:21:17.885498');
INSERT INTO tickets.user_permissions VALUES (265, 11, 19, true, '2026-02-12 03:21:17.88573');
INSERT INTO tickets.user_permissions VALUES (452, 18, 11, true, '2026-02-13 09:39:28.293214');
INSERT INTO tickets.user_permissions VALUES (453, 18, 18, true, '2026-02-13 09:39:28.294783');
INSERT INTO tickets.user_permissions VALUES (454, 18, 15, true, '2026-02-13 09:39:28.29541');
INSERT INTO tickets.user_permissions VALUES (455, 18, 16, true, '2026-02-13 09:39:28.295976');
INSERT INTO tickets.user_permissions VALUES (456, 18, 26, true, '2026-02-13 09:39:28.296493');
INSERT INTO tickets.user_permissions VALUES (457, 18, 20, true, '2026-02-13 09:39:28.299127');
INSERT INTO tickets.user_permissions VALUES (458, 18, 12, true, '2026-02-13 09:39:28.299678');
INSERT INTO tickets.user_permissions VALUES (459, 18, 28, true, '2026-02-13 09:39:28.300226');
INSERT INTO tickets.user_permissions VALUES (460, 18, 13, true, '2026-02-13 09:39:28.300749');
INSERT INTO tickets.user_permissions VALUES (461, 18, 14, true, '2026-02-13 09:39:28.301289');
INSERT INTO tickets.user_permissions VALUES (462, 18, 17, true, '2026-02-13 09:39:28.301708');
INSERT INTO tickets.user_permissions VALUES (463, 18, 6, true, '2026-02-13 09:39:28.302043');
INSERT INTO tickets.user_permissions VALUES (464, 18, 10, true, '2026-02-13 09:39:28.302371');
INSERT INTO tickets.user_permissions VALUES (465, 18, 8, true, '2026-02-13 09:39:28.302689');
INSERT INTO tickets.user_permissions VALUES (466, 18, 9, true, '2026-02-13 09:39:28.3031');
INSERT INTO tickets.user_permissions VALUES (467, 18, 7, true, '2026-02-13 09:39:28.303646');
INSERT INTO tickets.user_permissions VALUES (468, 18, 5, true, '2026-02-13 09:39:28.304291');
INSERT INTO tickets.user_permissions VALUES (469, 18, 19, true, '2026-02-13 09:39:28.304731');
INSERT INTO tickets.user_permissions VALUES (508, 17, 11, true, '2026-02-16 03:08:29.547047');
INSERT INTO tickets.user_permissions VALUES (509, 17, 18, true, '2026-02-16 03:08:29.552527');
INSERT INTO tickets.user_permissions VALUES (510, 17, 25, true, '2026-02-16 03:08:29.553335');
INSERT INTO tickets.user_permissions VALUES (511, 17, 15, true, '2026-02-16 03:08:29.553978');
INSERT INTO tickets.user_permissions VALUES (512, 17, 32, true, '2026-02-16 03:08:29.554744');
INSERT INTO tickets.user_permissions VALUES (513, 17, 30, true, '2026-02-16 03:08:29.555312');
INSERT INTO tickets.user_permissions VALUES (514, 17, 16, true, '2026-02-16 03:08:29.555756');
INSERT INTO tickets.user_permissions VALUES (515, 17, 26, true, '2026-02-16 03:08:29.556238');
INSERT INTO tickets.user_permissions VALUES (516, 17, 29, true, '2026-02-16 03:08:29.556695');
INSERT INTO tickets.user_permissions VALUES (517, 17, 20, true, '2026-02-16 03:08:29.557075');
INSERT INTO tickets.user_permissions VALUES (518, 17, 12, true, '2026-02-16 03:08:29.557426');
INSERT INTO tickets.user_permissions VALUES (519, 17, 2, true, '2026-02-16 03:08:29.557756');
INSERT INTO tickets.user_permissions VALUES (520, 17, 28, true, '2026-02-16 03:08:29.558086');
INSERT INTO tickets.user_permissions VALUES (521, 17, 13, true, '2026-02-16 03:08:29.558506');
INSERT INTO tickets.user_permissions VALUES (522, 17, 33, true, '2026-02-16 03:08:29.558915');
INSERT INTO tickets.user_permissions VALUES (523, 17, 27, true, '2026-02-16 03:08:29.559247');
INSERT INTO tickets.user_permissions VALUES (524, 17, 14, true, '2026-02-16 03:08:29.559546');
INSERT INTO tickets.user_permissions VALUES (525, 17, 17, true, '2026-02-16 03:08:29.559884');
INSERT INTO tickets.user_permissions VALUES (526, 17, 22, true, '2026-02-16 03:08:29.560311');
INSERT INTO tickets.user_permissions VALUES (527, 17, 23, true, '2026-02-16 03:08:29.561165');
INSERT INTO tickets.user_permissions VALUES (528, 17, 24, true, '2026-02-16 03:08:29.561564');
INSERT INTO tickets.user_permissions VALUES (529, 17, 21, true, '2026-02-16 03:08:29.561929');
INSERT INTO tickets.user_permissions VALUES (530, 17, 31, true, '2026-02-16 03:08:29.562361');
INSERT INTO tickets.user_permissions VALUES (531, 17, 6, true, '2026-02-16 03:08:29.562774');
INSERT INTO tickets.user_permissions VALUES (532, 17, 10, true, '2026-02-16 03:08:29.563129');
INSERT INTO tickets.user_permissions VALUES (533, 17, 8, true, '2026-02-16 03:08:29.563445');
INSERT INTO tickets.user_permissions VALUES (534, 17, 9, true, '2026-02-16 03:08:29.56378');
INSERT INTO tickets.user_permissions VALUES (535, 17, 7, true, '2026-02-16 03:08:29.564144');
INSERT INTO tickets.user_permissions VALUES (536, 17, 5, true, '2026-02-16 03:08:29.564551');
INSERT INTO tickets.user_permissions VALUES (537, 17, 19, true, '2026-02-16 03:08:29.56492');
INSERT INTO tickets.user_permissions VALUES (579, 2, 11, true, '2026-02-16 03:11:01.220533');
INSERT INTO tickets.user_permissions VALUES (580, 2, 18, true, '2026-02-16 03:11:01.221564');
INSERT INTO tickets.user_permissions VALUES (581, 2, 25, true, '2026-02-16 03:11:01.222044');
INSERT INTO tickets.user_permissions VALUES (582, 2, 15, true, '2026-02-16 03:11:01.222503');
INSERT INTO tickets.user_permissions VALUES (583, 2, 16, true, '2026-02-16 03:11:01.223826');
INSERT INTO tickets.user_permissions VALUES (584, 2, 26, true, '2026-02-16 03:11:01.224203');
INSERT INTO tickets.user_permissions VALUES (585, 2, 29, true, '2026-02-16 03:11:01.22456');
INSERT INTO tickets.user_permissions VALUES (586, 2, 20, true, '2026-02-16 03:11:01.224855');
INSERT INTO tickets.user_permissions VALUES (587, 2, 12, true, '2026-02-16 03:11:01.225107');
INSERT INTO tickets.user_permissions VALUES (350, 12, 11, true, '2026-02-13 09:28:58.164767');
INSERT INTO tickets.user_permissions VALUES (351, 12, 18, true, '2026-02-13 09:28:58.174604');
INSERT INTO tickets.user_permissions VALUES (352, 12, 25, true, '2026-02-13 09:28:58.175255');
INSERT INTO tickets.user_permissions VALUES (353, 12, 15, true, '2026-02-13 09:28:58.17633');
INSERT INTO tickets.user_permissions VALUES (354, 12, 32, true, '2026-02-13 09:28:58.176702');
INSERT INTO tickets.user_permissions VALUES (355, 12, 30, true, '2026-02-13 09:28:58.177045');
INSERT INTO tickets.user_permissions VALUES (356, 12, 16, true, '2026-02-13 09:28:58.177387');
INSERT INTO tickets.user_permissions VALUES (357, 12, 26, true, '2026-02-13 09:28:58.177632');
INSERT INTO tickets.user_permissions VALUES (358, 12, 29, true, '2026-02-13 09:28:58.177893');
INSERT INTO tickets.user_permissions VALUES (359, 12, 20, true, '2026-02-13 09:28:58.178278');
INSERT INTO tickets.user_permissions VALUES (360, 12, 12, true, '2026-02-13 09:28:58.178696');
INSERT INTO tickets.user_permissions VALUES (361, 12, 2, true, '2026-02-13 09:28:58.179023');
INSERT INTO tickets.user_permissions VALUES (362, 12, 28, true, '2026-02-13 09:28:58.179264');
INSERT INTO tickets.user_permissions VALUES (363, 12, 13, true, '2026-02-13 09:28:58.179484');
INSERT INTO tickets.user_permissions VALUES (367, 12, 33, true, '2026-02-13 09:28:58.180697');
INSERT INTO tickets.user_permissions VALUES (368, 12, 27, true, '2026-02-13 09:28:58.18096');
INSERT INTO tickets.user_permissions VALUES (369, 12, 14, true, '2026-02-13 09:28:58.181202');
INSERT INTO tickets.user_permissions VALUES (370, 12, 17, true, '2026-02-13 09:28:58.181432');
INSERT INTO tickets.user_permissions VALUES (371, 12, 22, true, '2026-02-13 09:28:58.182487');
INSERT INTO tickets.user_permissions VALUES (372, 12, 23, true, '2026-02-13 09:28:58.1828');
INSERT INTO tickets.user_permissions VALUES (373, 12, 24, true, '2026-02-13 09:28:58.183055');
INSERT INTO tickets.user_permissions VALUES (374, 12, 21, true, '2026-02-13 09:28:58.183315');
INSERT INTO tickets.user_permissions VALUES (375, 12, 31, true, '2026-02-13 09:28:58.183557');
INSERT INTO tickets.user_permissions VALUES (376, 12, 6, true, '2026-02-13 09:28:58.183792');
INSERT INTO tickets.user_permissions VALUES (377, 12, 10, true, '2026-02-13 09:28:58.184055');
INSERT INTO tickets.user_permissions VALUES (378, 12, 8, true, '2026-02-13 09:28:58.18436');
INSERT INTO tickets.user_permissions VALUES (379, 12, 9, true, '2026-02-13 09:28:58.184694');
INSERT INTO tickets.user_permissions VALUES (380, 12, 7, true, '2026-02-13 09:28:58.18501');
INSERT INTO tickets.user_permissions VALUES (381, 12, 5, true, '2026-02-13 09:28:58.185376');
INSERT INTO tickets.user_permissions VALUES (588, 2, 28, true, '2026-02-16 03:11:01.225386');
INSERT INTO tickets.user_permissions VALUES (589, 2, 13, true, '2026-02-16 03:11:01.225612');
INSERT INTO tickets.user_permissions VALUES (590, 2, 14, true, '2026-02-16 03:11:01.225836');
INSERT INTO tickets.user_permissions VALUES (591, 2, 17, true, '2026-02-16 03:11:01.226054');
INSERT INTO tickets.user_permissions VALUES (592, 2, 21, true, '2026-02-16 03:11:01.226272');
INSERT INTO tickets.user_permissions VALUES (593, 2, 6, true, '2026-02-16 03:11:01.226491');
INSERT INTO tickets.user_permissions VALUES (594, 2, 10, true, '2026-02-16 03:11:01.226707');
INSERT INTO tickets.user_permissions VALUES (595, 2, 8, true, '2026-02-16 03:11:01.22692');
INSERT INTO tickets.user_permissions VALUES (382, 12, 19, true, '2026-02-13 09:28:58.185752');
INSERT INTO tickets.user_permissions VALUES (470, 4, 11, true, '2026-02-13 10:00:46.398543');
INSERT INTO tickets.user_permissions VALUES (471, 4, 18, true, '2026-02-13 10:00:46.39972');
INSERT INTO tickets.user_permissions VALUES (472, 4, 15, true, '2026-02-13 10:00:46.400214');
INSERT INTO tickets.user_permissions VALUES (473, 4, 16, true, '2026-02-13 10:00:46.40069');
INSERT INTO tickets.user_permissions VALUES (474, 4, 26, true, '2026-02-13 10:00:46.401142');
INSERT INTO tickets.user_permissions VALUES (475, 4, 20, true, '2026-02-13 10:00:46.401554');
INSERT INTO tickets.user_permissions VALUES (476, 4, 12, true, '2026-02-13 10:00:46.402013');
INSERT INTO tickets.user_permissions VALUES (477, 4, 28, true, '2026-02-13 10:00:46.402414');
INSERT INTO tickets.user_permissions VALUES (478, 4, 13, true, '2026-02-13 10:00:46.402802');
INSERT INTO tickets.user_permissions VALUES (479, 4, 27, true, '2026-02-13 10:00:46.403277');
INSERT INTO tickets.user_permissions VALUES (480, 4, 14, true, '2026-02-13 10:00:46.403664');
INSERT INTO tickets.user_permissions VALUES (481, 4, 17, true, '2026-02-13 10:00:46.403995');
INSERT INTO tickets.user_permissions VALUES (482, 4, 6, true, '2026-02-13 10:00:46.4043');
INSERT INTO tickets.user_permissions VALUES (483, 4, 10, true, '2026-02-13 10:00:46.404605');
INSERT INTO tickets.user_permissions VALUES (484, 4, 8, true, '2026-02-13 10:00:46.404884');
INSERT INTO tickets.user_permissions VALUES (485, 4, 9, true, '2026-02-13 10:00:46.405141');
INSERT INTO tickets.user_permissions VALUES (486, 4, 7, true, '2026-02-13 10:00:46.405369');
INSERT INTO tickets.user_permissions VALUES (487, 4, 5, true, '2026-02-13 10:00:46.405605');
INSERT INTO tickets.user_permissions VALUES (488, 4, 19, true, '2026-02-13 10:00:46.405822');
INSERT INTO tickets.user_permissions VALUES (538, 30, 11, true, '2026-02-16 03:09:38.418222');
INSERT INTO tickets.user_permissions VALUES (539, 30, 18, true, '2026-02-16 03:09:38.418991');
INSERT INTO tickets.user_permissions VALUES (540, 30, 25, true, '2026-02-16 03:09:38.419432');
INSERT INTO tickets.user_permissions VALUES (541, 30, 15, true, '2026-02-16 03:09:38.419997');
INSERT INTO tickets.user_permissions VALUES (542, 30, 16, true, '2026-02-16 03:09:38.420469');
INSERT INTO tickets.user_permissions VALUES (543, 30, 26, true, '2026-02-16 03:09:38.42096');
INSERT INTO tickets.user_permissions VALUES (544, 30, 29, true, '2026-02-16 03:09:38.421435');
INSERT INTO tickets.user_permissions VALUES (545, 30, 20, true, '2026-02-16 03:09:38.421853');
INSERT INTO tickets.user_permissions VALUES (546, 30, 12, true, '2026-02-16 03:09:38.422228');
INSERT INTO tickets.user_permissions VALUES (547, 30, 28, true, '2026-02-16 03:09:38.422547');
INSERT INTO tickets.user_permissions VALUES (548, 30, 13, true, '2026-02-16 03:09:38.422849');
INSERT INTO tickets.user_permissions VALUES (549, 30, 14, true, '2026-02-16 03:09:38.423191');
INSERT INTO tickets.user_permissions VALUES (550, 30, 17, true, '2026-02-16 03:09:38.423651');
INSERT INTO tickets.user_permissions VALUES (551, 30, 6, true, '2026-02-16 03:09:38.424131');
INSERT INTO tickets.user_permissions VALUES (552, 30, 10, true, '2026-02-16 03:09:38.424746');
INSERT INTO tickets.user_permissions VALUES (553, 30, 8, true, '2026-02-16 03:09:38.426221');
INSERT INTO tickets.user_permissions VALUES (554, 30, 9, true, '2026-02-16 03:09:38.426659');
INSERT INTO tickets.user_permissions VALUES (555, 30, 7, true, '2026-02-16 03:09:38.426981');
INSERT INTO tickets.user_permissions VALUES (556, 30, 5, true, '2026-02-16 03:09:38.42735');
INSERT INTO tickets.user_permissions VALUES (557, 30, 19, true, '2026-02-16 03:09:38.427649');
INSERT INTO tickets.user_permissions VALUES (596, 2, 9, true, '2026-02-16 03:11:01.227133');
INSERT INTO tickets.user_permissions VALUES (597, 2, 7, true, '2026-02-16 03:11:01.227364');
INSERT INTO tickets.user_permissions VALUES (598, 2, 5, true, '2026-02-16 03:11:01.227575');
INSERT INTO tickets.user_permissions VALUES (599, 2, 19, true, '2026-02-16 03:11:01.229063');


--
-- TOC entry 5451 (class 0 OID 0)
-- Dependencies: 404
-- Name: permissions_id_seq; Type: SEQUENCE SET; Schema: tickets; Owner: postgres
--

SELECT pg_catalog.setval('tickets.permissions_id_seq', 33, true);


--
-- TOC entry 5452 (class 0 OID 0)
-- Dependencies: 406
-- Name: user_permissions_id_seq; Type: SEQUENCE SET; Schema: tickets; Owner: postgres
--

SELECT pg_catalog.setval('tickets.user_permissions_id_seq', 599, true);


--
-- TOC entry 5284 (class 2606 OID 19373)
-- Name: permissions permissions_code_key; Type: CONSTRAINT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.permissions
    ADD CONSTRAINT permissions_code_key UNIQUE (code);


--
-- TOC entry 5286 (class 2606 OID 19371)
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 5288 (class 2606 OID 19387)
-- Name: user_permissions unique_user_permission; Type: CONSTRAINT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.user_permissions
    ADD CONSTRAINT unique_user_permission UNIQUE (user_id, permission_id);


--
-- TOC entry 5290 (class 2606 OID 19385)
-- Name: user_permissions user_permissions_pkey; Type: CONSTRAINT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.user_permissions
    ADD CONSTRAINT user_permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 5291 (class 2606 OID 19393)
-- Name: user_permissions fk_permission; Type: FK CONSTRAINT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.user_permissions
    ADD CONSTRAINT fk_permission FOREIGN KEY (permission_id) REFERENCES tickets.permissions(id) ON DELETE CASCADE;


--
-- TOC entry 5292 (class 2606 OID 19388)
-- Name: user_permissions fk_user; Type: FK CONSTRAINT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.user_permissions
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES tickets.users(id) ON DELETE CASCADE;


-- Completed on 2026-02-16 10:52:43

--
-- PostgreSQL database dump complete
--

\unrestrict pKbByFqgnLOZn1fq1BSjWl9JrHESljrI4RbRrcevInOPO8XPHhlDtdrYuYDz15u

