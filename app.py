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

# إعداد قاعدة البيانات الداخلية (SQLite) لتخزين البيانات بالكامل داخل التطبيق
def init_db():
    conn = sqlite3.connect('swiss_audit_system.db', check_same_thread=False)
    c = conn.cursor()
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
    conn.commit()
    conn.close()

init_db()

# دوال التعامل مع قاعدة البيانات
def add_record(date, branch, box_no, employee, discrepancy, status, notes):
    conn = sqlite3.connect('swiss_audit_system.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        INSERT INTO audits (date, branch, box_no, employee, discrepancy, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (date, branch, box_no, employee, discrepancy, status, notes))
    conn.commit()
    conn.close()

def get_data():
    conn = sqlite3.connect('swiss_audit_system.db', check_same_thread=False)
    df = pd.read_sql_query("SELECT * FROM audits", conn)
    conn.close()
    return df

# حالة تسجيل الدخول
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_screen():
    st.markdown('<div style="background-color: #ffffff; padding: 25px; border-radius: 16px; border: 2px solid #d9ea37; text-align: center; max-width: 480px; margin: 30px auto; box-shadow: 0 4px 15px rgba(0,0,0,0.08);"><h2 style="color: #000000; font-family: Tahoma; margin-bottom: 5px;">شركة سويس للصرافة</h2><p style="color: #666666; font-size: 14px; margin-top: 0;">بوابة الدخول لقسم التدقيق الداخلي والرقابة</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
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
    st.sidebar.markdown("👤 **المستخدم:** `ADMIN`")
    st.sidebar.write("---")
    
    menu = st.sidebar.selectbox("قائمة التنقل الرئيسي", ["🏠 الرئيسية والمؤشرات", "📝 صفحة الإدخال اليومي", "🚨 تقرير الحالات غير المطابقة والسجلات"])
    
    st.sidebar.write("---")
    if st.sidebar.button("تسجيل الخروج", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    st.markdown('<div style="background-color: #ffffff; padding: 20px; border-radius: 12px; border-right: 6px solid #d9ea37; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 25px; text-align: center;"><h2 style="color: #111111; margin: 0;">شركة سويس للصرافة | نظام التدقيق والرقابة الداخلي</h2><p style="color: #666666; margin: 5px 0 0 0; font-size: 14px;">نظام إدارة المطابقات والتدقيق الميداني المستقل</p></div>', unsafe_allow_html=True)

    df = get_data()

    if menu == "🏠 الرئيسية والمؤشرات":
        st.subheader("📊 المؤشرات العامة لنظام التدقيق")
        
        total_records = len(df)
        non_compliant = len(df[df['status'] == 'غير مطابق']) if not df.empty else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي الحركات المسجلة", total_records)
        c2.metric("الحركات المطابقة", total_records - non_compliant)
        c3.metric("حالات عدم المطابقة", non_compliant)
        
        st.write("")
        st.info("💡 النظام يعمل بقاعدة بيانات داخلية مؤمنة بالكامل ومستقلة عن أي شيتات خارجية.")

    elif menu == "📝 صفحة الإدخال اليومي":
        st.subheader("📝 نموذج إدخال بيانات الصناديق والفروع اليومية")
        
        with st.form("audit_form"):
            col1, col2 = st.columns(2)
            with col1:
                audit_date = st.date_input("تاريخ التدقيق", datetime.now())
                branch = st.selectbox("اختر الفرع", ["فرع تلاع العلي", "فرع عبدون", "فرع مأدبا", "فرع ضاحية الرشيد"])
                box_no = st.text_input("رقم الصندوق", "7046")
            with col2:
                employee = st.text_input("اسم الموظف المسؤول")
                status = st.selectbox("حالة المطابقة", ["مطابق", "غير مطابق"])
                discrepancy = st.number_input("قيمة النقص أو الزيادة (د.أ)", min_value=0.0, value=0.0)
            
            notes = st.text_area("ملاحظات المدقق / تفاصيل الحركة")
            
            submit_btn = st.form_submit_button("حفظ الحركة في قاعدة بيانات النظام", use_container_width=True)
            
            if submit_btn:
                add_record(str(audit_date), branch, box_no, employee, discrepancy, status, notes)
                st.success("تم حفظ بيانات التدقيق بنجاح تام داخل قاعدة بيانات النظام!")

    elif menu == "🚨 تقرير الحالات غير المطابقة والسجلات":
        st.subheader("🚨 سجل حركات التدقيق والحالات غير المطابقة")
        
        if df.empty:
            st.warning("لا توجد سجلات مدخلة حتى الآن. استخدم صفحة الإدخال اليومي لإضافة الحركات.")
        else:
            filter_status = st.radio("تصفية العرض:", ["الكل", "غير مطابق فقط", "مطابق فقط"], horizontal=True)
            
            if filter_status == "غير مطابق فقط":
                view_df = df[df['status'] == 'غير مطابق']
            elif filter_status == "مطابق فقط":
                view_df = df[df['status'] == 'مطابق']
            else:
                view_df = df
                
            st.dataframe(view_df, use_container_width=True)

if not st.session_state.logged_in:
    login_screen()
else:
    main_app()
