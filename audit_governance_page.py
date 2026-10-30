import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Amman")

def now_local():
    return datetime.now(TZ)

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

# دالة تسجيل النشاط الرقابي لتجنب خطأ الاستيراد مع app.py
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

def show_governance_page(conn):
    st.markdown("### 🛡️ لوحة الحوكمة والتدقيق الرقمي (Metro Dashboard)")
    st.caption("سجل التدقيق الرقابي ومؤشرات الأداء التراكمي للموظفين بطراز المربعات العصرية")
    st.write("---")

    init_audit_log_table(conn)

    # تقسيم الواجهة إلى مربعين رئيسيين بجانب بعضهما (طراز ويندوز فون)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('''
            <div style="background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%); padding: 20px; border-radius: 12px; border: 2px solid #90cdf4; text-align: center; height: 160px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <h3 style="color: #2b6cb0; margin: 0 0 5px 0; font-size: 18px;">🔍 سجل التدقيق الرقابي</h3>
                    <p style="color: #2c5282; font-size: 12px; margin: 0;">متابعة عمليات التعديل، الحذف والترحيل التلقائي.</p>
                </div>
                <div style="background-color: #ffffff; padding: 6px; border-radius: 6px; font-weight: bold; color: #2b6cb0; font-size: 12px;">
                    عرض سجل الحركات النشطة
                </div>
            </div>
        ''', unsafe_allow_html=True)
        btn_tile_log = st.button("عرض سجل التدقيق", use_container_width=True, key="btn_g_1")

    with col2:
        st.markdown('''
            <div style="background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%); padding: 20px; border-radius: 12px; border: 2px solid #9ae6b4; text-align: center; height: 160px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <h3 style="color: #276749; margin: 0 0 5px 0; font-size: 18px;">📊 الأداء التراكمي للموظف</h3>
                    <p style="color: #22543d; font-size: 12px; margin: 0;">تحليل تكرارات المطابقة والمخالفات ونسب الالتزام.</p>
                </div>
                <div style="background-color: #ffffff; padding: 6px; border-radius: 6px; font-weight: bold; color: #276749; font-size: 12px;">
                    عرض بطاقة أداء الموظفين
                </div>
            </div>
        ''', unsafe_allow_html=True)
        btn_tile_score = st.button("عرض أداء الموظفين", use_container_width=True, key="btn_g_2")

    st.write("---")

    # التحكم بالتبديل التفاعلي بين المربعين
    if btn_tile_log or "gov_active_tile" not in st.session_state:
        st.session_state.gov_active_tile = 1

    if btn_tile_score:
        st.session_state.gov_active_tile = 2

    # عرض محتوى المربع الأول: سجل التدقيق الرقابي
    if st.session_state.gov_active_tile == 1:
        st.markdown("#### 🔍 تفاصيل سجل التدقيق الرقابي والمتابعة (Activity Log)")
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

    # عرض محتوى المربع الثاني: مؤشر الأداء التراكمي للموظف
    elif st.session_state.gov_active_tile == 2:
        st.markdown("#### 📊 بطاقة أداء الموظف التراكمية (Employee Scorecard)")
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
