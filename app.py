import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(
    page_title="نظام التدقيق الداخلي - شركة سويس للصرافة",
    page_icon="💼",
    layout="wide"
)

# إعداد قاعدة البيانات الداخلية (SQLite)
def init_db():
    conn = sqlite3.connect('swiss_audit_system.db', check_same_thread=False)
    c = conn.cursor()
    # جدول الحركات اليومية
    c.execute('''
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            branch TEXT,
            box_no TEXT,
            employee TEXT,
            discrepancy REAL,
            status TEXT,
            notes TEXT
        )
    ''')
    # جدول قاعدة بيانات الموظفين
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            box_no TEXT PRIMARY KEY,
            employee_name TEXT,
            current_branch TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# دوال التعامل مع الحركات
def add_audit_record(date, branch, box_no, employee, discrepancy, status, notes):
    conn = sqlite3.connect('swiss_audit_system.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        INSERT INTO audits (date, branch, box_no, employee, discrepancy, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (date, branch, box_no, employee, discrepancy, status, notes))
    conn.commit()
    conn.close()

def get_audits_data():
    conn = sqlite3.connect('swiss_audit_system.db', check_same_thread=False)
    df = pd.read_sql_query("SELECT * FROM audits", conn)
    conn.close()
    return df

# دوال التعامل مع الموظفين
def add_or_update_employee(box_no, employee_name, current_branch):
    conn = sqlite3.connect('swiss_audit_system.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        INSERT INTO employees (box_no, employee_name, current_branch)
        VALUES (?, ?, ?)
        ON CONFLICT(box_no) DO UPDATE SET
            employee_name = excluded.employee_name,
            current_branch = excluded.current_branch
    ''', (box_no, employee_name, current_branch))
    conn.commit()
    conn.close()

def get_employees_data():
    conn = sqlite3.connect('swiss_audit_system.db', check_same_thread=False)
    df = pd.read_sql_query("SELECT * FROM employees", conn)
    conn.close()
    return df

def get_employee_by_box(box_no):
    conn = sqlite3.connect('swiss_audit_system.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT employee_name, current_branch FROM employees WHERE box_no = ?", (box_no,))
    row = c.fetchone()
    conn.close()
    return row

# حالة تسجيل الدخول
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_screen():
    st.markdown('''
        <div style="background: linear-gradient(135deg, #ffffff 0%, #f9f9f9 100%); padding: 35px; border-radius: 16px; border: 2px solid #d9ea37; text-align: center; max-width: 480px; margin: 40px auto; box-shadow: 0 6px 20px rgba(0,0,0,0.08);">
            <div style="font-size: 40px; margin-bottom: 10px;">💼</div>
            <h2 style="color: #111111; font-family: Tahoma; margin-bottom: 5px;">شركة سويس للصرافة</h2>
            <p style="color: #666666; font-size: 14px; font-weight: bold; margin-top: 0;">قسم التدقيق الداخلي والرقابة</p>
        </div>
    ''', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("اسم المستخدم")
            password = st.text_input("كلمة المرور", type="password")
            submit_login = st.form_submit_button("تسجيل الدخول", use_container_width=True)
            
            if submit_login:
                if username == "ADMIN" and password == "1234":
                    st.session_state.logged_in = True
                    st.success("تم تسجيل الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error("اسم المستخدم أو كلمة المرور غير صحيحة")

def main_app():
    with st.sidebar:
        st.markdown('''
            <div style="text-align: center; padding: 10px; background-color: #f1f1f1; border-radius: 10px; margin-bottom: 15px;">
                <h4 style="margin: 0; color: #111;">💼 سويس للصرافة</h4>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #555;">التدقيق الداخلي</p>
            </div>
        ''', unsafe_allow_html=True)
        st.markdown("👤 **المستخدم:** `ADMIN`")
        st.write("---")
    
    menu = st.sidebar.selectbox("قائمة التنقل الرئيسي", [
        "🏠 الرئيسية والمؤشرات", 
        "📝 صفحة الإدخال اليومي", 
        "👥 قاعدة بيانات الموظفين",
        "🚨 تقرير الحالات غير المطابقة والسجلات"
    ])
    
    st.sidebar.write("---")
    if st.sidebar.button("تسجيل الخروج", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    st.markdown('<div style="background-color: #ffffff; padding: 20px; border-radius: 12px; border-right: 6px solid #d9ea37; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 25px; text-align: center;"><h2 style="color: #111111; margin: 0;">شركة سويس للصرافة | نظام التدقيق والرقابة الداخلي</h2><p style="color: #666666; margin: 5px 0 0 0; font-size: 14px;">نظام إدارة المطابقات والتدقيق الميداني المستقل</p></div>', unsafe_allow_html=True)

    df_audits = get_audits_data()

    if menu == "🏠 الرئيسية والمؤشرات":
        st.subheader("📊 المؤشرات العامة لنظام التدقيق")
        
        total_records = len(df_audits)
        non_compliant = len(df_audits[df_audits['status'] == 'غير مطابق']) if not df_audits.empty else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي الحركات المسجلة", total_records)
        c2.metric("الحركات المطابقة", total_records - non_compliant)
        c3.metric("حالات عدم المطابقة", non_compliant)
        
        st.write("")
        st.info("💡 النظام يعمل بقاعدة بيانات داخلية مؤمنة بالكامل ومستقلة عن أي شيتات خارجية.")

    elif menu == "👥 قاعدة بيانات الموظفين":
        st.subheader("👥 إدارة قاعدة بيانات الموظفين والتنقلات")
        st.caption("يمكنك من هنا إضافة موظف جديد أو تحديث الفرع الحالي لموظف بناءً على رقم صندوقه.")
        
        col_form, col_table = st.columns([1, 1.2])
        
        with col_form:
            st.markdown("##### ➕ إضافة / تعديل بيانات موظف")
            with st.form("emp_form"):
                emp_box = st.text_input("رقم الصندوق", placeholder="مثال: 7046")
                emp_name = st.text_input("اسم الموظف ثلاثي")
                emp_branch = st.selectbox("الفرع الحالي", [
                    "فرع تلاع العلي", "فرع عبدون", "فرع مأدبا", "فرع ضاحية الرشيد", 
                    "فرع العقبة", "فرع الزرقاء", "فرع إربد", "فرع الجبيهة", "فرع مرج الحمام"
                ])
                save_emp = st.form_submit_button("حفظ / تحديث بيانات الموظف", use_container_width=True)
                
                if save_emp:
                    if emp_box and emp_name:
                        add_or_update_employee(emp_box.strip(), emp_name.strip(), emp_branch)
                        st.success(f"تم حفظ بيانات الموظف ({emp_name}) للصندوق رقم ({emp_box}) بنجاح!")
                        st.rerun()
                    else:
                        st.error("يرجى إدخال رقم الصندوق واسم الموظف كاملين.")
                        
        with col_table:
            st.markdown("##### 📋 قائمة الموظفين المسجلين")
            df_emp = get_employees_data()
            if df_emp.empty:
                st.info("لا يوجد موظفون مسجلون حالياً. استخدم النموذج لإضافة أول موظف.")
            else:
                st.dataframe(df_emp.rename(columns={
                    "box_no": "رقم الصندوق",
                    "employee_name": "اسم الموظف",
                    "current_branch": "الفرع الحالي"
                }), use_container_width=True)

    elif menu == "📝 صفحة الإدخال اليومي":
        st.subheader("📝 نموذج إدخال بيانات الصناديق والفروع اليومية")
        
        # اختيار رقم الصندوق للربط التلقائي
        box_input = st.text_input("🔍 أدخل رقم الصندوق للبحث التلقائي عن الموظف والفرع:", placeholder="أدخل رقم الصندوق واضغط Enter (مثال: 7046)")
        
        auto_employee = ""
        auto_branch = "فرع تلاع العلي"
        
        if box_input.strip():
            emp_info = get_employee_by_box(box_input.strip())
            if emp_info:
                auto_employee = emp_info[0]
                auto_branch = emp_info[1]
                st.success(f"✅ تم التعرف على الموظف: **{auto_employee}** | الفرع الحالي: **{auto_branch}**")
            else:
                st.warning("⚠️ رقم الصندوق غير مسجل في قاعدة بيانات الموظفين. يمكنك إدخال الأسماء يدوياً أو إضافته من صفحة الموظفين.")

        st.write("---")
        
        with st.form("audit_form"):
            col1, col2 = st.columns(2)
            with col1:
                audit_date = st.date_input("تاريخ التدقيق", datetime.now())
                box_no = st.text_input("رقم الصندوق", value=box_input.strip())
                branch = st.text_input("الفرع", value=auto_branch)
            with col2:
                employee = st.text_input("اسم الموظف المسؤول", value=auto_employee)
                status = st.selectbox("حالة المطابقة", ["مطابق", "غير مطابق"])
                discrepancy = st.number_input("قيمة النقص أو الزيادة (د.أ)", min_value=0.0, value=0.0)
            
            notes = st.text_area("ملاحظات المدقق / تفاصيل الحركة")
            
            submit_btn = st.form_submit_button("حفظ الحركة في قاعدة بيانات النظام", use_container_width=True)
            
            if submit_btn:
                if box_no and employee:
                    add_audit_record(str(audit_date), branch, box_no, employee, discrepancy, status, notes)
                    st.success("تم حفظ بيانات التدقيق بنجاح تام داخل قاعدة بيانات النظام!")
                else:
                    st.error("يرجى التأكد من كتابة رقم الصندوق واسم الموظف.")

    elif menu == "🚨 تقرير الحالات غير المطابقة والسجلات":
        st.subheader("🚨 سجل حركات التدقيق والحالات غير المطابقة")
        
        if df_audits.empty:
            st.warning("لا توجد سجلات مدخلة حتى الآن. استخدم صفحة الإدخال اليومي لإضافة الحركات.")
        else:
            filter_status = st.radio("تصفية العرض:", ["الكل", "غير مطابق فقط", "مطابق فقط"], horizontal=True)
            
            if filter_status == "غير مطابق فقط":
                view_df = df_audits[df_audits['status'] == 'غير مطابق']
            elif filter_status == "مطابق فقط":
                view_df = df_audits[df_audits['status'] == 'مطابق']
            else:
                view_df = df_audits
                
            st.dataframe(view_df.rename(columns={
                "id": "الرقم",
                "date": "التاريخ",
                "branch": "الفرع",
                "box_no": "رقم الصندوق",
                "employee": "الموظف",
                "discrepancy": "المبلغ",
                "status": "الحالة",
                "notes": "الملاحظات"
            }), use_container_width=True)

if not st.session_state.logged_in:
    login_screen()
else:
    main_app()
