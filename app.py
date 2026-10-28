import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
from fpdf import FPDF
import os
import urllib.request
import arabic_reshaper
from bidi.algorithm import get_display

# استدعاء صفحة التقارير وصفحة الحوكمة والتدقيق الجديدة
from reports_page import show_reports_page
from audit_governance_page import show_governance_page, log_activity

# تحديد المنطقة الزمنية لمدينة عمّان (الأردن)
TZ = ZoneInfo("Asia/Amman")

def now_local():
    return datetime.now(TZ)

def num(x):
    try:
        return 0.0 if pd.isna(x) else float(x)
    except:
        return 0.0

# رابط CSV المباشر لورقة بيانات الموظفين والصناديق
GOOGLE_SHEETS_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSmavjxMii0NOgfAytcirzipjVzUa6eQJBUui7UgPo4dyeHEl2cFfP-_CcmyQ49Dmr2FDEo_e2Ek8ZY/pub?gid=1052037948&single=true&output=csv"

# إعدادات الصفحة
st.set_page_config(
    page_title="نظام التدقيق الداخلي - شركة سويس للصرافة",
    page_icon="💼",
    layout="wide"
)

# إعداد قاعدة البيانات وتحديث هيكل الموظفين تلقائياً إذا لزم الأمر
def init_db():
    conn = sqlite3.connect('swiss_audit_system.db', check_same_thread=False)
    c = conn.cursor()
    
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
    
    c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='employees'")
    _row = c.fetchone()
    if _row and "UNIQUE(branch_no, box_no)" not in (_row[0] or ""):
        c.execute("DROP TABLE employees")
        
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            box_no TEXT,
            employee_name TEXT,
            branch_name TEXT,
            branch_no TEXT,
            UNIQUE(branch_no, box_no)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT,
            full_name TEXT
        )
    ''')
    
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT OR IGNORE INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)", 
                  ("ADMIN", "1234", "مشرف رئيسي", "مدير النظام"))
        conn.commit()

    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect('swiss_audit_system.db', check_same_thread=False)

# دالة مزامنة بيانات الموظفين من Google Sheets
def sync_employees_from_sheets():
    try:
        df_sheet = pd.read_csv(GOOGLE_SHEETS_CSV_URL)
        if df_sheet.shape[1] >= 4:
            df_clean = pd.DataFrame()
            df_clean['branch_no'] = df_sheet.iloc[:, 0]
            df_clean['branch_name'] = df_sheet.iloc[:, 1]
            df_clean['box_no'] = df_sheet.iloc[:, 2]
            df_clean['employee_name'] = df_sheet.iloc[:, 3]
        else:
            return False, "عدد الأعمدة في ملف جوجل شيت أقل من المطلوبة."
            
        df_clean.dropna(subset=['box_no'], inplace=True)
        
        for col in ['box_no', 'employee_name', 'branch_name', 'branch_no']:
            df_clean[col] = df_clean[col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            df_clean[col] = df_clean[col].replace(['nan', 'None', 'null'], '')
            
        df_clean = df_clean[df_clean['box_no'] != '']

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM employees")
        for _, row in df_clean.iterrows():
            c.execute('''
                INSERT OR REPLACE INTO employees (branch_no, branch_name, box_no, employee_name)
                VALUES (?, ?, ?, ?)
            ''', (row['branch_no'], row['branch_name'], row['box_no'], row['employee_name']))
        conn.commit()
        conn.close()
        return True, len(df_clean)
    except Exception as e:
        return False, str(e)

def ar(text):
    if not text:
        return ""
    try:
        text = str(text)
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return str(text)

# دالة توليد تقرير PDF
def generate_pdf_report(df_data, report_title):
    font_path = "Amiri-Regular.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf"
            urllib.request.urlretrieve(url, font_path)
        except:
            pass

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    logo_file = "LOGO-removebg-preview.png"
    if os.path.exists(logo_file):
        try:
            pdf.image(logo_file, x=85, y=10, w=40)
            pdf.ln(22)
        except:
            pass

    if os.path.exists(font_path):
        pdf.add_font("Amiri", fname=font_path)
        pdf.set_font("Amiri", size=16)
    else:
        pdf.set_font("Arial", size=16)
    
    pdf.cell(190, 10, text=ar("شركة سويس للصرافة - تقرير التدقيق الداخلي الأرشيفي"), new_x="LMARGIN", new_y="NEXT", align='C')
    
    if os.path.exists(font_path):
        pdf.set_font("Amiri", size=12)
    else:
        pdf.set_font("Arial", size=12)
        
    pdf.cell(190, 8, text=ar(report_title), new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(8)
    
    if os.path.exists(font_path):
        pdf.set_font("Amiri", size=9)
    else:
        pdf.set_font("Arial", size=9)
        
    headers = [
        ("الوقت", 24), 
        ("الحالة", 20),
        ("النقص", 16), 
        ("الزيادة", 16), 
        ("اسم الموظف", 40), 
        ("رقم الصندوق", 20), 
        ("اسم الفرع", 38), 
        ("رقم الفرع", 16)
    ]
    for i, (h, w) in enumerate(headers):
        last = i == len(headers) - 1
        pdf.cell(w, 8, ar(h), border=1, align='C',
                 new_x="LMARGIN" if last else "RIGHT",
                 new_y="NEXT" if last else "TOP")
    
    for _, row in df_data.iterrows():
        # دعم قراءة المفاتيح سواء كانت بالأسماء العربية أو الإنجليزية
        val_time = str(row.get("الوقت", row.get("audit_time", "")))
        val_status = str(row.get("الحالة", row.get("status", "")))
        val_shortage = str(row.get("النقص", row.get("shortage", 0.0)))
        val_excess = str(row.get("الزيادة", row.get("excess", 0.0)))
        val_emp = str(row.get("اسم الموظف", row.get("employee_name", "")))
        val_box = str(row.get("رقم الصندوق", row.get("box_no", "")))
        val_branch_name = str(row.get("اسم الفرع", row.get("branch_name", "")))
        val_branch_no = str(row.get("رقم الفرع", row.get("branch_no", "")))

        values = [
            (val_time, 24),
            (val_status, 20),
            (val_shortage, 16), 
            (val_excess, 16), 
            (val_emp, 40),
            (val_box, 20), 
            (val_branch_name, 38), 
            (val_branch_no, 16)
        ]
        for i, (v, w) in enumerate(values):
            last = i == len(values) - 1
            pdf.cell(w, 8, ar(v), border=1, align='C',
                     new_x="LMARGIN" if last else "RIGHT",
                     new_y="NEXT" if last else "TOP")
    
    return bytes(pdf.output())

# دالة تلوين الحالة (أخضر لـ مطابق، أحمر لـ غير مطابق، وأزرق لـ مجاز)
def color_status(val):
    if val == "مطابق":
        return 'background-color: #d4edda; color: #155724; font-weight: bold;'
    elif val == "غير مطابق":
        return 'background-color: #f8d7da; color: #721c24; font-weight: bold;'
    elif val == "مجاز":
        return 'background-color: #cce5ff; color: #004085; font-weight: bold;'
    return ''

# حالة تسجيل الدخول
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_role" not in st.session_state:
    st.session_state.user_role = ""

def login_screen():
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        logo_file = "LOGO-removebg-preview.png"
        if os.path.exists(logo_file):
            st.image(logo_file, use_column_width=True)
            
        st.markdown('''
            <div style="background: linear-gradient(135deg, #ffffff 0%, #f9f9f9 100%); padding: 25px; border-radius: 16px; border: 2px solid #d9ea37; text-align: center; margin-bottom: 20px; box-shadow: 0 6px 20px rgba(0,0,0,0.08);">
                <h2 style="color: #111111; font-family: Tahoma; margin-bottom: 5px;">شركة سويس للصرافة</h2>
                <p style="color: #666666; font-size: 14px; font-weight: bold; margin-top: 0;">قسم التدقيق الداخلي والرقابة</p>
            </div>
        ''', unsafe_allow_html=True)
        
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
        logo_file = "LOGO-removebg-preview.png"
        if os.path.exists(logo_file):
            st.image(logo_file, use_column_width=True)
        
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
        "👥 قاعدة بيانات الموظفين والصناديق (Google Sheets)",
        "🔐 تغيير كلمة المرور الشخصية",
        "📊 المؤشرات والتقارير الإحصائية"
    ]
    
    if st.session_state.user_role == "مشرف رئيسي":
        menu_options.insert(3, "🔑 إدارة المستخدمين والصلاحيات")
        menu_options.append("🛡️ الحوكمة والسجل الرقابي")

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
        st.subheader("📋 جدول المتابعة والتدقيق اليومي للحركات (مرتبط بالتاريخ والفرع)")
        
        selected_date = st.date_input("تاريخ التدقيق المطلوب", now_local().date())
        date_str = str(selected_date)
        
        df_emp = pd.read_sql_query("SELECT * FROM employees", conn)
        
        if df_emp.empty:
            st.warning("⚠️ لا توجد بيانات موظفين مسجلة في قاعدة البيانات، جاري سحب البيانات تلقائياً من Google Sheets...")
            success, info = sync_employees_from_sheets()
            if success:
                st.success(f"✅ تم سحب ({info}) سجل من Google Sheets بنجاح!")
                st.rerun()
            else:
                st.error(f"⚠️ تعذر سحب البيانات من Google Sheets: {info}")
        else:
            branch_options = ["الكل"] + list(df_emp['branch_name'].unique())
            branch_filter = st.selectbox("تصفية حسب الفرع:", branch_options)
            
            if branch_filter != "الكل":
                working_df = df_emp[df_emp['branch_name'] == branch_filter].copy()
            else:
                working_df = df_emp.copy()

            df_saved = pd.read_sql_query("SELECT * FROM daily_audit WHERE audit_date = ?", conn, params=(date_str,))
            
            if not df_saved.empty:
                working_df = pd.merge(
                    working_df, 
                    df_saved[['branch_no', 'box_no', 'excess', 'shortage', 'status', 'audit_time', 'notes']], 
                    on=['branch_no', 'box_no'], 
                    how='left'
                )
                working_df.rename(columns={'excess': 'الزيادة', 'shortage': 'النقص', 'status': 'الحالة', 'audit_time': 'الوقت', 'notes': 'الملاحظات'}, inplace=True)
            else:
                working_df["الزيادة"] = 0.0
                working_df["النقص"] = 0.0
                working_df["الحالة"] = None
                working_df["الوقت"] = ""
                working_df["الملاحظات"] = ""

            working_df["الزيادة"] = working_df["الزيادة"].fillna(0.0)
            working_df["النقص"] = working_df["النقص"].fillna(0.0)
            working_df["الوقت"] = working_df["الوقت"].fillna("")
            working_df["الملاحظات"] = working_df["الملاحظات"].fillna("")
            
            working_df["الحالة"] = working_df["الحالة"].where(
                working_df["الحالة"].isin(["مطابق", "غير مطابق", "مجاز"]), None
            )

            working_df = working_df[[
                "branch_no", "branch_name", "box_no", "employee_name", 
                "الزيادة", "النقص", "الحالة", "الوقت", "الملاحظات"
            ]]
            
            styled_filtered_df = working_df.style.map(color_status, subset=['الحالة'])

            edited_df = st.data_editor(
                styled_filtered_df,
                column_config={
                    "branch_no": st.column_config.TextColumn("رقم الفرع", disabled=True),
                    "branch_name": st.column_config.TextColumn("اسم الفرع", disabled=True),
                    "box_no": st.column_config.TextColumn("رقم الصندوق", disabled=True),
                    "employee_name": st.column_config.TextColumn("اسم الموظف", disabled=True),
                    "الزيادة": "الزيادة",
                    "النقص": "النقص",
                    "الحالة": st.column_config.SelectboxColumn(
                        "الحالة ▼ (اختر)",
                        options=["مطابق", "غير مطابق", "مجاز"],
                        required=False,
                        help="اضغط على الخلية لاختيار الحالة، ولحذفها اختر الخلية واضغط Delete",
                    ),
                    "الوقت": st.column_config.TextColumn("الوقت", disabled=True),
                    "الملاحظات": "الملاحظات"
                },
                use_container_width=True,
                hide_index=True,
                key=f"audit_editor_leave_{date_str}_{branch_filter}"
            )

            current_time_str = now_local().strftime("%I:%M:%S %p")
            c = conn.cursor()
            changed = False
            
            for _, row in edited_df.iterrows():
                b_no = str(row["branch_no"])
                box = str(row["box_no"])
                status_val = row["الحالة"] if row["الحالة"] in ("مطابق", "غير مطابق", "مجاز") else None
                excess_v = num(row["الزيادة"])
                shortage_v = num(row["النقص"])
                notes_v = "" if pd.isna(row["الملاحظات"]) else str(row["الملاحظات"])

                c.execute("SELECT id, audit_time, status, excess, shortage, notes FROM daily_audit WHERE audit_date = ? AND branch_no = ? AND box_no = ?", (date_str, b_no, box))
                rec = c.fetchone()

                if status_val:
                    if rec:
                        if (rec[2], rec[3], rec[4], rec[5] or "") != (status_val, excess_v, shortage_v, notes_v):
                            new_time = current_time_str if (rec[2] != status_val or not rec[1]) else rec[1]
                            c.execute('''UPDATE daily_audit
                                         SET excess=?, shortage=?, status=?, notes=?, audit_time=?
                                         WHERE audit_date=? AND branch_no=? AND box_no=?''',
                                      (excess_v, shortage_v, status_val, notes_v, new_time, date_str, b_no, box))
                            changed = True
                            log_activity(conn, st.session_state.username, "تعديل تدقيق يومي", f"تاريخ: {date_str}, فرع: {b_no}, صندوق: {box}, حالة: {status_val}")
                    else:
                        c.execute('''INSERT INTO daily_audit (audit_date, branch_no, branch_name, box_no, employee_name, excess, shortage, status, notes, audit_time)
                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                  (date_str, b_no, str(row["branch_name"]), box, str(row["employee_name"]),
                                   excess_v, shortage_v, status_val, notes_v, current_time_str))
                        changed = True
                        log_activity(conn, st.session_state.username, "إضافة تدقيق يومي جديد", f"تاريخ: {date_str}, فرع: {b_no}, صندوق: {box}, حالة: {status_val}")
                elif rec:
                    c.execute("DELETE FROM daily_audit WHERE audit_date = ? AND branch_no = ? AND box_no = ?", (date_str, b_no, box))
                    changed = True
                    log_activity(conn, st.session_state.username, "حذف تدقيق يومي", f"تاريخ: {date_str}, فرع: {b_no}, صندوق: {box}")

            conn.commit()
            if changed:
                st.rerun()

            st.success(f"⚡ يتم حفظ التعديلات تلقائياً لتاريخ ({date_str}) بشكل فوري ومستقل لكل فرع!")

            # صلاحية المشرف الرئيسي ADMIN لتنظيف السجل اليومي بالكامل
            if st.session_state.username == "ADMIN" and st.session_state.user_role == "مشرف رئيسي":
                with st.expander("🗑️ منطقة خطر: التنظيف الكامل لجدول التدقيق اليومي"):
                    st.error("⚠️ تحذير: هذا الإجراء سيقوم بحذف كافة السجلات اليومية في قاعدة البيانات نهائياً!")
                    confirm_clear_daily = st.checkbox("أؤكد رغبتي في مسح وتنظيف السجل اليومي بالكامل", key="chk_daily_clear")
                    if st.button("🧹 مسح وتنظيف السجل اليومي بالكامل نهائياً", use_container_width=True) and confirm_clear_daily:
                        conn.execute("DELETE FROM daily_audit")
                        conn.commit()
                        log_activity(conn, st.session_state.username, "تنظيف كامل", "تم مسح وتنظيف السجل اليومي بالكامل")
                        st.success("✅ تم تنظيف ومسح السجل اليومي بالكامل بنجاح!")
                        st.rerun()

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
                        pdf_data = generate_pdf_report(df_mismatches, f"تقرير الحالات غير المطابقة ليوم {date_str}")
                        st.download_button(
                            label="📥 تحميل تقرير PDF",
                            data=pdf_data,
                            file_name=f"non_matching_report_{date_str}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

    elif menu == "📁 المطابقات الشهرية والترحيل":
        st.subheader("📁 أرشيف المطابقات الشهرية والترحيل والتقارير المتقدمة")
        st.caption("من هنا يمكنك ترحيل حركات اليوم (مع ترحيل الصناديق غير المدققة تلقائياً كـ 'مجاز'), استعراض الأرشيف، وتصدير التقارير.")
        
        target_date = st.date_input("تاريخ اليوم المراد ترحيله وعرضه", now_local().date(), key="archive_date")
        target_date_str = str(target_date)
        
        col_btn1, col_btn2 = st.columns([1, 2])
        with col_btn1:
            if st.button("📥 تنفيذ ترحيل وتحديث حركات اليوم المحدد", use_container_width=True):
                c = conn.cursor()
                c.execute("SELECT branch_no, branch_name, box_no, employee_name FROM employees")
                all_employees = c.fetchall()
                
                if not all_employees:
                    st.warning("⚠️ لا توجد بيانات موظفين مسجلة في النظام.")
                else:
                    migrated_count = 0
                    updated_count = 0
                    for emp in all_employees:
                        b_no, b_name, box_no, emp_name = emp
                        
                        c.execute("SELECT status, excess, shortage, notes, audit_time FROM daily_audit WHERE audit_date = ? AND branch_no = ? AND box_no = ?", 
                                  (target_date_str, b_no, box_no))
                        daily_rec = c.fetchone()
                        
                        if daily_rec:
                            status_v, excess_v, shortage_v, notes_v, time_v = daily_rec
                        else:
                            status_v = "مجاز"
                            excess_v = 0.0
                            shortage_v = 0.0
                            notes_v = "ترحيل تلقائي - لم يتم الإدخال"
                            time_v = "تلقائي"
                            
                        c.execute("SELECT id FROM monthly_audit_archive WHERE audit_date = ? AND branch_no = ? AND box_no = ?", 
                                  (target_date_str, b_no, box_no))
                        existing_archive = c.fetchone()
                        
                        if existing_archive:
                            c.execute('''
                                UPDATE monthly_audit_archive 
                                SET branch_name = ?, employee_name = ?, excess = ?, shortage = ?, status = ?, notes = ?, audit_time = ?
                                WHERE audit_date = ? AND branch_no = ? AND box_no = ?
                            ''', (b_name, emp_name, excess_v, shortage_v, status_v, notes_v, time_v, target_date_str, b_no, box_no))
                            updated_count += 1
                        else:
                            c.execute('''
                                INSERT INTO monthly_audit_archive (audit_date, branch_no, branch_name, box_no, employee_name, excess, shortage, status, notes, audit_time)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (target_date_str, b_no, b_name, box_no, emp_name, excess_v, shortage_v, status_v, notes_v, time_v))
                            migrated_count += 1
                            
                    conn.commit()
                    log_activity(conn, st.session_state.username, "ترحيل أرشيف", f"تاريخ الترحيل: {target_date_str} (إدراج: {migrated_count}, تحديث: {updated_count})")
                    st.success(f"✅ تمت عملية المزامنة والترحيل بنجاح! (تم إدراج {migrated_count} سجل جديد، وتحديث {updated_count} سجل معدل لتاريخ {target_date_str})")
                    st.rerun()
        
        st.write("---")
        st.markdown("##### 📊 استعراض وتصدير تقارير الأرشيف المتقدمة والمخصصة")
        
        df_all_archive = pd.read_sql_query("SELECT DISTINCT branch_name, box_no, employee_name FROM monthly_audit_archive", conn)
        
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            start_p_date = st.date_input("من تاريخ", now_local().date(), key="start_p")
        with col_f2:
            end_p_date = st.date_input("إلى تاريخ", now_local().date(), key="end_p")
        with col_f3:
            branch_options = ["الكل"] + (df_all_archive['branch_name'].dropna().unique().tolist() if not df_all_archive.empty else [])
            selected_branch_filter = st.selectbox("تصفية حسب الفرع:", branch_options)
        with col_f4:
            box_options = ["الكل"] + (df_all_archive['box_no'].dropna().unique().tolist() if not df_all_archive.empty else [])
            selected_box_filter = st.selectbox("تصفية حسب رقم الصندوق:", box_options)

        query = "SELECT * FROM monthly_audit_archive WHERE audit_date BETWEEN ? AND ?"
        params = [str(start_p_date), str(end_p_date)]
        
        if selected_branch_filter != "الكل":
            query += " AND branch_name = ?"
            params.append(selected_branch_filter)
            
        if selected_box_filter != "الكل":
            query += " AND box_no = ?"
            params.append(selected_box_filter)
            
        df_export = pd.read_sql_query(query, conn, params=params)
        report_title_str = f"تقرير الفترة من {start_p_date} إلى {end_p_date} (فرع: {selected_branch_filter}, صندوق: {selected_box_filter})"

        if df_export.empty:
            st.info("⚠️ لا توجد سجلات مطابقة لمعايير البحث المحددة في الأرشيف.")
        else:
            st.success(f"✅ تم العثور على ({len(df_export)}) سجل تطابق خيارات الفلترة المطلوبة.")
            
            df_styled_view = df_export.rename(columns={
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
            }).style.map(color_status, subset=['الحالة'])
            
            st.dataframe(df_styled_view, use_container_width=True)
            
            st.markdown("##### 📥 تصدير وطباعة التقرير المخصص:")
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                excel_data = df_export.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📊 تحميل كملف Excel / CSV",
                    data=excel_data,
                    file_name=f"custom_audit_report.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                    
            with col_exp2:
                pdf_archive_data = generate_pdf_report(df_export, report_title_str)
                st.download_button(
                    label="📄 تحميل كملف PDF",
                    data=pdf_archive_data,
                    file_name=f"custom_audit_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

        st.write("---")
        with st.expander("🗑️ إدارة وحذف سجل تجريبي أو خاطئ محدد"):
            del_date = st.date_input("تاريخ السجل المراد حذفه", now_local().date(), key="del_date_picker")
            del_date_str = str(del_date)
            
            df_day_records = pd.read_sql_query(
                "SELECT audit_date, branch_no, branch_name, box_no, employee_name FROM monthly_audit_archive WHERE audit_date = ?",
                conn, params=(del_date_str,))
            if df_day_records.empty:
                df_day_records = pd.read_sql_query(
                    "SELECT audit_date, branch_no, branch_name, box_no, employee_name FROM daily_audit WHERE audit_date = ?",
                    conn, params=(del_date_str,))
            
            if df_day_records.empty:
                st.info(f"⚠️ لا توجد أي سجلات مسجلة لتاريخ ({del_date_str}).")
            else:
                idx = st.selectbox(
                    "اختر الصندوق أو السجل المراد حذفه:",
                    options=list(df_day_records.index),
                    format_func=lambda i: f"{df_day_records.loc[i, 'branch_name']} - صندوق {df_day_records.loc[i, 'box_no']} ({df_day_records.loc[i, 'employee_name']})"
                )
                if st.button("🗑️ حذف هذا السجل نهائياً", use_container_width=True):
                    r = df_day_records.loc[idx]
                    for tbl in ("monthly_audit_archive", "daily_audit"):
                        conn.execute(f"DELETE FROM {tbl} WHERE audit_date = ? AND branch_no = ? AND box_no = ?",
                                     (del_date_str, r["branch_no"], r["box_no"]))
                    conn.commit()
                    log_activity(conn, st.session_state.username, "حذف سجل محدد", f"تاريخ: {del_date_str}, فرع: {r['branch_name']}, صندوق: {r['box_no']}")
                    st.success(f"✅ تم حذف سجل الصندوق ({r['box_no']}) في ({r['branch_name']}) لتاريخ ({del_date_str}).")
                    st.rerun()

        # صلاحية المشرف الرئيسي ADMIN لتنظيف الأرشيف الشهري بالكامل
        if st.session_state.username == "ADMIN" and st.session_state.user_role == "مشرف رئيسي":
            with st.expander("🗑️ منطقة خطر: التنظيف الكامل لأرشيف المطابقات الشهرية"):
                st.error("⚠️ تحذير: هذا الإجراء سيقوم بحذف كافة السجلات والأرشيف الشهري بالكامل وبشكل نهائي!")
                confirm_clear_archive = st.checkbox("أؤكد رغبتي في مسح وتنظيف الأرشيف الشهري بالكامل", key="chk_archive_clear")
                if st.button("🧹 مسح وتنظيف الأرشيف الشهري بالكامل نهائياً", use_container_width=True) and confirm_clear_archive:
                    conn.execute("DELETE FROM monthly_audit_archive")
                    conn.commit()
                    log_activity(conn, st.session_state.username, "تنظيف كامل أرشيف", "تم مسح وتنظيف أرشيف المطابقات الشهرية بالكامل")
                    st.success("✅ تم تنظيف ومسح أرشيف المطابقات الشهرية بالكامل بنجاح!")
                    st.rerun()

    elif menu == "👥 قاعدة بيانات الموظفين والصناديق (Google Sheets)":
        st.subheader("👥 إدارة قاعدة بيانات الموظفين والصناديق والفروع")
        st.caption("البيانات مرتبطة تلقائياً وبشكل حي مع ملف Google Sheets الخاص بشركة سويس للصرافة.")
        
        if st.button("🔄 مزامنة وتحديث البيانات من Google Sheets الآن", use_container_width=True):
            with st.spinner("جاري الاتصال بـ Google Sheets وتحديث البيانات..."):
                success, info = sync_employees_from_sheets()
                if success:
                    log_activity(conn, st.session_state.username, "مزامنة Google Sheets", f"تم تحديث ({info}) سجل")
                    st.success(f"✅ تم المزامنة بنجاح! تم تحديث ({info}) سجل موظف وصندوق.")
                    st.rerun()
                else:
                    st.error(f"❌ تعذرت المزامنة: {info}")
                    
        st.write("---")
        st.markdown("##### 📊 السجلات الحالية المخزنة والمحدثة من Google Sheets")
        df_current = pd.read_sql_query("SELECT branch_no, branch_name, box_no, employee_name FROM employees", conn)
        if df_current.empty:
            st.info("لا توجد بيانات مسجلة حالياً، اضغط على زر المزامنة أعلاه لتحديث البيانات.")
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
                            log_activity(conn, st.session_state.username, "تغيير كلمة المرور", "تم تغيير كلمة المرور الشخصية بنجاح")
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
                                log_activity(conn, st.session_state.username, "إضافة مستخدم", f"تم إضافة المستخدم الجديد: {new_user}")
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
                        log_activity(conn, st.session_state.username, "تعديل مستخدم", f"تم تعديل بيانات المستخدم: {selected_target_user}")
                        st.success(f"تم تحديث بيانات المستخدم ({selected_target_user}) بنجاح!")
                        st.rerun()
                        
                    if delete_btn and selected_target_user:
                        if selected_target_user == "ADMIN":
                            st.error("⚠️ لا يمكن حذف حساب المشرف الرئيسي (ADMIN) الأساسي للنظام!")
                        else:
                            c = conn.cursor()
                            c.execute("DELETE FROM users WHERE username = ?", (selected_target_user,))
                            conn.commit()
                            log_activity(conn, st.session_state.username, "حذف مستخدم", f"تم حذف المستخدم: {selected_target_user}")
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
        show_reports_page(conn)

    elif menu == "🛡️ الحوكمة والسجل الرقابي":
        show_governance_page(conn)

    conn.close()

if not st.session_state.logged_in:
    login_screen()
else:
    main_app()
