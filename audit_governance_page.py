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

# الدالة الرئيسية لعرض صفحة الحوكمة والتدقيق المتقدمة
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

    # 2. قسم بطاقة أداء الموظف التراكمية (Employee Scorecard)
    with st.container():
        st.markdown('''
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border-right: 5px solid #2b6cb0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px;">
                <h4 style="margin:0; color: #2b6cb0;">📊 2. مؤشر الأداء التراكمي للموظف (Employee Scorecard)</h4>
                <p style="margin:5px 0 0 0; font-size: 13px; color: #666;">تحليل تكرارات المطابقة والمخالفات لكل موظف وتقييم مستوى الالتزام الرقابي.</p>
            </div>
        ''', unsafe_allow_html=True)

        df_emp_list = pd.read_sql_query("SELECT DISTINCT employee_name FROM employees WHERE employee_name IS NOT NULL AND employee_name != ''", conn)
        
        if df_emp_list.empty:
            st.info("⚠️ لا توجد أسماء موظفين مسجلة في النظام.")
        else:
            selected_emp = st.selectbox("اختر اسم الموظف لتقييم أدائه:", df_emp_list['employee_name'].tolist())
            
            if selected_emp:
                df_emp_perf = pd.read_sql_query('''
                    SELECT audit_date, branch_name, box_no, status, excess, shortage, notes, audit_time
                    FROM monthly_audit_archive
                    WHERE employee_name = ?
                    ORDER BY audit_date DESC
                ''', conn, params=(selected_emp,))
                
                if df_emp_perf.empty:
                    st.warning(f"⚠️ لا توجد سجلات مؤرشفة للموظف ({selected_emp}) بعد.")
                else:
                    total_days = len(df_emp_perf)
                    matches = len(df_emp_perf[df_emp_perf['status'] == 'مطابق'])
                    non_matches = len(df_emp_perf[df_emp_perf['status'] == 'غير مطابق'])
                    leaves = len(df_emp_perf[df_emp_perf['status'] == 'مجاز'])
                    
                    commitment_rate = round((matches / (total_days - leaves) * 100), 1) if (total_days - leaves) > 0 else 100.0

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("نسبة الالتزام الرقابي", f"{commitment_rate}%")
                    c2.metric("أيام مطابقة ✅", matches)
                    c3.metric("أيام غير مطابقة 🚨", non_matches)
                    c4.metric("أيام مجاز 🔹", leaves)

                    st.markdown("##### 📋 تفاصيل سجل الأداء التاريخي للموظف:")
                    st.dataframe(df_emp_perf.rename(columns={
                        "audit_date": "التاريخ",
                        "branch_name": "الفرع",
                        "box_no": "رقم الصندوق",
                        "status": "الحالة",
                        "excess": "الزيادة",
                        "shortage": "النقص",
                        "notes": "الملاحظات",
                        "audit_time": "وقت التدقيق"
                    }), use_container_width=True, hide_index=True)
