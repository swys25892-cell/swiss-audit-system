import streamlit as st
import pandas as pd
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
    # جدول خاص بتسجيل الاعتمادات والتوقيعات الرقمية للتقارير
    c.execute('''
        CREATE TABLE IF NOT EXISTS digital_signoffs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sign_date TEXT,
            username TEXT,
            report_title TEXT,
            notes TEXT
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
                    c2.metric("أيام مطابق ✅", matches)
                    c3.metric("أيام غير مطابق 🚨", non_matches)
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

    st.write("---")

    # 3. قسم التوقيع والاعتماد الرقمي للتقارير (Digital Sign-off)
    with st.container():
        st.markdown('''
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border-right: 5px solid #38a169; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px;">
                <h4 style="margin:0; color: #38a169;">✍️ 3. التوقيع والاعتماد الرقمي للتقارير (Digital Sign-off)</h4>
                <p style="margin:5px 0 0 0; font-size: 13px; color: #666;">اعتماد رسمي موثق ومختوم رقمياً للتقارير الصادرة من قسم التدقيق الداخلي والرقابة.</p>
            </div>
        ''', unsafe_allow_html=True)

        with st.form("digital_signoff_form"):
            report_title_input = st.text_input("عنوان التقرير المراد اعتماده وتوقيعه رقمياً:", "تقرير التدقيق والرقابة الميدانية الشامل")
            sign_notes = st.text_area("ملاحظات الاعتماد والختم الرقابي:", "تمت مراجعة وتدقيق الحركات والبيانات الواردة وأصبحت معتمدة رسمياً.")
            
            submit_sign = st.form_submit_button("✍️ اعتماد وتوقيع التقرير رقمياً", use_container_width=True)
            
            if submit_sign:
                if report_title_input.strip():
                    current_sign_time = now_local().strftime("%Y-%m-%d %I:%M:%S %p")
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO digital_signoffs (sign_date, username, report_title, notes)
                        VALUES (?, ?, ?, ?)
                    ''', (current_sign_time, st.session_state.username, report_title_input.strip(), sign_notes.strip()))
                    conn.commit()
                    log_activity(conn, st.session_state.username, "اعتماد وتوقيع رقمي", f"تم اعتماد التقرير: {report_title_input.strip()}")
                    st.success(f"✅ تم اعتماد وتوقيع التقرير رقمياً بنجاح بواسطة المستخدم ({st.session_state.username}) بتاريخ ({current_sign_time})!")
                else:
                    st.error("يرجى إدخال عنوان التقرير المراد اعتماده.")

        st.markdown("##### 📜 سجل الاعتمادات والتوقيعات الرقمية السابقة:")
        df_signs = pd.read_sql_query("SELECT * FROM digital_signoffs ORDER BY id DESC", conn)
        if df_signs.empty:
            st.info("ℹ️ لا توجد اعتمادات رقمية مسجلة حتى الآن.")
        else:
            st.dataframe(df_signs.rename(columns={
                "id": "معرف الاعتماد",
                "sign_date": "وقت وتاريخ الاعتماد",
                "username": "المعتمد المسؤول",
                "report_title": "عنوان التقرير",
                "notes": "الملاحظات الرقابية"
            }), use_container_width=True, hide_index=True)
