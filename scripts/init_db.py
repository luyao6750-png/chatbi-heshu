"""
初始化 ChatBI 演示数据库：自动建库、建表、灌入样例数据。

用法：
    python scripts/init_db.py

行为：
    1. 若目标数据库不存在，自动创建；
    2. 删除并重建 9 张表（幂等，可反复执行）；
    3. 灌入医疗样例数据，覆盖 ChatBI 面板中的示例问题。

说明：表结构对齐主项目 `alembic` 迁移与 `SCHEMA_PROMPT`。
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

import asyncpg

# 让脚本可直接运行，也能 import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from chatbi.config import get_settings  # noqa: E402

settings = get_settings()

# ── DDL：9 张表 ─────────────────────────────────────────────────────────
SCHEMA_STATEMENTS = [
    """
    CREATE TABLE departments (
        id BIGSERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        created_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    )""",
    """
    CREATE TABLE diseases (
        id BIGSERIAL PRIMARY KEY,
        name VARCHAR(200) NOT NULL UNIQUE,
        department_id BIGINT REFERENCES departments(id) ON DELETE SET NULL,
        description TEXT, cause TEXT, prevent TEXT, cure_way TEXT,
        cure_lasttime VARCHAR(200), cured_prob VARCHAR(200),
        easy_get TEXT, cost_money VARCHAR(200),
        created_at TIMESTAMP DEFAULT now(), updated_at TIMESTAMP DEFAULT now()
    )""",
    """
    CREATE TABLE symptoms (
        id BIGSERIAL PRIMARY KEY,
        name VARCHAR(200) NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT now(), updated_at TIMESTAMP DEFAULT now()
    )""",
    """
    CREATE TABLE drugs (
        id BIGSERIAL PRIMARY KEY,
        name VARCHAR(200) NOT NULL, alias VARCHAR(500), category VARCHAR(100),
        manufacturer VARCHAR(200), approval_number VARCHAR(100), is_otc BOOLEAN,
        stock_quantity INT, price FLOAT, expire_date VARCHAR(50),
        created_at TIMESTAMP DEFAULT now(), updated_at TIMESTAMP DEFAULT now()
    )""",
    """
    CREATE TABLE drug_details (
        id BIGSERIAL PRIMARY KEY,
        drug_id BIGINT NOT NULL UNIQUE REFERENCES drugs(id) ON DELETE CASCADE,
        indication TEXT, usage_dosage TEXT, adverse_reaction TEXT,
        contraindication TEXT, precaution TEXT, interaction TEXT,
        storage TEXT, full_instruction TEXT,
        created_at TIMESTAMP DEFAULT now(), updated_at TIMESTAMP DEFAULT now()
    )""",
    """
    CREATE TABLE disease_symptoms (
        id BIGSERIAL PRIMARY KEY,
        disease_id BIGINT NOT NULL REFERENCES diseases(id) ON DELETE CASCADE,
        symptom_id BIGINT NOT NULL REFERENCES symptoms(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT now(), updated_at TIMESTAMP DEFAULT now()
    )""",
    """
    CREATE TABLE disease_drugs (
        id BIGSERIAL PRIMARY KEY,
        disease_id BIGINT NOT NULL REFERENCES diseases(id) ON DELETE CASCADE,
        drug_id BIGINT NOT NULL REFERENCES drugs(id) ON DELETE CASCADE,
        relation_type VARCHAR(20) NOT NULL DEFAULT 'common',
        created_at TIMESTAMP DEFAULT now(), updated_at TIMESTAMP DEFAULT now()
    )""",
    """
    CREATE TABLE patients (
        id BIGSERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL, gender VARCHAR(10), age INT,
        phone VARCHAR(20), id_card VARCHAR(50),
        allergy_history TEXT, medical_history TEXT, blood_type VARCHAR(10),
        created_at TIMESTAMP DEFAULT now(), updated_at TIMESTAMP DEFAULT now()
    )""",
    """
    CREATE TABLE consultations (
        id BIGSERIAL PRIMARY KEY,
        patient_id BIGINT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        department_id BIGINT REFERENCES departments(id) ON DELETE SET NULL,
        chief_complaint TEXT, diagnosis TEXT, prescription TEXT,
        urgency_level VARCHAR(20) NOT NULL DEFAULT 'normal',
        session_id VARCHAR(100), milvus_doc_id VARCHAR(100),
        created_at TIMESTAMP DEFAULT now(), updated_at TIMESTAMP DEFAULT now()
    )""",
]

DROP_STATEMENTS = [
    "DROP TABLE IF EXISTS consultations CASCADE",
    "DROP TABLE IF EXISTS patients CASCADE",
    "DROP TABLE IF EXISTS disease_drugs CASCADE",
    "DROP TABLE IF EXISTS disease_symptoms CASCADE",
    "DROP TABLE IF EXISTS drug_details CASCADE",
    "DROP TABLE IF EXISTS drugs CASCADE",
    "DROP TABLE IF EXISTS symptoms CASCADE",
    "DROP TABLE IF EXISTS diseases CASCADE",
    "DROP TABLE IF EXISTS departments CASCADE",
]

# ── 样例数据 ───────────────────────────────────────────────────────────
SEED_STATEMENTS = [
    # 科室
    """INSERT INTO departments (id, name, description) VALUES
    (1, '内科', '内科疾病诊疗'), (2, '外科', '外科手术与诊疗'),
    (3, '儿科', '儿童疾病诊疗'), (4, '骨科', '骨骼与关节疾病诊疗'),
    (5, '皮肤科', '皮肤病诊疗')""",

    # 疾病
    """INSERT INTO diseases (id, name, department_id, description) VALUES
    (1, '高血压', 1, '以动脉血压持续升高为主要表现的慢性疾病'),
    (2, '糖尿病', 1, '胰岛素分泌或作用缺陷引起的代谢性疾病'),
    (3, '冠心病', 1, '冠状动脉粥样硬化性心脏病'),
    (4, '感冒', 3, '上呼吸道病毒感染性疾病'),
    (5, '肺炎', 3, '肺部感染性疾病'),
    (6, '阑尾炎', 2, '阑尾急性炎症'),
    (7, '骨折', 4, '骨的完整性或连续性中断'),
    (8, '关节炎', 4, '关节炎症性疾病'),
    (9, '湿疹', 5, '皮肤炎症性疾病'),
    (10, '荨麻疹', 5, '皮肤过敏性风团')""",

    # 症状
    """INSERT INTO symptoms (id, name) VALUES
    (1, '头痛'), (2, '发热'), (3, '咳嗽'), (4, '血压升高'), (5, '血糖升高'),
    (6, '胸痛'), (7, '腹痛'), (8, '皮疹'), (9, '关节疼痛'), (10, '乏力'),
    (11, '鼻塞'), (12, '气短')""",

    # 疾病-症状
    """INSERT INTO disease_symptoms (disease_id, symptom_id) VALUES
    (1,1),(1,4),(1,10), (2,5),(2,10), (3,6),(3,12),
    (4,2),(4,3),(4,11),(4,1), (5,2),(5,3),(5,12),
    (6,7),(6,2), (8,9),(8,10), (9,8), (10,8)""",

    # 药品
    """INSERT INTO drugs (id, name, alias, category, manufacturer, approval_number, is_otc, stock_quantity, price, expire_date) VALUES
    (1, '阿司匹林', '拜阿司匹灵', '解热镇痛', '拜耳', '国药准字H20050011', true, 120, 12.5, '2027-06-30'),
    (2, '布洛芬', '芬必得', '解热镇痛', '中美史克', '国药准字H10900089', true, 35, 18.0, '2026-12-31'),
    (3, '二甲双胍', NULL, '降糖药', '华北制药', '国药准字H13020632', false, 80, 25.0, '2027-03-31'),
    (4, '阿莫西林', '阿莫仙', '抗生素', '联邦制药', '国药准字H44021518', false, 45, 15.5, '2027-01-31'),
    (5, '硝苯地平', '心痛定', '降压药', '上海信谊', '国药准字H31020219', false, 60, 22.0, '2027-05-31'),
    (6, '对乙酰氨基酚', '泰诺林', '解热镇痛', '上海强生', '国药准字H31020026', true, 200, 9.8, '2027-08-31'),
    (7, '头孢克肟', NULL, '抗生素', '广州白云山', '国药准字H20051048', false, 28, 35.0, '2026-11-30'),
    (8, '钙尔奇D', '钙片', '维生素类', '惠氏', '国药准字H10950030', true, 150, 45.0, '2028-01-31'),
    (9, '阿卡波糖', '拜糖平', '降糖药', '拜耳', '国药准字H19990205', false, 90, 55.0, '2027-09-30'),
    (10, '维生素C', '维C', '维生素类', '华北制药', '国药准字H13020627', true, 300, 5.5, '2027-12-31')""",

    # 药品详情（少量示例）
    """INSERT INTO drug_details (drug_id, indication, usage_dosage, adverse_reaction, contraindication) VALUES
    (1, '用于缓解轻至中度疼痛，如头痛、牙痛、肌肉痛。', '口服，一次 0.3~0.6g，一日 3 次。', '偶见胃肠道不适、恶心。', '对本品过敏者禁用。'),
    (3, '用于 2 型糖尿病，尤其肥胖患者。', '口服，起始剂量一次 0.5g，一日 2 次。', '腹泻、恶心、腹胀。', '肝肾功能不全者慎用。'),
    (4, '用于敏感菌所致的呼吸道感染、泌尿系统感染。', '口服，一次 0.5g，每 6~8 小时 1 次。', '皮疹、腹泻。', '青霉素过敏者禁用。')""",

    # 疾病-药品
    """INSERT INTO disease_drugs (disease_id, drug_id, relation_type) VALUES
    (1, 5, 'recommend'), (1, 1, 'common'), (2, 3, 'common'), (2, 9, 'recommend'),
    (3, 1, 'common'), (4, 6, 'common'), (4, 2, 'common'), (6, 4, 'common'), (6, 7, 'recommend')""",

    # 患者
    """INSERT INTO patients (id, name, gender, age, phone, id_card, allergy_history, medical_history, blood_type) VALUES
    (1, '张三', '男', 45, '13800138001', '110101198001011234', '青霉素', '高血压', 'A'),
    (2, '李四', '女', 32, '13800138002', '110101199201022345', NULL, NULL, 'B'),
    (3, '王五', '男', 8, '13800138003', '110101201801033456', NULL, '哮喘', 'O'),
    (4, '赵六', '女', 60, '13800138004', '110101196401044567', '磺胺', '糖尿病', 'AB'),
    (5, '孙七', '男', 28, '13800138005', '110101199801055678', NULL, NULL, 'A'),
    (6, '周八', '女', 55, '13800138006', '110101196901066789', NULL, '高血压', 'B'),
    (7, '吴九', '男', 70, '13800138007', '110101195401077890', '头孢', '冠心病', 'O'),
    (8, '郑十', '女', 40, '13800138008', '110101198401088901', NULL, NULL, 'A')""",

    # 问诊记录（近 30 天，覆盖 5 个科室，便于"问诊量排名/趋势"类查询）
    """INSERT INTO consultations (id, patient_id, department_id, chief_complaint, diagnosis, urgency_level, created_at) VALUES
    (1, 1, 1, '头痛、血压升高', '高血压', 'normal', now() - interval '1 day'),
    (2, 2, 3, '咳嗽、发热', '感冒', 'normal', now() - interval '1 day'),
    (3, 3, 3, '发热、鼻塞', '感冒', 'normal', now() - interval '2 days'),
    (4, 4, 1, '血糖升高、乏力', '糖尿病', 'normal', now() - interval '2 days'),
    (5, 5, 4, '关节疼痛', '关节炎', 'normal', now() - interval '3 days'),
    (6, 6, 1, '头晕、血压升高', '高血压', 'urgent', now() - interval '3 days'),
    (7, 7, 1, '胸痛、气短', '冠心病', 'emergency', now() - interval '4 days'),
    (8, 8, 5, '皮疹、瘙痒', '湿疹', 'normal', now() - interval '4 days'),
    (9, 1, 1, '复诊，血压控制情况', '高血压', 'normal', now() - interval '5 days'),
    (10, 2, 2, '右下腹痛、发热', '阑尾炎', 'urgent', now() - interval '6 days'),
    (11, 3, 3, '咳嗽加重、气短', '肺炎', 'urgent', now() - interval '7 days'),
    (12, 4, 1, '乏力、口干', '糖尿病', 'normal', now() - interval '8 days'),
    (13, 5, 4, '跌倒后局部疼痛', '骨折', 'emergency', now() - interval '9 days'),
    (14, 6, 1, '血压复查', '高血压', 'normal', now() - interval '10 days'),
    (15, 7, 1, '胸闷', '冠心病', 'urgent', now() - interval '11 days'),
    (16, 8, 5, '皮肤风团', '荨麻疹', 'normal', now() - interval '12 days'),
    (17, 1, 1, '头痛', '高血压', 'normal', now() - interval '14 days'),
    (18, 2, 3, '发热', '感冒', 'normal', now() - interval '15 days'),
    (19, 3, 2, '腹痛', '阑尾炎', 'urgent', now() - interval '16 days'),
    (20, 4, 1, '血糖监测', '糖尿病', 'normal', now() - interval '18 days'),
    (21, 5, 4, '关节肿胀', '关节炎', 'normal', now() - interval '20 days'),
    (22, 6, 1, '头晕', '高血压', 'normal', now() - interval '22 days'),
    (23, 7, 1, '胸痛复诊', '冠心病', 'normal', now() - interval '25 days'),
    (24, 8, 5, '皮疹复诊', '湿疹', 'normal', now() - interval '28 days')""",
]

# 重置自增序列，避免后续插入主键冲突
SEQUENCE_RESETS = [
    "SELECT setval(pg_get_serial_sequence('departments', 'id'), (SELECT COALESCE(MAX(id), 1) FROM departments))",
    "SELECT setval(pg_get_serial_sequence('diseases', 'id'), (SELECT COALESCE(MAX(id), 1) FROM diseases))",
    "SELECT setval(pg_get_serial_sequence('symptoms', 'id'), (SELECT COALESCE(MAX(id), 1) FROM symptoms))",
    "SELECT setval(pg_get_serial_sequence('drugs', 'id'), (SELECT COALESCE(MAX(id), 1) FROM drugs))",
    "SELECT setval(pg_get_serial_sequence('drug_details', 'id'), (SELECT COALESCE(MAX(id), 1) FROM drug_details))",
    "SELECT setval(pg_get_serial_sequence('disease_symptoms', 'id'), (SELECT COALESCE(MAX(id), 1) FROM disease_symptoms))",
    "SELECT setval(pg_get_serial_sequence('disease_drugs', 'id'), (SELECT COALESCE(MAX(id), 1) FROM disease_drugs))",
    "SELECT setval(pg_get_serial_sequence('patients', 'id'), (SELECT COALESCE(MAX(id), 1) FROM patients))",
    "SELECT setval(pg_get_serial_sequence('consultations', 'id'), (SELECT COALESCE(MAX(id), 1) FROM consultations))",
]


async def ensure_database() -> None:
    """若目标数据库不存在则创建。"""
    conn = await asyncpg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database="postgres",
    )
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", settings.DB_NAME
        )
        if not exists:
            # 数据库名来自配置，使用双引号安全引用
            await conn.execute(f'CREATE DATABASE "{settings.DB_NAME}"')
            print(f"已创建数据库：{settings.DB_NAME}")
        else:
            print(f"数据库已存在：{settings.DB_NAME}")
    finally:
        await conn.close()


async def init_tables() -> None:
    """删旧建新 + 灌入样例数据。"""
    conn = await asyncpg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
    )
    try:
        for stmt in DROP_STATEMENTS:
            await conn.execute(stmt)
        print("已清空旧表")

        for stmt in SCHEMA_STATEMENTS:
            await conn.execute(stmt)
        print("已创建 9 张表")

        for stmt in SEED_STATEMENTS:
            await conn.execute(stmt)
        print("已灌入样例数据")

        for stmt in SEQUENCE_RESETS:
            await conn.execute(stmt)
        print("已重置自增序列")
    finally:
        await conn.close()


async def main() -> None:
    print(f"目标数据库：{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    await ensure_database()
    await init_tables()
    print("✅ ChatBI 演示数据初始化完成")


if __name__ == "__main__":
    asyncio.run(main())
