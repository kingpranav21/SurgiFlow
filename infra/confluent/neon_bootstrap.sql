--
-- PostgreSQL database dump
--


-- Dumped from database version 16.14 (Homebrew)
-- Dumped by pg_dump version 16.14 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.shipments DROP CONSTRAINT IF EXISTS shipments_supplier_id_fkey;
ALTER TABLE IF EXISTS ONLY public.shipments DROP CONSTRAINT IF EXISTS shipments_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.shipments DROP CONSTRAINT IF EXISTS shipments_hospital_id_fkey;
ALTER TABLE IF EXISTS ONLY public.procedures DROP CONSTRAINT IF EXISTS procedures_hospital_id_fkey;
ALTER TABLE IF EXISTS ONLY public.procedure_requirements DROP CONSTRAINT IF EXISTS procedure_requirements_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.orders DROP CONSTRAINT IF EXISTS orders_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.orders DROP CONSTRAINT IF EXISTS orders_hospital_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS inventory_product_id_fkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS inventory_hospital_id_fkey;
DROP INDEX IF EXISTS public.idx_shipments_status;
DROP INDEX IF EXISTS public.idx_risk_created;
DROP INDEX IF EXISTS public.idx_procedures_hospital;
DROP INDEX IF EXISTS public.idx_inventory_product;
ALTER TABLE IF EXISTS ONLY public.suppliers DROP CONSTRAINT IF EXISTS suppliers_pkey;
ALTER TABLE IF EXISTS ONLY public.shipments DROP CONSTRAINT IF EXISTS shipments_pkey;
ALTER TABLE IF EXISTS ONLY public.risk_predictions DROP CONSTRAINT IF EXISTS risk_predictions_pkey;
ALTER TABLE IF EXISTS ONLY public.recommendations DROP CONSTRAINT IF EXISTS recommendations_pkey;
ALTER TABLE IF EXISTS ONLY public.products DROP CONSTRAINT IF EXISTS products_pkey;
ALTER TABLE IF EXISTS ONLY public.procedures DROP CONSTRAINT IF EXISTS procedures_pkey;
ALTER TABLE IF EXISTS ONLY public.procedure_requirements DROP CONSTRAINT IF EXISTS procedure_requirements_pkey;
ALTER TABLE IF EXISTS ONLY public.orders DROP CONSTRAINT IF EXISTS orders_pkey;
ALTER TABLE IF EXISTS ONLY public.inventory DROP CONSTRAINT IF EXISTS inventory_pkey;
ALTER TABLE IF EXISTS ONLY public.hospitals DROP CONSTRAINT IF EXISTS hospitals_pkey;
ALTER TABLE IF EXISTS public.risk_predictions ALTER COLUMN prediction_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.recommendations ALTER COLUMN recommendation_id DROP DEFAULT;
DROP TABLE IF EXISTS public.suppliers;
DROP TABLE IF EXISTS public.shipments;
DROP SEQUENCE IF EXISTS public.risk_predictions_prediction_id_seq;
DROP TABLE IF EXISTS public.risk_predictions;
DROP SEQUENCE IF EXISTS public.recommendations_recommendation_id_seq;
DROP TABLE IF EXISTS public.recommendations;
DROP TABLE IF EXISTS public.products;
DROP TABLE IF EXISTS public.procedures;
DROP TABLE IF EXISTS public.procedure_requirements;
DROP TABLE IF EXISTS public.orders;
DROP TABLE IF EXISTS public.inventory;
DROP TABLE IF EXISTS public.hospitals;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: hospitals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hospitals (
    hospital_id character varying(50) NOT NULL,
    name character varying(255) NOT NULL,
    city character varying(100),
    state character varying(100)
);


