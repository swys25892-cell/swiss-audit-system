import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Amman")

def now_local():
    return datetime.now(TZ)

# دالة لإنشاء جدول سجل التدقيق في قاعدة البيانات إذا لم يكن موجوداً
def init_audit_log_table(conn):
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS audit_activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_time TEXT,
            username TEXT,
            action_type TEXT,
            details TEXT
        )
    ''')
    conn.commit()

# دالة لتسجيل أي نشاط رقابي
def log_activity(conn, username, action_type, details):
    try:
        c = conn.cursor()
        init_audit_log_table(conn)
        c.execute('''
            INSERT INTO audit_activity_log (action_time, username, action_type, details)
            VALUES (?, ?, ?, ?)
        ''', (now_local().strftime("%Y-%m-%d %I:%M:%S %p"), username, action_type, details))
        conn.commit()
    except Exception as e:
        print("خطأ في تسجيل النشاط:", e)

# الدالة الرئيسية لعرض صفحة الحوكمة والتدقيق المتقدمة (للمشرف الرئيسي فقط)
def show_governance_page(conn):
    st.markdown("### 🛡️ لوحة الحوكمة والتدقيق الرقمي (Audit Governance)")
    st.caption("سجل التدقيق الرقابي، مؤشرات الأداء التراكمي، والتوقيع والاعتماد الرقمي للتقارير")
    st.write("---")

    init_audit_log_table(conn)

    # 1. قسم سجل التدقيق الرقابي (Activity Log)
    with st.container():
        st.markdown('''
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border-right: 5px solid #1c4587; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px;">
                <h4 style="margin:0; color: #1c4587;">🔍 1. سجل التدقيق الرقابي والمتابعة (Activity Log)</h4>
                <p style="margin:5px 0 0 0; font-size: 13px; color: #666;">سجل تلقائي موثق لجميع عمليات التعديل، الحذف، والترحيل داخل النظام.</p>
            </div>
        ''', unsafe_allow_html=True)

        df_logs = pd.read_sql_query("SELECT * FROM audit_activity_log ORDER BY id DESC LIMIT 100", conn)
        
        if df_logs.empty:
            st.info("ℹ️ لا توجد سجلات نشاط مسجلة حتى الآن.")
        else:
            st.dataframe(df_logs.rename(columns={
                "id": "معرف الحركة",
                "action_time": "وقت الحركة",
                "username": "المستخدم المسؤول",
                "action_type": "نوع الإجراء",
                "details": "التفاصيل"
            }), use_container_width=True, hide_index=True)

    st.write("---")
    
    # 2. قريباً بقية الأقسام (مؤشر الأداء التراكمي والتوقيع الرقمي)
    st.info("💡 يتم الآن تجهيز بقية أقسام مؤشرات الأداء التراكمي والتوقيع الرقمي لإضافتها بالتتابع.")
