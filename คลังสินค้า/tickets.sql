--
-- PostgreSQL database dump
--

\restrict s7LRLCgTHd1WZAEEURdAAdnca4rhkFU87gsVjIwblDlabYKTDwROF24nkORRSSE

-- Dumped from database version 18.0
-- Dumped by pg_dump version 18.0

-- Started on 2026-02-12 10:55:06

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
-- TOC entry 5441 (class 0 OID 0)
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
-- TOC entry 5442 (class 0 OID 0)
-- Dependencies: 406
-- Name: user_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: tickets; Owner: postgres
--

ALTER SEQUENCE tickets.user_permissions_id_seq OWNED BY tickets.user_permissions.id;


--
-- TOC entry 5270 (class 2604 OID 19363)
-- Name: permissions id; Type: DEFAULT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.permissions ALTER COLUMN id SET DEFAULT nextval('tickets.permissions_id_seq'::regclass);


--
-- TOC entry 5272 (class 2604 OID 19378)
-- Name: user_permissions id; Type: DEFAULT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.user_permissions ALTER COLUMN id SET DEFAULT nextval('tickets.user_permissions_id_seq'::regclass);


--
-- TOC entry 5433 (class 0 OID 19360)
-- Dependencies: 405
-- Data for Name: permissions; Type: TABLE DATA; Schema: tickets; Owner: postgres
--