--
-- Name: inventory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory (
    hospital_id character varying(50) NOT NULL,
    product_id character varying(50) NOT NULL,
    quantity integer NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.orders (
    order_id character varying(50) NOT NULL,
    hospital_id character varying(50),
    product_id character varying(50),
    quantity integer,
    status character varying(50),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: procedure_requirements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.procedure_requirements (
    procedure_type character varying(100) NOT NULL,
    product_id character varying(50) NOT NULL,
    quantity_per_procedure integer
);


--
-- Name: procedures; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.procedures (
    procedure_id character varying(50) NOT NULL,
    hospital_id character varying(50),
    procedure_type character varying(100),
    scheduled_time timestamp without time zone,
    status character varying(50)
);


--
-- Name: products; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.products (
    product_id character varying(50) NOT NULL,
    name character varying(255) NOT NULL,
    category character varying(100),
    unit_cost numeric(12,2),
    safety_stock integer DEFAULT 0
);


--
-- Name: recommendations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recommendations (
    recommendation_id bigint NOT NULL,
    source_hospital_id character varying(50),
    target_hospital_id character varying(50),
    product_id character varying(50),
    quantity integer,
    reason text,
    status character varying(30) DEFAULT 'PENDING'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: recommendations_recommendation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.recommendations_recommendation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: recommendations_recommendation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.recommendations_recommendation_id_seq OWNED BY public.recommendations.recommendation_id;


--
-- Name: risk_predictions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.risk_predictions (
    prediction_id bigint NOT NULL,
    hospital_id character varying(50),
    product_id character varying(50),
    risk_level character varying(20),
    current_inventory integer,
    projected_demand integer,
    projected_inventory integer,
    predicted_stockout timestamp without time zone,
    reason text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: risk_predictions_prediction_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.risk_predictions_prediction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: risk_predictions_prediction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.risk_predictions_prediction_id_seq OWNED BY public.risk_predictions.prediction_id;


--
-- Name: shipments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shipments (
    shipment_id character varying(50) NOT NULL,
    supplier_id character varying(50),
    hospital_id character varying(50),
    product_id character varying(50),
    quantity integer,
    status character varying(50),
    expected_delivery timestamp without time zone,
    delay_hours integer DEFAULT 0,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: suppliers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.suppliers (
    supplier_id character varying(50) NOT NULL,
    name character varying(255),
    reliability_score numeric(5,2)
);


--
-- Name: recommendations recommendation_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recommendations ALTER COLUMN recommendation_id SET DEFAULT nextval('public.recommendations_recommendation_id_seq'::regclass);


--
-- Name: risk_predictions prediction_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_predictions ALTER COLUMN prediction_id SET DEFAULT nextval('public.risk_predictions_prediction_id_seq'::regclass);


--
-- Data for Name: hospitals; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.hospitals (hospital_id, name, city, state) FROM stdin;
H001	Mumbai Central Surgical	Mumbai	MH
H002	Pune Medical Center	Pune	MH
H003	Delhi Surgical Hub	Delhi	DL
H004	Mumbai West Specialty	Mumbai	MH
H005	Bengaluru Care Hospital	Bengaluru	KA
H006	Hyderabad Ortho Center	Hyderabad	TS
H007	Chennai Procedure Wing	Chennai	TN
H008	Ahmedabad MedSupply Hub	Ahmedabad	GJ
H009	Kolkata Surgical Network	Kolkata	WB
H010	Jaipur Care Alliance	Jaipur	RJ
H011	Kochi Coastal Medical	Kochi	KL
H012	Chandigarh North Clinic	Chandigarh	CH
\.


--
-- Data for Name: inventory; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inventory (hospital_id, product_id, quantity, updated_at) FROM stdin;
H001	STAPLER-01	9	2026-09-22 14:40:48.472218
H002	SPEC-BAG	25	2026-09-22 14:40:48.472218
H001	TROC-5	29	2026-09-22 15:48:46.81191
H005	SUTURE-01	25	2026-09-22 14:40:48.472218
H006	SPEC-BAG	25	2026-09-22 14:40:48.472218
H007	SUTURE-01	25	2026-09-22 14:40:48.472218
H007	MESH-01	25	2026-09-22 14:40:48.472218
H009	SUTURE-01	25	2026-09-22 14:40:48.472218
H009	SPEC-BAG	25	2026-09-22 14:40:48.472218
H010	TROC-5	25	2026-09-22 14:40:48.472218
H011	IRRI-01	25	2026-09-22 14:40:48.472218
H002	TROC-5	23	2026-09-22 16:06:13.56965
H005	TROC-5	23	2026-09-22 16:20:00.703868
H005	STAPLER-01	24	2026-09-22 16:01:21.643048
H001	SUTURE-01	23	2026-09-22 15:09:31.236983
H004	SUTURE-01	21	2026-09-22 16:20:36.019592
H009	ELEC-HOOK	23	2026-09-22 15:49:27.052273
H007	STAPLER-01	23	2026-09-22 15:30:49.792658
H005	CLIP-CART	21	2026-09-22 16:05:38.376643
H002	IRRI-01	22	2026-09-22 16:07:34.035577
H002	GRASP-01	23	2026-09-22 16:14:13.307414
H002	SCOPE-01	24	2026-09-22 14:44:37.511672
H008	STAPLER-01	19	2026-09-22 15:59:41.07572
H011	GRASP-01	21	2026-09-22 15:46:25.900042
H004	MESH-01	23	2026-09-22 15:13:43.13573
H001	GRASP-01	24	2026-09-22 14:45:52.995321
H001	SCOPE-01	23	2026-09-22 16:05:58.489667
H010	STAPLER-01	21	2026-09-22 15:33:05.749601
H003	TROC-5	22	2026-09-22 15:59:46.112975
H009	TROC-5	24	2026-09-22 16:09:14.672549
H004	CATH-01	24	2026-09-22 15:16:54.425523
H011	SPEC-BAG	19	2026-09-22 16:00:11.25578
H003	IRRI-01	23	2026-09-22 16:19:50.638489
H009	STAPLER-01	22	2026-09-22 15:51:47.872135
H005	ELEC-HOOK	18	2026-09-22 16:13:58.211217
H005	TROC-10	22	2026-09-22 16:16:24.659884
H004	STAPLER-01	19	2026-09-22 16:18:20.238205
H003	SPEC-BAG	21	2026-09-22 16:20:10.775187
H002	TROC-10	21	2026-09-22 15:55:09.281998
H012	SUTURE-01	24	2026-09-22 15:46:56.09041
H012	TROC-10	22	2026-09-22 15:24:12.236249
H008	TROC-5	24	2026-09-22 15:57:15.07483
H010	GRASP-01	22	2026-09-22 16:07:59.181995
H004	GRASP-01	20	2026-09-22 16:14:18.32579
H006	CLIP-CART	23	2026-09-22 15:18:04.827073
H008	MESH-01	24	2026-09-22 15:54:08.884221
H012	CLIP-CART	23	2026-09-22 15:59:36.035734
H001	SPEC-BAG	21	2026-09-22 15:41:43.955507
H010	SUTURE-01	24	2026-09-22 15:34:01.065785
H004	SPEC-BAG	19	2026-09-22 16:04:38.010883
H004	TROC-5	23	2026-09-22 16:20:41.051857
H010	CATH-01	24	2026-09-22 15:31:25.102164
H007	ELEC-HOOK	22	2026-09-22 15:46:20.874029
H005	IRRI-01	22	2026-09-22 14:58:17.558146
H001	TROC-10	26	2026-09-22 15:59:10.883234
H010	SPEC-BAG	22	2026-09-22 15:49:42.146572
H005	SPEC-BAG	24	2026-09-22 14:55:51.845556
H002	MESH-01	24	2026-09-22 15:29:34.300363
H008	CATH-01	23	2026-09-22 15:07:10.504465
H006	ELEC-HOOK	23	2026-09-22 15:53:38.687539
H010	CLIP-CART	23	2026-09-22 14:57:32.318557
H011	SUTURE-01	21	2026-09-22 16:15:48.823952
H005	GRASP-01	23	2026-09-22 15:41:33.906789
H006	GRASP-01	23	2026-09-22 16:03:42.497931
H003	GRASP-01	20	2026-09-22 16:12:17.53705
H011	SCOPE-01	24	2026-09-22 15:18:19.93714
H003	SUTURE-01	20	2026-09-22 16:18:05.181819
H002	CLIP-CART	23	2026-09-22 15:54:44.132881
H006	STAPLER-01	21	2026-09-22 15:49:11.949623
H008	ELEC-HOOK	23	2026-09-22 15:28:03.749679
H002	CATH-01	21	2026-09-22 16:07:49.139966
H008	SPEC-BAG	22	2026-09-22 15:56:59.969057
H004	TROC-10	22	2026-09-22 15:52:13.14156
H001	IRRI-01	20	2026-09-22 16:13:22.990034
H011	CLIP-CART	23	2026-09-22 15:38:17.643521
H007	SCOPE-01	24	2026-09-22 15:04:59.828326
H008	CLIP-CART	23	2026-09-22 15:06:20.267706
H008	IRRI-01	21	2026-09-22 16:13:33.047643
H011	ELEC-HOOK	21	2026-09-22 16:02:21.977159
H006	TROC-5	23	2026-09-22 15:09:26.184551
H006	SCOPE-01	20	2026-09-22 15:58:15.515859
H009	IRRI-01	23	2026-09-22 15:11:27.177352
H007	TROC-10	19	2026-09-22 15:59:00.820739
H011	CATH-01	23	2026-09-22 16:20:15.923243
H009	SCOPE-01	22	2026-09-22 16:11:17.175245
H006	MESH-01	22	2026-09-22 15:56:34.822543
H007	CLIP-CART	23	2026-09-22 15:13:58.235864
H003	CLIP-CART	24	2026-09-22 15:35:56.815545
H010	TROC-10	24	2026-09-22 16:08:14.2582
H006	SUTURE-01	20	2026-09-22 16:02:27.027751
H001	CLIP-CART	21	2026-09-22 16:14:53.47538
H007	IRRI-01	24	2026-09-22 15:28:59.069206
H006	IRRI-01	20	2026-09-22 16:15:43.794616
H001	CATH-01	20	2026-09-22 16:16:54.793393
H005	CATH-01	21	2026-09-22 16:00:41.425516
H007	TROC-5	21	2026-09-22 15:58:20.540642
H003	SCOPE-01	20	2026-09-22 16:11:47.356333
H003	STAPLER-01	24	2026-09-22 15:26:13.083143
H007	SPEC-BAG	20	2026-09-22 15:50:57.578146
H009	CATH-01	22	2026-09-22 15:55:59.620507
H005	MESH-01	24	2026-09-22 15:41:18.805637
H011	TROC-10	24	2026-09-22 15:43:44.741365
H011	MESH-01	20	2026-09-22 16:12:57.739298
H002	STAPLER-01	22	2026-09-22 15:31:50.245471
H011	TROC-5	18	2026-09-22 16:18:10.203863
H009	GRASP-01	23	2026-09-22 15:36:21.988636
H007	CATH-01	20	2026-09-22 15:42:24.268342
H006	CATH-01	23	2026-09-22 16:10:57.077464
H003	MESH-01	23	2026-09-22 15:44:35.061982
H004	CLIP-CART	22	2026-09-22 15:40:48.65722
H009	MESH-01	20	2026-09-22 16:03:07.2736
H008	SUTURE-01	22	2026-09-22 15:45:05.256223
H004	SCOPE-01	19	2026-09-22 15:42:44.367662
H008	GRASP-01	24	2026-09-22 15:43:49.781734
H006	TROC-10	19	2026-09-22 15:43:54.807688
H005	SCOPE-01	19	2026-09-22 16:11:42.329357
H009	CLIP-CART	24	2026-09-22 15:47:06.160936
H012	TROC-5	21	2026-09-22 16:07:54.158441
H010	ELEC-HOOK	22	2026-09-22 15:48:51.842769
H008	SCOPE-01	24	2026-09-22 16:03:22.37987
H010	IRRI-01	22	2026-09-22 16:07:18.93188
H003	ELEC-HOOK	22	2026-09-22 16:12:52.721087
H009	TROC-10	21	2026-09-22 16:01:51.817618
H012	STAPLER-01	20	2026-09-22 16:03:27.409556
H003	CATH-01	22	2026-09-22 16:07:13.901347
H004	IRRI-01	21	2026-09-22 16:08:19.291895
H011	STAPLER-01	20	2026-09-22 16:18:35.283409
H007	GRASP-01	22	2026-09-22 16:16:59.81257
H012	GRASP-01	22	2026-09-22 15:20:00.609466
H008	TROC-10	20	2026-09-22 15:27:08.436099
H012	SPEC-BAG	22	2026-09-22 15:39:23.097524
H012	IRRI-01	22	2026-09-22 15:54:59.234118
H012	ELEC-HOOK	24	2026-09-22 15:55:29.409006
H001	MESH-01	20	2026-09-22 16:03:37.467746
H012	MESH-01	21	2026-09-22 16:08:09.224948
H012	CATH-01	20	2026-09-22 16:15:18.674095
H012	SCOPE-01	21	2026-09-22 16:17:19.937673
H001	ELEC-HOOK	20	2026-09-22 16:20:51.087913
H010	SCOPE-01	18	2026-09-22 15:35:21.586474
H004	ELEC-HOOK	22	2026-09-22 15:48:56.871832
H003	TROC-10	22	2026-09-22 15:55:49.557801
H010	MESH-01	19	2026-09-22 16:05:18.247698
H002	ELEC-HOOK	21	2026-09-22 16:09:19.707941
H002	SUTURE-01	20	2026-09-22 16:14:03.239106
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.orders (order_id, hospital_id, product_id, quantity, status, created_at) FROM stdin;
ORD9821	H001	STAPLER-01	50	PLACED	2026-09-20 14:40:48.472218
\.


--
-- Data for Name: procedure_requirements; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.procedure_requirements (procedure_type, product_id, quantity_per_procedure) FROM stdin;
LAPAROSCOPIC_CHOLECYSTECTOMY	TROC-10	2
LAPAROSCOPIC_CHOLECYSTECTOMY	TROC-5	2
LAPAROSCOPIC_CHOLECYSTECTOMY	CLIP-CART	1
LAPAROSCOPIC_CHOLECYSTECTOMY	SUTURE-01	2
LAPAROSCOPIC_CHOLECYSTECTOMY	SPEC-BAG	1
LAPAROSCOPIC_CHOLECYSTECTOMY	STAPLER-01	1
APPENDECTOMY	TROC-10	1
APPENDECTOMY	TROC-5	2
APPENDECTOMY	CLIP-CART	1
APPENDECTOMY	SUTURE-01	2
HERNIA_REPAIR	MESH-01	1
HERNIA_REPAIR	SUTURE-01	3
HERNIA_REPAIR	TROC-5	1
ARTHROSCOPY	CATH-01	1
ARTHROSCOPY	IRRI-01	2
ARTHROSCOPY	SCOPE-01	1
\.


--
-- Data for Name: procedures; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.procedures (procedure_id, hospital_id, procedure_type, scheduled_time, status) FROM stdin;
P8801	H001	LAPAROSCOPIC_CHOLECYSTECTOMY	2026-09-23 13:10:48.472218	SCHEDULED
P8802	H001	LAPAROSCOPIC_CHOLECYSTECTOMY	2026-09-23 13:40:48.472218	SCHEDULED
P8803	H001	LAPAROSCOPIC_CHOLECYSTECTOMY	2026-09-23 14:10:48.472218	SCHEDULED
P8804	H001	LAPAROSCOPIC_CHOLECYSTECTOMY	2026-09-23 14:40:48.472218	SCHEDULED
P8805	H001	LAPAROSCOPIC_CHOLECYSTECTOMY	2026-09-23 15:10:48.472218	SCHEDULED
P8806	H001	LAPAROSCOPIC_CHOLECYSTECTOMY	2026-09-23 15:40:48.472218	SCHEDULED
P8807	H001	LAPAROSCOPIC_CHOLECYSTECTOMY	2026-09-23 16:10:48.472218	SCHEDULED
P9901	H005	ARTHROSCOPY	2026-09-23 14:40:48.472218	SCHEDULED
P9902	H003	HERNIA_REPAIR	2026-09-24 14:40:48.472218	SCHEDULED
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.products (product_id, name, category, unit_cost, safety_stock) FROM stdin;
STAPLER-01	Endoscopic Stapler	Stapling	4200.00	8
TROC-10	Trocar 10mm	Access	850.00	10
TROC-5	Trocar 5mm	Access	650.00	10
CLIP-CART	Clip Cartridge	Clipping	1200.00	6
SUTURE-01	Absorbable Suture Pack	Closure	180.00	20
SPEC-BAG	Specimen Retrieval Bag	Retrieval	320.00	8
CATH-01	Surgical Catheter Set	Accessories	210.00	12
MESH-01	Hernia Mesh Sheet	Implants	2400.00	5
SCOPE-01	Laparoscope Lens Cover	Optics	95.00	15
IRRI-01	Irrigation Tubing Kit	Fluid	140.00	12
ELEC-HOOK	Electrocautery Hook	Energy	780.00	6
GRASP-01	Grasping Forceps Tip	Instruments	560.00	8
SKU-013	Surgical SKU 13	General	230.00	5
SKU-014	Surgical SKU 14	General	240.00	5
SKU-015	Surgical SKU 15	General	250.00	5
SKU-016	Surgical SKU 16	General	260.00	5
SKU-017	Surgical SKU 17	General	270.00	5
SKU-018	Surgical SKU 18	General	280.00	5
SKU-019	Surgical SKU 19	General	290.00	5
SKU-020	Surgical SKU 20	General	300.00	5
SKU-021	Surgical SKU 21	General	310.00	5
SKU-022	Surgical SKU 22	General	320.00	5
SKU-023	Surgical SKU 23	General	330.00	5
SKU-024	Surgical SKU 24	General	340.00	5
SKU-025	Surgical SKU 25	General	350.00	5
SKU-026	Surgical SKU 26	General	360.00	5
SKU-027	Surgical SKU 27	General	370.00	5
SKU-028	Surgical SKU 28	General	380.00	5
SKU-029	Surgical SKU 29	General	390.00	5
SKU-030	Surgical SKU 30	General	400.00	5
SKU-031	Surgical SKU 31	General	410.00	5
SKU-032	Surgical SKU 32	General	420.00	5
SKU-033	Surgical SKU 33	General	430.00	5
SKU-034	Surgical SKU 34	General	440.00	5
SKU-035	Surgical SKU 35	General	450.00	5
SKU-036	Surgical SKU 36	General	460.00	5
SKU-037	Surgical SKU 37	General	470.00	5
SKU-038	Surgical SKU 38	General	480.00	5
SKU-039	Surgical SKU 39	General	490.00	5
SKU-040	Surgical SKU 40	General	500.00	5
\.


--
-- Data for Name: recommendations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.recommendations (recommendation_id, source_hospital_id, target_hospital_id, product_id, quantity, reason, status, created_at) FROM stdin;
512	H004	H001	STAPLER-01	8	H001 predicted shortage; H004 has surplus of 11	PENDING	2026-09-22 16:21:26.157153
\.


--
-- Data for Name: risk_predictions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.risk_predictions (prediction_id, hospital_id, product_id, risk_level, current_inventory, projected_demand, projected_inventory, predicted_stockout, reason, created_at) FROM stdin;
308161	H001	STAPLER-01	HIGH	9	13	-4	\N	7 units driven by scheduled procedures. Incoming shipment delayed by 18 hours. Projected shortfall of 4 units	2026-09-22 16:21:26.157153
308162	H002	SPEC-BAG	LOW	25	6	19	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308163	H001	TROC-5	MEDIUM	29	20	9	\N	14 units driven by scheduled procedures	2026-09-22 16:21:26.157153
308164	H005	SUTURE-01	MEDIUM	25	6	19	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308165	H006	SPEC-BAG	LOW	25	6	19	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308166	H007	SUTURE-01	MEDIUM	25	6	19	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308167	H007	MESH-01	LOW	25	6	19	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308168	H009	SUTURE-01	MEDIUM	25	6	19	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308169	H009	SPEC-BAG	LOW	25	6	19	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308170	H010	TROC-5	LOW	25	6	19	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308171	H011	IRRI-01	LOW	25	6	19	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308172	H002	TROC-5	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308173	H005	TROC-5	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308174	H005	STAPLER-01	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308175	H001	SUTURE-01	MEDIUM	23	20	3	\N	14 units driven by scheduled procedures	2026-09-22 16:21:26.157153
308176	H004	SUTURE-01	MEDIUM	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308177	H009	ELEC-HOOK	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308178	H007	STAPLER-01	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308179	H005	CLIP-CART	LOW	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308180	H002	IRRI-01	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308181	H002	GRASP-01	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308182	H002	SCOPE-01	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308183	H008	STAPLER-01	LOW	19	6	13	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308184	H011	GRASP-01	LOW	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308185	H004	MESH-01	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308186	H001	GRASP-01	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308187	H001	SCOPE-01	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308188	H010	STAPLER-01	LOW	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308189	H003	TROC-5	LOW	22	7	15	\N	1 units driven by scheduled procedures	2026-09-22 16:21:26.157153
308190	H009	TROC-5	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308191	H004	CATH-01	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308192	H011	SPEC-BAG	LOW	19	6	13	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308193	H003	IRRI-01	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308194	H009	STAPLER-01	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308195	H005	ELEC-HOOK	LOW	18	6	12	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308196	H005	TROC-10	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308197	H004	STAPLER-01	LOW	19	6	13	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308198	H003	SPEC-BAG	LOW	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308199	H002	TROC-10	LOW	21	6	55	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308200	H012	SUTURE-01	MEDIUM	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308201	H012	TROC-10	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308202	H008	TROC-5	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308203	H010	GRASP-01	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308204	H004	GRASP-01	LOW	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308205	H006	CLIP-CART	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308206	H008	MESH-01	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308207	H012	CLIP-CART	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308208	H001	SPEC-BAG	LOW	21	13	8	\N	7 units driven by scheduled procedures	2026-09-22 16:21:26.157153
308209	H010	SUTURE-01	MEDIUM	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308210	H004	SPEC-BAG	LOW	19	6	13	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308211	H004	TROC-5	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308212	H010	CATH-01	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308213	H007	ELEC-HOOK	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308214	H005	IRRI-01	LOW	22	8	14	\N	2 units driven by scheduled procedures	2026-09-22 16:21:26.157153
308215	H001	TROC-10	MEDIUM	26	20	6	\N	14 units driven by scheduled procedures	2026-09-22 16:21:26.157153
308216	H010	SPEC-BAG	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308217	H005	SPEC-BAG	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308218	H002	MESH-01	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308219	H008	CATH-01	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308220	H006	ELEC-HOOK	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308221	H010	CLIP-CART	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308222	H011	SUTURE-01	MEDIUM	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308223	H005	GRASP-01	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308224	H006	GRASP-01	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308225	H003	GRASP-01	LOW	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308226	H011	SCOPE-01	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308227	H003	SUTURE-01	MEDIUM	20	9	11	\N	3 units driven by scheduled procedures	2026-09-22 16:21:26.157153
308228	H002	CLIP-CART	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308229	H006	STAPLER-01	LOW	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308230	H008	ELEC-HOOK	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308231	H002	CATH-01	LOW	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308232	H008	SPEC-BAG	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308233	H004	TROC-10	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308234	H001	IRRI-01	LOW	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308235	H011	CLIP-CART	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308236	H007	SCOPE-01	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308237	H008	CLIP-CART	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308238	H008	IRRI-01	LOW	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308239	H011	ELEC-HOOK	LOW	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308240	H006	TROC-5	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308241	H006	SCOPE-01	MEDIUM	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308242	H009	IRRI-01	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308243	H007	TROC-10	LOW	19	6	13	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308244	H011	CATH-01	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308245	H009	SCOPE-01	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308246	H006	MESH-01	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308247	H007	CLIP-CART	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308248	H003	CLIP-CART	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308249	H010	TROC-10	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308250	H006	SUTURE-01	MEDIUM	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308251	H001	CLIP-CART	LOW	21	13	8	\N	7 units driven by scheduled procedures	2026-09-22 16:21:26.157153
308252	H007	IRRI-01	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308253	H006	IRRI-01	LOW	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308254	H001	CATH-01	LOW	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308255	H005	CATH-01	LOW	21	7	14	\N	1 units driven by scheduled procedures	2026-09-22 16:21:26.157153
308256	H007	TROC-5	LOW	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308257	H003	SCOPE-01	MEDIUM	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308258	H003	STAPLER-01	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308259	H007	SPEC-BAG	LOW	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308260	H009	CATH-01	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308261	H005	MESH-01	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308262	H011	TROC-10	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308263	H011	MESH-01	LOW	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308264	H002	STAPLER-01	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308265	H011	TROC-5	LOW	18	6	12	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308266	H009	GRASP-01	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308267	H007	CATH-01	LOW	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308268	H006	CATH-01	LOW	23	6	17	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308269	H003	MESH-01	LOW	23	7	16	\N	1 units driven by scheduled procedures	2026-09-22 16:21:26.157153
308270	H004	CLIP-CART	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308271	H009	MESH-01	LOW	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308272	H008	SUTURE-01	MEDIUM	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308273	H004	SCOPE-01	MEDIUM	19	6	13	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308274	H008	GRASP-01	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308275	H006	TROC-10	LOW	19	6	13	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308276	H005	SCOPE-01	MEDIUM	19	7	12	\N	1 units driven by scheduled procedures	2026-09-22 16:21:26.157153
308277	H009	CLIP-CART	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308278	H012	TROC-5	LOW	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308279	H010	ELEC-HOOK	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308280	H008	SCOPE-01	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308281	H010	IRRI-01	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308282	H003	ELEC-HOOK	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308283	H009	TROC-10	LOW	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308284	H012	STAPLER-01	LOW	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308285	H003	CATH-01	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308286	H004	IRRI-01	LOW	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308287	H011	STAPLER-01	LOW	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308288	H007	GRASP-01	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308289	H012	GRASP-01	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308290	H008	TROC-10	LOW	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308291	H012	SPEC-BAG	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308292	H012	IRRI-01	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308293	H012	ELEC-HOOK	LOW	24	6	18	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308294	H001	MESH-01	LOW	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308295	H012	MESH-01	LOW	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308296	H012	CATH-01	LOW	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308297	H012	SCOPE-01	LOW	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308298	H001	ELEC-HOOK	LOW	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308299	H010	SCOPE-01	MEDIUM	18	6	12	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308300	H004	ELEC-HOOK	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308301	H003	TROC-10	LOW	22	6	16	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308302	H010	MESH-01	LOW	19	6	13	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308303	H002	ELEC-HOOK	LOW	21	6	15	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
308304	H002	SUTURE-01	MEDIUM	20	6	14	\N	Supply coverage within safety stock	2026-09-22 16:21:26.157153
\.


--
-- Data for Name: shipments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.shipments (shipment_id, supplier_id, hospital_id, product_id, quantity, status, expected_delivery, delay_hours, updated_at) FROM stdin;
SHP201	SUP07	H002	TROC-10	40	IN_TRANSIT	2026-09-23 02:40:48.472218	0	2026-09-22 14:40:48.472218
SHP182	SUP12	H001	STAPLER-01	50	DELAYED	2026-09-24 04:40:48.472218	18	2026-09-22 15:57:05.970464
\.


--
-- Data for Name: suppliers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.suppliers (supplier_id, name, reliability_score) FROM stdin;
SUP12	MedDevice Logistics India	0.91
SUP03	OrthoStream Distributors	0.88
SUP07	AccessPort Supply Co	0.94
SUP01	ClipTech Regional	0.86
SUP09	SutureLink Partners	0.92
\.


--
-- Name: recommendations_recommendation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.recommendations_recommendation_id_seq', 512, true);


--
-- Name: risk_predictions_prediction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.risk_predictions_prediction_id_seq', 308304, true);


--
-- Name: hospitals hospitals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hospitals
    ADD CONSTRAINT hospitals_pkey PRIMARY KEY (hospital_id);


--
-- Name: inventory inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_pkey PRIMARY KEY (hospital_id, product_id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (order_id);


--
-- Name: procedure_requirements procedure_requirements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.procedure_requirements
    ADD CONSTRAINT procedure_requirements_pkey PRIMARY KEY (procedure_type, product_id);


--
-- Name: procedures procedures_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.procedures
    ADD CONSTRAINT procedures_pkey PRIMARY KEY (procedure_id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (product_id);


--
-- Name: recommendations recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_pkey PRIMARY KEY (recommendation_id);


--
-- Name: risk_predictions risk_predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_predictions
    ADD CONSTRAINT risk_predictions_pkey PRIMARY KEY (prediction_id);


--
-- Name: shipments shipments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT shipments_pkey PRIMARY KEY (shipment_id);


--
-- Name: suppliers suppliers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT suppliers_pkey PRIMARY KEY (supplier_id);


--
-- Name: idx_inventory_product; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_inventory_product ON public.inventory USING btree (product_id);


--
-- Name: idx_procedures_hospital; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_procedures_hospital ON public.procedures USING btree (hospital_id);


--
-- Name: idx_risk_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_risk_created ON public.risk_predictions USING btree (created_at DESC);


--
-- Name: idx_shipments_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_shipments_status ON public.shipments USING btree (status);


--
-- Name: inventory inventory_hospital_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_hospital_id_fkey FOREIGN KEY (hospital_id) REFERENCES public.hospitals(hospital_id);


--
-- Name: inventory inventory_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(product_id);


--
-- Name: orders orders_hospital_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_hospital_id_fkey FOREIGN KEY (hospital_id) REFERENCES public.hospitals(hospital_id);


--
-- Name: orders orders_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(product_id);


--
-- Name: procedure_requirements procedure_requirements_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.procedure_requirements
    ADD CONSTRAINT procedure_requirements_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(product_id);


--
-- Name: procedures procedures_hospital_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.procedures
    ADD CONSTRAINT procedures_hospital_id_fkey FOREIGN KEY (hospital_id) REFERENCES public.hospitals(hospital_id);


--
-- Name: shipments shipments_hospital_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT shipments_hospital_id_fkey FOREIGN KEY (hospital_id) REFERENCES public.hospitals(hospital_id);


--
-- Name: shipments shipments_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT shipments_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(product_id);


--
-- Name: shipments shipments_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT shipments_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(supplier_id);


--
-- PostgreSQL database dump complete
--


