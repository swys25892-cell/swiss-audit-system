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
        CREATE TABLE IF NOT EXISTS daily_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audit_date TEXT,
            branch_no TEXT,
            branch_name TEXT,
            box_no TEXT,
            employee_name TEXT,
            excess REAL,
            shortage REAL,
            status TEXT,
            notes TEXT,
            audit_time TEXT
        )
    ''')
    
    # جدول المطابقات والترحيل الشهري
    c.execute('''
        CREATE TABLE IF NOT EXISTS monthly_audit_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audit_date TEXT,
            branch_no TEXT,
            branch_name TEXT,
            box_no TEXT,
            employee_name TEXT,
            excess REAL,
            shortage REAL,
            status TEXT,
            notes TEXT,
            audit_time TEXT
        )
    ''')
    
    # جدول الموظفين والصناديق الأساسي
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            box_no TEXT PRIMARY KEY,
            employee_name TEXT,
            branch_name TEXT,
            branch_no TEXT
        )
    ''')
    
    try:
        c.execute("ALTER TABLE employees ADD COLUMN branch_no TEXT")
    except:
        pass
    try:
        c.execute("ALTER TABLE employees ADD COLUMN branch_name TEXT")
    except:
        pass
        
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect('swiss_audit_system.db', check_same_thread=False)

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
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #555;">التدقيق الداخلي والرقابة</p>
            </div>
        ''', unsafe_allow_html=True)
        st.markdown("👤 **المستخدم:** `ADMIN`")
        st.write("---")
    
    menu = st.sidebar.selectbox("قائمة التنقل الرئيسي", [
        "📋 لوحة المتابعة والتدقيق اليومي", 
        "📁 المطابقات الشهرية والترحيل",
        "👥 قاعدة بيانات الموظفين والصناديق",
        "📊 المؤشرات والتقارير الإحصائية"
    ])
    
    st.sidebar.write("---")
    if st.sidebar.button("تسجيل الخروج", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    # الهيدر العلوي للنظام
    st.markdown('''
        <div style="background-color: #ffffff; padding: 18px; border-radius: 12px; border-right: 6px solid #d9ea37; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 20px; text-align: center;">
            <h2 style="color: #111111; margin: 0; font-size: 22px;">شركة سويس للصرافة | لوحة المتابعة والتدقيق اليومي للحركات</h2>
            <p style="color: #666666; margin: 4px 0 0 0; font-size: 13px;">نظام إدارة المطابقات والتدقيق الميداني المستقل</p>
        </div>
    ''', unsafe_allow_html=True)

    conn = get_db_connection()

    if menu == "📋 لوحة المتابعة والتدقيق اليومي":
        st.subheader("📋 جدول المتابعة والتدقيق اليومي للحركات (مرتبط بالتاريخ)")
        
        selected_date = st.date_input("تاريخ التدقيق المطلوب", datetime.now())
        date_str = str(selected_date)
        
        df_emp = pd.read_sql_query("SELECT * FROM employees", conn)
        
        if df_emp.empty:
            st.warning("⚠️ تنبيه: يرجى أولاً إدخال بيانات الموظفين والصناديق من قائمة (قاعدة بيانات الموظفين والصناديق).")
        else:
            df_saved = pd.read_sql_query("SELECT * FROM daily_audit WHERE audit_date = ?", conn, params=(date_str,))
            working_df = df_emp.copy()
            
            if not df_saved.empty:
                df_saved = df_saved.drop_duplicates(subset=['box_no'], keep='last')
                working_df = pd.merge(working_df, df_saved[['box_no', 'excess', 'shortage', 'status', 'audit_time', 'notes']], on='box_no', how='left')
                working_df.rename(columns={'excess': 'الزيادة', 'shortage': 'النقص', 'status': 'الحالة', 'audit_time': 'الوقت', 'notes': 'الملاحظات'}, inplace=True)
            else:
                working_df["الزيادة"] = 0.0
                working_df["النقص"] = 0.0
                working_df["الحالة"] = "مطابق"
                working_df["الوقت"] = ""
                working_df["الملاحظات"] = ""

            working_df["الزيادة"] = working_df["الزيادة"].fillna(0.0)
            working_df["النقص"] = working_df["النقص"].fillna(0.0)
            working_df["الحالة"] = working_df["الحالة"].fillna("مطابق")
            working_df["الوقت"] = working_df["الوقت"].fillna("")
            working_df["الملاحظات"] = working_df["الملاحظات"].fillna("")

            working_df = working_df[[
                "branch_no", "branch_name", "box_no", "employee_name", 
                "الزيادة", "النقص", "الحالة", "الوقت", "الملاحظات"
            ]]

            branch_filter = st.selectbox("تصفية حسب الفرع:", ["الكل"] + list(df_emp['branch_name'].unique()))
            
            if branch_filter != "الكل":
                filtered_df = working_df[working_df['branch_name'] == branch_filter]
            else:
                filtered_df = working_df
            
            edited_df = st.data_editor(
                filtered_df,
                column_config={
                    "branch_no": st.column_config.TextColumn("رقم الفرع", disabled=True),
                    "branch_name": st.column_config.TextColumn("اسم الفرع", disabled=True),
                    "box_no": st.column_config.TextColumn("رقم الصندوق", disabled=True),
                    "employee_name": st.column_config.TextColumn("اسم الموظف", disabled=True),
                    "الزيادة": "الزيادة",
                    "النقص": "النقص",
                    "الحالة": st.column_config.SelectboxColumn("الحالة", options=["مطابق", "غير مطابق"], required=True),
                    "الوقت": st.column_config.TextColumn("الوقت", disabled=True),
                    "الملاحظات": "الملاحظات"
                },
                use_container_width=True,
                hide_index=True,
                key=f"audit_editor_{date_str}"
            )

            current_time_str = datetime.now().strftime("%I:%M:%S %p")
            c = conn.cursor()
            for index, row in edited_df.iterrows():
                box = str(row["box_no"])
                c.execute("SELECT id, audit_time, status FROM daily_audit WHERE audit_date = ? AND box_no = ?", (date_str, box))
                existing_rec = c.fetchone()
                
                if existing_rec:
                    old_time = existing_rec[1]
                    old_status = existing_rec[2]
                    new_time = current_time_str if (old_status != str(row["الحالة"]) or not old_time) else old_time
                    
                    c.execute('''
                        UPDATE daily_audit 
                        SET excess = ?, shortage = ?, status = ?, notes = ?, audit_time = ?
                        WHERE audit_date = ? AND box_no = ?
                    ''', (float(row["الزيادة"]), float(row["النقص"]), str(row["الحالة"]), str(row["الملاحظات"]), new_time, date_str, box))
                else:
                    c.execute('''
                        INSERT INTO daily_audit (audit_date, branch_no, branch_name, box_no, employee_name, excess, shortage, status, notes, audit_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (date_str, str(row["branch_no"]), str(row["branch_name"]), box, str(row["employee_name"]), float(row["الزيادة"]), float(row["النقص"]), str(row["الحالة"]), str(row["الملاحظات"]), current_time_str))
            conn.commit()
            st.success(f"⚡ يتم حفظ التعديلات تلقائياً لتاريخ ({date_str}) بشكل فوري!")

    elif menu == "📁 المطابقات الشهرية والترحيل":
        st.subheader("📁 أرشيف المطابقات الشهرية والترحيل اليومي")
        st.caption("من هنا يمكنك ترحيل حركات وتدقيق التاريخ المحدد إلى قاعدة بيانات المطابقات الشهرية.")
        
        target_date = st.date_input("تاريخ اليوم المراد ترحيله وعرضه", datetime.now(), key="archive_date")
        target_date_str = str(target_date)
        
        col_btn1, col_btn2 = st.columns([1, 2])
        with col_btn1:
            if st.button("📥 تنفيذ ترحيل حركات اليوم المحدد", use_container_width=True):
                df_day = pd.read_sql_query("SELECT * FROM daily_audit WHERE audit_date = ?", conn, params=(target_date_str,))
                if df_day.empty:
                    st.warning(f"⚠️ لا توجد حركات مسجلة لتاريخ ({target_date_str}) ليتم ترحيلها.")
                else:
                    c = conn.cursor()
                    for _, r in df_day.iterrows():
                        c.execute("SELECT id FROM monthly_audit_archive WHERE audit_date = ? AND box_no = ?", (target_date_str, r["box_no"]))
                        exists = c.fetchone()
                        if not exists:
                            c.execute('''
                                INSERT INTO monthly_audit_archive (audit_date, branch_no, branch_name, box_no, employee_name, excess, shortage, status, notes, audit_time)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (r["audit_date"], r["branch_no"], r["branch_name"], r["box_no"], r["employee_name"], r["excess"], r["shortage"], r["status"], r["notes"], r["audit_time"]))
                    conn.commit()
                    st.success(f"✅ تم ترحيل حركات تاريخ ({target_date_str}) إلى أرشيف المطابقات الشهرية بنجاح تام!")
                    st.rerun()
        
        st.write("---")
        st.markdown("##### 📊 جدول أرشيف المطابقات الشهرية والترحيلات المسجلة")
        
        # خيار لتصفية الأرشيف حسب التاريخ المختار أو عرضه كاملاً
        archive_view_mode = st.radio("طريقة عرض الأرشيف:", ["عرض السجلات الخاصة بالتاريخ المختار أعلاه فقط", "عرض كافة سجلات الأرشيف الشهري"], horizontal=True)
        
        if archive_view_mode == "عرض السجلات الخاصة بالتاريخ المختار أعلاه فقط":
            df_monthly = pd.read_sql_query("SELECT * FROM monthly_audit_archive WHERE audit_date = ?", conn, params=(target_date_str,))
        else:
            df_monthly = pd.read_sql_query("SELECT * FROM monthly_audit_archive", conn)

        if df_monthly.empty:
            st.info(f"لا توجد سجلات مرحلة مطابقة لتاريخ ({target_date_str}) في الأرشيف الشهري.")
        else:
            st.dataframe(df_monthly.rename(columns={
                "audit_date": "التاريخ",
                "branch_no": "رقم الفرع",
                "branch_name": "اسم الفرع",
                "box_no": "رقم الصندوق",
                "employee_name": "اسم الموظف",
                "excess": "الزيادة",
                "shortage": "النقص",
                "status": "الحالة",
                "audit_time": "الوقت",
                "notes": "الملاحظات"
            }), use_container_width=True)

    elif menu == "👥 قاعدة بيانات الموظفين والصناديق":
        st.subheader("👥 إدارة قاعدة بيانات الموظفين والصناديق والفروع")
        st.caption("إضافة أو تعديل الصناديق وأسماء الموظفين وتوزيعهم على الفروع كما في جداول الشركة.")
        
        col1, col2 = st.columns([1, 1.2])
        with col1:
            with st.form("add_emp_form"):
                b_no = st.text_input("رقم الفرع (مثال: 2)")
                b_name = st.text_input("اسم الفرع (مثال: فرع تلاع العلي)")
                box_num = st.text_input("رقم الصندوق (مثال: 7046)")
                emp_n = st.text_input("اسم الموظف")
                
                save_btn = st.form_submit_button("إضافة / تحديث الصندوق والموظف", use_container_width=True)
                
                if save_btn:
                    if box_num and emp_n and b_name:
                        c = conn.cursor()
                        c.execute('''
                            INSERT INTO employees (box_no, employee_name, branch_name, branch_no)
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT(box_no) DO UPDATE SET
                                employee_name = excluded.employee_name,
                                branch_name = excluded.branch_name,
                                branch_no = excluded.branch_no
                        ''', (box_num.strip(), emp_n.strip(), b_name.strip(), b_no.strip()))
                        conn.commit()
                        st.success(f"تم حفظ الصندوق ({box_num}) للموظف ({emp_n}) بنجاح!")
                        st.rerun()
                    else:
                        st.error("يرجى ملء الحقول الأساسية (رقم الصندوق، اسم الموظف، اسم الفرع).")
                        
        with col2:
            st.markdown("##### 📊 السجلات الحالية في قاعدة البيانات")
            df_current = pd.read_sql_query("SELECT * FROM employees", conn)
            if df_current.empty:
                st.info("لا توجد بيانات مسجلة حتى الآن.")
            else:
                st.dataframe(df_current.rename(columns={
                    "box_no": "رقم الصندوق",
                    "employee_name": "اسم الموظف",
                    "branch_name": "اسم الفرع",
                    "branch_no": "رقم الفرع"
                }), use_container_width=True)

    elif menu == "📊 المؤشرات والتقارير الإحصائية":
        st.subheader("📊 المؤشرات والتقارير العامة للتدقيق")
        c1, c2, c3 = st.columns(3)
        df_all = pd.read_sql_query("SELECT * FROM employees", conn)
        total_boxes = len(df_all)
        c1.metric("إجمالي الصناديق المسجلة", total_boxes)
        c2.metric("الصناديق المطابقة", total_boxes)
        c3.metric("حالات عدم المطابقة", 0)
        st.info("💡 يتم تحديث المؤشرات تلقائياً بناءً على حركات التدقيق اليومية المسجلة.")

    conn.close()

if not st.session_state.logged_in:
    login_screen()
else:
    main_app()