INSERT INTO tickets.permissions VALUES (1, 'index', 'index', 'หน้าแรก', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (2, 'dashboard', 'dashboard', 'หน้า Dashboard', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (3, 'login', 'login', 'เข้าสู่ระบบ', '2026-02-12 09:33:28.694192');
INSERT INTO tickets.permissions VALUES (4, 'logout', 'logout', 'ออกจากระบบ', '2026-02-12 09:33:28.694192');
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
-- TOC entry 5435 (class 0 OID 19375)
-- Dependencies: 407
-- Data for Name: user_permissions; Type: TABLE DATA; Schema: tickets; Owner: postgres
--

INSERT INTO tickets.user_permissions VALUES (1, 1, 11, true, '2026-02-12 02:49:44.061439');
INSERT INTO tickets.user_permissions VALUES (2, 1, 18, true, '2026-02-12 02:49:49.660935');
INSERT INTO tickets.user_permissions VALUES (3, 1, 25, true, '2026-02-12 02:49:55.016684');
INSERT INTO tickets.user_permissions VALUES (4, 1, 15, true, '2026-02-12 02:49:58.380247');
INSERT INTO tickets.user_permissions VALUES (5, 1, 32, true, '2026-02-12 02:50:03.859981');
INSERT INTO tickets.user_permissions VALUES (6, 1, 30, true, '2026-02-12 02:50:13.465514');
INSERT INTO tickets.user_permissions VALUES (7, 1, 16, true, '2026-02-12 02:50:19.600716');
INSERT INTO tickets.user_permissions VALUES (8, 1, 26, true, '2026-02-12 02:50:29.349768');
INSERT INTO tickets.user_permissions VALUES (9, 1, 29, true, '2026-02-12 02:50:39.58142');
INSERT INTO tickets.user_permissions VALUES (10, 1, 20, true, '2026-02-12 02:50:44.229064');
INSERT INTO tickets.user_permissions VALUES (11, 1, 12, true, '2026-02-12 02:50:50.224474');
INSERT INTO tickets.user_permissions VALUES (12, 1, 2, true, '2026-02-12 02:50:55.17953');
INSERT INTO tickets.user_permissions VALUES (13, 1, 28, true, '2026-02-12 02:51:11.666771');
INSERT INTO tickets.user_permissions VALUES (14, 1, 13, true, '2026-02-12 02:51:22.167679');
INSERT INTO tickets.user_permissions VALUES (15, 1, 1, true, '2026-02-12 02:52:18.398');
INSERT INTO tickets.user_permissions VALUES (16, 1, 3, true, '2026-02-12 02:52:26.512645');
INSERT INTO tickets.user_permissions VALUES (17, 1, 4, true, '2026-02-12 02:52:29.993423');
INSERT INTO tickets.user_permissions VALUES (18, 1, 33, true, '2026-02-12 02:52:33.146533');
INSERT INTO tickets.user_permissions VALUES (19, 1, 27, true, '2026-02-12 02:52:43.460276');
INSERT INTO tickets.user_permissions VALUES (20, 1, 14, true, '2026-02-12 02:52:50.480149');
INSERT INTO tickets.user_permissions VALUES (22, 1, 17, true, '2026-02-12 02:53:05.963165');
INSERT INTO tickets.user_permissions VALUES (23, 1, 22, true, '2026-02-12 02:53:11.394041');
INSERT INTO tickets.user_permissions VALUES (24, 1, 23, true, '2026-02-12 02:53:15.990673');
INSERT INTO tickets.user_permissions VALUES (25, 1, 24, true, '2026-02-12 02:53:33.143713');
INSERT INTO tickets.user_permissions VALUES (26, 1, 21, true, '2026-02-12 02:53:58.324622');
INSERT INTO tickets.user_permissions VALUES (27, 1, 31, true, '2026-02-12 02:54:05.972205');
INSERT INTO tickets.user_permissions VALUES (28, 1, 6, true, '2026-02-12 02:54:12.94049');
INSERT INTO tickets.user_permissions VALUES (29, 1, 10, true, '2026-02-12 02:54:18.738612');
INSERT INTO tickets.user_permissions VALUES (30, 1, 8, true, '2026-02-12 02:54:22.571434');
INSERT INTO tickets.user_permissions VALUES (31, 1, 9, true, '2026-02-12 02:54:26.670761');
INSERT INTO tickets.user_permissions VALUES (32, 1, 7, true, '2026-02-12 02:54:29.785893');
INSERT INTO tickets.user_permissions VALUES (33, 1, 5, true, '2026-02-12 02:54:33.868831');
INSERT INTO tickets.user_permissions VALUES (34, 1, 19, true, '2026-02-12 02:54:37.519212');
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
INSERT INTO tickets.user_permissions VALUES (148, 13, 1, true, '2026-02-12 03:19:46.607655');
INSERT INTO tickets.user_permissions VALUES (149, 13, 3, true, '2026-02-12 03:19:46.607919');
INSERT INTO tickets.user_permissions VALUES (150, 13, 4, true, '2026-02-12 03:19:46.608152');
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
INSERT INTO tickets.user_permissions VALUES (167, 12, 11, true, '2026-02-12 03:19:53.345593');
INSERT INTO tickets.user_permissions VALUES (168, 12, 18, true, '2026-02-12 03:19:53.346449');
INSERT INTO tickets.user_permissions VALUES (169, 12, 25, true, '2026-02-12 03:19:53.346798');
INSERT INTO tickets.user_permissions VALUES (170, 12, 15, true, '2026-02-12 03:19:53.347129');
INSERT INTO tickets.user_permissions VALUES (171, 12, 32, true, '2026-02-12 03:19:53.347432');
INSERT INTO tickets.user_permissions VALUES (172, 12, 30, true, '2026-02-12 03:19:53.347724');
INSERT INTO tickets.user_permissions VALUES (173, 12, 16, true, '2026-02-12 03:19:53.348054');
INSERT INTO tickets.user_permissions VALUES (174, 12, 26, true, '2026-02-12 03:19:53.348406');
INSERT INTO tickets.user_permissions VALUES (175, 12, 29, true, '2026-02-12 03:19:53.349329');
INSERT INTO tickets.user_permissions VALUES (176, 12, 20, true, '2026-02-12 03:19:53.350466');
INSERT INTO tickets.user_permissions VALUES (177, 12, 12, true, '2026-02-12 03:19:53.351663');
INSERT INTO tickets.user_permissions VALUES (178, 12, 2, true, '2026-02-12 03:19:53.352878');
INSERT INTO tickets.user_permissions VALUES (179, 12, 28, true, '2026-02-12 03:19:53.353881');
INSERT INTO tickets.user_permissions VALUES (180, 12, 13, true, '2026-02-12 03:19:53.354434');
INSERT INTO tickets.user_permissions VALUES (181, 12, 1, true, '2026-02-12 03:19:53.355303');
INSERT INTO tickets.user_permissions VALUES (182, 12, 3, true, '2026-02-12 03:19:53.356263');
INSERT INTO tickets.user_permissions VALUES (183, 12, 4, true, '2026-02-12 03:19:53.356682');
INSERT INTO tickets.user_permissions VALUES (184, 12, 33, true, '2026-02-12 03:19:53.357187');
INSERT INTO tickets.user_permissions VALUES (185, 12, 27, true, '2026-02-12 03:19:53.357529');
INSERT INTO tickets.user_permissions VALUES (186, 12, 14, true, '2026-02-12 03:19:53.35778');
INSERT INTO tickets.user_permissions VALUES (187, 12, 17, true, '2026-02-12 03:19:53.358024');
INSERT INTO tickets.user_permissions VALUES (188, 12, 22, true, '2026-02-12 03:19:53.358312');
INSERT INTO tickets.user_permissions VALUES (189, 12, 23, true, '2026-02-12 03:19:53.358598');
INSERT INTO tickets.user_permissions VALUES (190, 12, 24, true, '2026-02-12 03:19:53.358836');
INSERT INTO tickets.user_permissions VALUES (191, 12, 21, true, '2026-02-12 03:19:53.35906');
INSERT INTO tickets.user_permissions VALUES (192, 12, 31, true, '2026-02-12 03:19:53.359279');
INSERT INTO tickets.user_permissions VALUES (193, 12, 6, true, '2026-02-12 03:19:53.359493');
INSERT INTO tickets.user_permissions VALUES (194, 12, 10, true, '2026-02-12 03:19:53.359713');
INSERT INTO tickets.user_permissions VALUES (195, 12, 8, true, '2026-02-12 03:19:53.35993');
INSERT INTO tickets.user_permissions VALUES (196, 12, 9, true, '2026-02-12 03:19:53.36023');
INSERT INTO tickets.user_permissions VALUES (197, 12, 7, true, '2026-02-12 03:19:53.360516');
INSERT INTO tickets.user_permissions VALUES (198, 12, 5, true, '2026-02-12 03:19:53.360933');
INSERT INTO tickets.user_permissions VALUES (199, 12, 19, true, '2026-02-12 03:19:53.361197');
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
INSERT INTO tickets.user_permissions VALUES (214, 39, 1, true, '2026-02-12 03:20:51.696914');
INSERT INTO tickets.user_permissions VALUES (215, 39, 3, true, '2026-02-12 03:20:51.697459');
INSERT INTO tickets.user_permissions VALUES (216, 39, 4, true, '2026-02-12 03:20:51.697889');
INSERT INTO tickets.user_permissions VALUES (217, 39, 33, true, '2026-02-12 03:20:51.698571');
INSERT INTO tickets.user_permissions VALUES (218, 39, 27, true, '2026-02-12 03:20:51.69907');
INSERT INTO tickets.user_permissions VALUES (219, 39, 14, true, '2026-02-12 03:20:51.699432');
INSERT INTO tickets.user_permissions VALUES (220, 39, 17, true, '2026-02-12 03:20:51.699724');
INSERT INTO tickets.user_permissions VALUES (221, 39, 22, true, '2026-02-12 03:20:51.700009');
INSERT INTO tickets.user_permissions VALUES (222, 39, 23, true, '2026-02-12 03:20:51.700303');
INSERT INTO tickets.user_permissions VALUES (223, 39, 24, true, '2026-02-12 03:20:51.700631');
INSERT INTO tickets.user_permissions VALUES (224, 39, 21, true, '2026-02-12 03:20:51.700953');
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
INSERT INTO tickets.user_permissions VALUES (247, 11, 1, true, '2026-02-12 03:21:17.880984');
INSERT INTO tickets.user_permissions VALUES (248, 11, 3, true, '2026-02-12 03:21:17.881344');
INSERT INTO tickets.user_permissions VALUES (249, 11, 4, true, '2026-02-12 03:21:17.881567');
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
INSERT INTO tickets.user_permissions VALUES (292, 30, 11, true, '2026-02-12 03:37:57.83767');
INSERT INTO tickets.user_permissions VALUES (293, 30, 18, true, '2026-02-12 03:37:57.839026');
INSERT INTO tickets.user_permissions VALUES (294, 30, 25, true, '2026-02-12 03:37:57.839767');
INSERT INTO tickets.user_permissions VALUES (295, 30, 15, true, '2026-02-12 03:37:57.840732');
INSERT INTO tickets.user_permissions VALUES (296, 30, 16, true, '2026-02-12 03:37:57.841494');
INSERT INTO tickets.user_permissions VALUES (297, 30, 26, true, '2026-02-12 03:37:57.841972');
INSERT INTO tickets.user_permissions VALUES (298, 30, 29, true, '2026-02-12 03:37:57.842507');
INSERT INTO tickets.user_permissions VALUES (299, 30, 20, true, '2026-02-12 03:37:57.842901');
INSERT INTO tickets.user_permissions VALUES (300, 30, 12, true, '2026-02-12 03:37:57.84326');
INSERT INTO tickets.user_permissions VALUES (301, 30, 2, true, '2026-02-12 03:37:57.8436');
INSERT INTO tickets.user_permissions VALUES (302, 30, 28, true, '2026-02-12 03:37:57.844224');
INSERT INTO tickets.user_permissions VALUES (303, 30, 13, true, '2026-02-12 03:37:57.844633');
INSERT INTO tickets.user_permissions VALUES (304, 30, 1, true, '2026-02-12 03:37:57.844979');
INSERT INTO tickets.user_permissions VALUES (305, 30, 3, true, '2026-02-12 03:37:57.84536');
INSERT INTO tickets.user_permissions VALUES (306, 30, 4, true, '2026-02-12 03:37:57.845648');
INSERT INTO tickets.user_permissions VALUES (307, 30, 14, true, '2026-02-12 03:37:57.845925');
INSERT INTO tickets.user_permissions VALUES (308, 30, 17, true, '2026-02-12 03:37:57.846214');
INSERT INTO tickets.user_permissions VALUES (309, 30, 22, true, '2026-02-12 03:37:57.84649');
INSERT INTO tickets.user_permissions VALUES (310, 30, 23, true, '2026-02-12 03:37:57.846715');
INSERT INTO tickets.user_permissions VALUES (311, 30, 24, true, '2026-02-12 03:37:57.846935');
INSERT INTO tickets.user_permissions VALUES (312, 30, 21, true, '2026-02-12 03:37:57.847149');
INSERT INTO tickets.user_permissions VALUES (313, 30, 6, true, '2026-02-12 03:37:57.84746');
INSERT INTO tickets.user_permissions VALUES (314, 30, 10, true, '2026-02-12 03:37:57.84774');
INSERT INTO tickets.user_permissions VALUES (315, 30, 8, true, '2026-02-12 03:37:57.848092');
INSERT INTO tickets.user_permissions VALUES (316, 30, 9, true, '2026-02-12 03:37:57.84844');
INSERT INTO tickets.user_permissions VALUES (317, 30, 7, true, '2026-02-12 03:37:57.849241');
INSERT INTO tickets.user_permissions VALUES (318, 30, 5, true, '2026-02-12 03:37:57.850077');
INSERT INTO tickets.user_permissions VALUES (319, 30, 19, true, '2026-02-12 03:37:57.850476');
INSERT INTO tickets.user_permissions VALUES (320, 29, 11, true, '2026-02-12 03:38:13.449435');
INSERT INTO tickets.user_permissions VALUES (321, 29, 18, true, '2026-02-12 03:38:13.45021');
INSERT INTO tickets.user_permissions VALUES (322, 29, 25, true, '2026-02-12 03:38:13.450683');
INSERT INTO tickets.user_permissions VALUES (323, 29, 15, true, '2026-02-12 03:38:13.451149');
INSERT INTO tickets.user_permissions VALUES (324, 29, 16, true, '2026-02-12 03:38:13.451611');
INSERT INTO tickets.user_permissions VALUES (325, 29, 26, true, '2026-02-12 03:38:13.452123');
INSERT INTO tickets.user_permissions VALUES (326, 29, 29, true, '2026-02-12 03:38:13.45416');
INSERT INTO tickets.user_permissions VALUES (327, 29, 20, true, '2026-02-12 03:38:13.456247');
INSERT INTO tickets.user_permissions VALUES (328, 29, 12, true, '2026-02-12 03:38:13.457505');
INSERT INTO tickets.user_permissions VALUES (329, 29, 28, true, '2026-02-12 03:38:13.457916');
INSERT INTO tickets.user_permissions VALUES (330, 29, 13, true, '2026-02-12 03:38:13.45843');
INSERT INTO tickets.user_permissions VALUES (331, 29, 1, true, '2026-02-12 03:38:13.458841');
INSERT INTO tickets.user_permissions VALUES (332, 29, 3, true, '2026-02-12 03:38:13.459229');
INSERT INTO tickets.user_permissions VALUES (333, 29, 4, true, '2026-02-12 03:38:13.459663');
INSERT INTO tickets.user_permissions VALUES (334, 29, 14, true, '2026-02-12 03:38:13.460066');
INSERT INTO tickets.user_permissions VALUES (335, 29, 17, true, '2026-02-12 03:38:13.460398');
INSERT INTO tickets.user_permissions VALUES (336, 29, 22, true, '2026-02-12 03:38:13.461032');
INSERT INTO tickets.user_permissions VALUES (337, 29, 23, true, '2026-02-12 03:38:13.461507');
INSERT INTO tickets.user_permissions VALUES (338, 29, 24, true, '2026-02-12 03:38:13.461912');
INSERT INTO tickets.user_permissions VALUES (339, 29, 21, true, '2026-02-12 03:38:13.462294');
INSERT INTO tickets.user_permissions VALUES (340, 29, 6, true, '2026-02-12 03:38:13.462643');
INSERT INTO tickets.user_permissions VALUES (341, 29, 10, true, '2026-02-12 03:38:13.462972');
INSERT INTO tickets.user_permissions VALUES (342, 29, 8, true, '2026-02-12 03:38:13.463341');
INSERT INTO tickets.user_permissions VALUES (343, 29, 9, true, '2026-02-12 03:38:13.463685');
INSERT INTO tickets.user_permissions VALUES (344, 29, 7, true, '2026-02-12 03:38:13.464145');
INSERT INTO tickets.user_permissions VALUES (345, 29, 5, true, '2026-02-12 03:38:13.464652');
INSERT INTO tickets.user_permissions VALUES (346, 29, 19, true, '2026-02-12 03:38:13.464969');


--
-- TOC entry 5443 (class 0 OID 0)
-- Dependencies: 404
-- Name: permissions_id_seq; Type: SEQUENCE SET; Schema: tickets; Owner: postgres
--

SELECT pg_catalog.setval('tickets.permissions_id_seq', 33, true);


--
-- TOC entry 5444 (class 0 OID 0)
-- Dependencies: 406
-- Name: user_permissions_id_seq; Type: SEQUENCE SET; Schema: tickets; Owner: postgres
--

SELECT pg_catalog.setval('tickets.user_permissions_id_seq', 349, true);


--
-- TOC entry 5276 (class 2606 OID 19373)
-- Name: permissions permissions_code_key; Type: CONSTRAINT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.permissions
    ADD CONSTRAINT permissions_code_key UNIQUE (code);


--
-- TOC entry 5278 (class 2606 OID 19371)
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 5280 (class 2606 OID 19387)
-- Name: user_permissions unique_user_permission; Type: CONSTRAINT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.user_permissions
    ADD CONSTRAINT unique_user_permission UNIQUE (user_id, permission_id);


--
-- TOC entry 5282 (class 2606 OID 19385)
-- Name: user_permissions user_permissions_pkey; Type: CONSTRAINT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.user_permissions
    ADD CONSTRAINT user_permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 5283 (class 2606 OID 19393)
-- Name: user_permissions fk_permission; Type: FK CONSTRAINT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.user_permissions
    ADD CONSTRAINT fk_permission FOREIGN KEY (permission_id) REFERENCES tickets.permissions(id) ON DELETE CASCADE;


--
-- TOC entry 5284 (class 2606 OID 19388)
-- Name: user_permissions fk_user; Type: FK CONSTRAINT; Schema: tickets; Owner: postgres
--

ALTER TABLE ONLY tickets.user_permissions
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES tickets.users(id) ON DELETE CASCADE;


-- Completed on 2026-02-12 10:55:06

--
-- PostgreSQL database dump complete
--

\unrestrict s7LRLCgTHd1WZAEEURdAAdnca4rhkFU87gsVjIwblDlabYKTDwROF24nkORRSSE

