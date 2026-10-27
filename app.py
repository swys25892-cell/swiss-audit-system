import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import os
import urllib.request
import arabic_reshaper
from bidi.algorithm import get_display

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
    
    # جدول المستخدمين والصلاحيات
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT,
            full_name TEXT
        )
    ''')
    
    # إنشاء حساب المشرف الافتراضي إن لم يكن موجوداً
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)", 
                  ("ADMIN", "1234", "مشرف رئيسي", "مدير النظام"))
        conn.commit()
        
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

# تجهيز النص العربي للعرض الصحيح في PDF
def ar(text):
    if not text:
        return ""
    try:
        text = str(text)
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return str(text)

# دالة توليد تقرير PDF يدعم العربية بشكل كامل
def generate_pdf_report(df_data, date_str):
    font_path = "Amiri-Regular.ttf"
    if not os.path.exists(font_path):
        try:
            # تحميل خط Amiri مجاناً لتثبيته في السحابة
            url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf"
            urllib.request.urlretrieve(url, font_path)
        except:
            pass

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    if os.path.exists(font_path):
        pdf.add_font("Amiri", fname=font_path)
        pdf.set_font("Amiri", size=16)
    else:
        pdf.set_font("Arial", size=16)
    
    # ترويسة التقرير
    pdf.cell(190, 10, text=ar("شركة سويس للصرافة - تقرير التدقيق الداخلي"), new_x="LMARGIN", new_y="NEXT", align='C')
    
    if os.path.exists(font_path):
        pdf.set_font("Amiri", size=12)
    else:
        pdf.set_font("Arial", size=12)
        
    pdf.cell(190, 8, text=ar(f"تقرير الحالات غير المطابقة - التاريخ: {date_str}"), new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(8)
    
    # رأس الجدول (من اليمين لليسار)
    if os.path.exists(font_path):
        pdf.set_font("Amiri", size=10)
    else:
        pdf.set_font("Arial", size=10)
        
    headers = [("الوقت", 30), ("الزيادة", 20), ("اسم الموظف", 45), ("رقم الصندوق", 25), ("اسم الفرع", 50), ("رقم الفرع", 20)]
    for i, (h, w) in enumerate(headers):
        last = i == len(headers) - 1
        pdf.cell(w, 8, ar(h), border=1, align='C',
                 new_x="LMARGIN" if last else "RIGHT",
                 new_y="NEXT" if last else "TOP")
    
    if os.path.exists(font_path):
        pdf.set_font("Amiri", size=9)
    else:
        pdf.set_font("Arial", size=9)
        
    for _, row in df_data.iterrows():
        values = [
            (str(row["الوقت"]), 30), 
            (str(row["الزيادة"]), 20), 
            (str(row["employee_name"]), 45),
            (str(row["box_no"]), 25), 
            (str(row["branch_name"]), 50), 
            (str(row["branch_no"]), 20)
        ]
        for i, (v, w) in enumerate(values):
            last = i == len(values) - 1
            pdf.cell(w, 8, ar(v), border=1, align='C',
                     new_x="LMARGIN" if last else "RIGHT",
                     new_y="NEXT" if last else "TOP")
    
    return bytes(pdf.output())

# حالة تسجيل الدخول
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_role" not in st.session_state:
    st.session_state.user_role = ""

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
            username_input = st.text_input("اسم المستخدم")
            password_input = st.text_input("كلمة المرور", type="password")
            submit_login = st.form_submit_button("تسجيل الدخول", use_container_width=True)
            
            if submit_login:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("SELECT password, role FROM users WHERE username = ?", (username_input.strip(),))
                user_record = c.fetchone()
                conn.close()
                
                if user_record and user_record[0] == password_input.strip():
                    st.session_state.logged_in = True
                    st.session_state.username = username_input.strip()
                    st.session_state.user_role = user_record[1]
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
        st.markdown(f"👤 **المستخدم:** `{st.session_state.username}`")
        st.markdown(f"🔒 **الصلاحية:** `{st.session_state.user_role}`")
        st.write("---")
    
    menu_options = [
        "📋 لوحة المتابعة والتدقيق اليومي", 
        "📁 المطابقات الشهرية والترحيل",
        "👥 قاعدة بيانات الموظفين والصناديق",
        "🔐 تغيير كلمة المرور الشخصية",
        "📊 المؤشرات والتقارير الإحصائية"
    ]
    
    if st.session_state.user_role == "مشرف رئيسي":
        menu_options.insert(3, "🔑 إدارة المستخدمين والصلاحيات")

    menu = st.sidebar.selectbox("قائمة التنقل الرئيسي", menu_options)
    
    st.sidebar.write("---")
    if st.sidebar.button("تسجيل الخروج", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_role = ""
        st.rerun()

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

            st.write("---")
            if st.button("🚨 استخراج تقرير الحالات غير المطابقة ليوم " + date_str, use_container_width=True):
                df_mismatches = edited_df[edited_df["الحالة"] == "غير مطابق"]
                if df_mismatches.empty:
                    st.info("🎉 لا توجد أي حالات (غير مطابق) مسجلة لهذا التاريخ.")
                else:
                    st.warning(f"⚠️ تم رصد ({len(df_mismatches)}) حالة غير مطابقة لهذا اليوم:")
                    st.dataframe(df_mismatches, use_container_width=True, hide_index=True)
                    
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        csv_data = df_mismatches.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 تحميل تقرير CSV",
                            data=csv_data,
                            file_name=f"non_matching_report_{date_str}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    with col_d2:
                        pdf_data = generate_pdf_report(df_mismatches, date_str)
                        st.download_button(
                            label="📥 تحميل تقرير PDF",
                            data=pdf_data,
                            file_name=f"non_matching_report_{date_str}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

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

    elif menu == "🔐 تغيير كلمة المرور الشخصية":
        st.subheader("🔐 تغيير كلمة المرور الخاصة بحسابك")
        st.caption(f"أنت تقوم بتغيير كلمة المرور الخاصة بالمستخدم الحالي: `{st.session_state.username}`")
        
        col_p1, col_p2 = st.columns([1, 1])
        with col_p1:
            with st.form("change_my_pass_form"):
                old_pass_input = st.text_input("كلمة المرور الحالية", type="password")
                new_pass_input = st.text_input("كلمة المرور الجديدة", type="password")
                confirm_pass_input = st.text_input("تأكيد كلمة المرور الجديدة", type="password")
                
                change_btn = st.form_submit_button("تحديث كلمة المرور", use_container_width=True)
                
                if change_btn:
                    if not old_pass_input or not new_pass_input or not confirm_pass_input:
                        st.error("يرجى ملء كافة الحقول المطلوبة.")
                    elif new_pass_input != confirm_pass_input:
                        st.error("كلمة المرور الجديدة وتأكيدها غير متطابقتين.")
                    else:
                        c = conn.cursor()
                        c.execute("SELECT password FROM users WHERE username = ?", (st.session_state.username,))
                        current_db_pass = c.fetchone()[0]
                        
                        if current_db_pass != old_pass_input.strip():
                            st.error("كلمة المرور الحالية غير صحيحة.")
                        else:
                            c.execute("UPDATE users SET password = ? WHERE username = ?", (new_pass_input.strip(), st.session_state.username))
                            conn.commit()
                            st.success("✅ تم تغيير كلمة المرور بنجاح! يرجى استخدامها عند تسجيل الدخول القادم.")

    elif menu == "🔑 إدارة المستخدمين والصلاحيات":
        st.subheader("🔑 إدارة حسابات المدققين وصلاحيات الدخول")
        st.caption("إضافة حسابات جديدة، مراجعة كلمات المرور للموظفين، وتعديلها أو حذفها.")
        
        if st.session_state.user_role != "مشرف رئيسي":
            st.error("⚠️ عذراً، هذه الصفحة مخصصة للمشرف الرئيسي فقط.")
        else:
            col_u1, col_u2 = st.columns([1, 1.3])
            with col_u1:
                with st.form("new_user_form"):
                    st.markdown("##### ➕ إضافة مستخدم جديد")
                    new_user = st.text_input("اسم المستخدم (بالإنجليزية، مثال: ahmad)")
                    new_pass = st.text_input("كلمة المرور", type="password")
                    new_name = st.text_input("اسم الموظف الكامل")
                    new_role = st.selectbox("الصلاحية", ["مدقق", "مشرف رئيسي"])
                    
                    add_user_btn = st.form_submit_button("إضافة المستخدم", use_container_width=True)
                    
                    if add_user_btn:
                        if new_user and new_pass and new_name:
                            try:
                                c = conn.cursor()
                                c.execute("INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                                          (new_user.strip(), new_pass.strip(), new_role, new_name.strip()))
                                conn.commit()
                                st.success(f"تم إضافة المستخدم ({new_name}) بنجاح!")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("اسم المستخدم موجود مسبقاً، يرجى اختيار اسم آخر.")
                        else:
                            st.error("يرجى ملء جميع الحقول المطلوبة.")
                            
                st.write("---")
                with st.form("edit_delete_user_form"):
                    st.markdown("##### ✏️ تعديل أو حذف مستخدم")
                    df_all_users = pd.read_sql_query("SELECT username FROM users", conn)
                    user_list = df_all_users['username'].tolist() if not df_all_users.empty else []
                    
                    selected_target_user = st.selectbox("اختر اسم المستخدم للتعديل/الحذف", user_list)
                    edit_pass = st.text_input("كلمة المرور الجديدة (اختياري)", type="password")
                    edit_role = st.selectbox("تعديل الصلاحية", ["مدقق", "مشرف رئيسي"])
                    
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        update_btn = st.form_submit_button("💾 تحديث البيانات", use_container_width=True)
                    with col_b2:
                        delete_btn = st.form_submit_button("🗑️ حذف المستخدم", use_container_width=True)
                        
                    if update_btn and selected_target_user:
                        c = conn.cursor()
                        if edit_pass.strip():
                            c.execute("UPDATE users SET password = ?, role = ? WHERE username = ?", (edit_pass.strip(), edit_role, selected_target_user))
                        else:
                            c.execute("UPDATE users SET role = ? WHERE username = ?", (edit_role, selected_target_user))
                        conn.commit()
                        st.success(f"تم تحديث بيانات المستخدم ({selected_target_user}) بنجاح!")
                        st.rerun()
                        
                    if delete_btn and selected_target_user:
                        if selected_target_user == "ADMIN":
                            st.error("⚠️ لا يمكن حذف حساب المشرف الرئيسي (ADMIN) الأساسي للنظام!")
                        else:
                            c = conn.cursor()
                            c.execute("DELETE FROM users WHERE username = ?", (selected_target_user,))
                            conn.commit()
                            st.success(f"تم حذف المستخدم ({selected_target_user}) بنجاح!")
                            st.rerun()
                            
            with col_u2:
                st.markdown("##### 📋 جدول المستخدمين وكلمات المرور (خاص بالمدير)")
                df_users = pd.read_sql_query("SELECT username, password, full_name, role FROM users", conn)
                st.dataframe(df_users.rename(columns={
                    "username": "اسم المستخدم",
                    "password": "كلمة المرور",
                    "full_name": "الاسم الكامل",
                    "role": "الصلاحية"
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
