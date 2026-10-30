import streamlit as pd_st # للتمييز إذا لزم، أو استخدم st العادي
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from fpdf import FPDF
import os
import urllib.request
import arabic_reshaper
from bidi.algorithm import get_display

TZ = ZoneInfo("Asia/Amman")

def now_local():
    return datetime.now(TZ)

def ar(text):
    if not text:
        return ""
    try:
        text = str(text)
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return str(text)

def init_closing_db(conn):
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS shortage_closings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            closing_date TEXT,
            branch_no TEXT,
            branch_name TEXT,
            box_no TEXT,
            employee_name TEXT,
            diff_date TEXT,
            amount REAL,
            username TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()

def generate_closing_pdf(df_items, c_date, current_username):
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
        pdf.set_font("Amiri", size=14)
    else:
        pdf.set_font("Arial", size=14)
    
    pdf.cell(190, 8, text=ar("شركة سويس للصرافة"), new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(190, 8, text=ar("قسم التدقيق الداخلي والرقابة"), new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(5)
    
    if os.path.exists(font_path):
        pdf.set_font("Amiri", size=12)
    else:
        pdf.set_font("Arial", size=12)

    pdf.cell(190, 8, text=ar("اقفال فروقات/النقص"), new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(5)

    pdf.cell(190, 8, text=ar(f"التاريخ: {c_date}"), new_x="LMARGIN", new_y="NEXT", align='R')
    pdf.cell(190, 8, text=ar("الى :- قسم المحاسبة"), new_x="LMARGIN", new_y="NEXT", align='R')
    pdf.ln(5)

    pdf.set_font("Amiri", size=11)
    pdf.cell(190, 8, text=ar("يرجى تحويل فروقات جرد الخزينة في الفروع من حسابات الصناديق, حسب البيان التالي :"), new_x="LMARGIN", new_y="NEXT", align='R')
    pdf.ln(3)

    headers = [("قيمة الفرق", 35), ("تاريخ الفرق", 35), ("اسم صاحب العهدة", 45), ("الفرع", 40), ("رقم الصندوق", 35)]
    for i, (h, w) in enumerate(headers):
        last = i == len(headers) - 1
        pdf.cell(w, 8, ar(h), border=1, align='C', new_x="LMARGIN" if last else "RIGHT", new_y="NEXT" if last else "TOP")

    for _, row in df_items.iterrows():
        vals = [
            (str(row["قيمة الفرق"]), 35),
            (str(row["تاريخ الفرق"]), 35),
            (str(row["اسم صاحب العهدة"]), 45),
            (str(row["الفرع"]), 40),
            (str(row["رقم الصندوق"]), 35)
        ]
        for i, (v, w) in enumerate(vals):
            last = i == len(vals) - 1
            pdf.cell(w, 8, ar(v), border=1, align='C', new_x="LMARGIN" if last else "RIGHT", new_y="NEXT" if last else "TOP")

    pdf.ln(20)
    pdf.set_font("Amiri", size=10)
    sign_text = f"المدقق الداخلي: {current_username} - الاعتماد الرقمي: {now_local().strftime('%Y-%m-%d %I:%M:%S %p')}"
    pdf.cell(190, 8, text=ar(sign_text), new_x="LMARGIN", new_y="NEXT", align='R')
    
    pdf.ln(15)
    pdf.cell(190, 8, text=ar("لاستعمال قسم المحاسبة ........................................................................ المدير المالي"), new_x="LMARGIN", new_y="NEXT", align='R')

    return bytes(pdf.output())

def show_shortage_closing_page(conn):
    init_closing_db(conn)

    st.markdown('''
        <div style="background-color: #ffffff; padding: 18px; border-radius: 12px; border-right: 6px solid #d9ea37; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 20px; text-align: center;">
            <h2 style="color: #111111; margin: 0; font-size: 22px;">شركة سويس للصرافة | قسم التدقيق الداخلي والرقابة</h2>
            <p style="color: #666666; margin: 4px 0 0 0; font-size: 13px;">نموذج إقفال فروقات / النقص الموجه إلى قسم المحاسبة</p>
        </div>
    ''', unsafe_allow_html=True)

    st.subheader("📁 إنشاء وتصدير نموذج إقفال النقوصات")
    st.caption("يرجى اختيار الصندوق لجلب بيانات الموظف والفرع تلقائياً وتوليد نموذج الإقفال المعتمد.")

    col_h1, col_h2 = st.columns(2)
    with col_h1:
        form_date = st.date_input("تاريخ النموذج", now_local().date(), key="closing_form_date")
    with col_h2:
        st.text_input("الى:", value="قسم المحاسبة", disabled=True, key="to_dept_disabled")

    st.markdown("**يرجى تحويل فروقات جرد الخزينة في الفروع من حسابات الصناديق، حسب البيان التالي:**")

    df_emps = pd.read_sql_query("SELECT DISTINCT branch_no, branch_name, box_no, employee_name FROM employees", conn)
    
    if df_emps.empty:
        st.warning("⚠️ لا توجد بيانات موظفين مسجلة. يرجى مزامنة بيانات الموظفين أولاً.")
    else:
        df_emps['display_label'] = df_emps['branch_name'] + " - صندوق " + df_emps['box_no'] + " (" + df_emps['employee_name'] + ")"
        
        selected_box_label = st.selectbox("اختر الصندوق المطلوب إقفال نقصه:", df_emps['display_label'].tolist())
        
        selected_row = df_emps[df_emps['display_label'] == selected_box_label].iloc[0]
        
        b_no = selected_row['branch_no']
        b_name = selected_row['branch_name']
        box_no = selected_row['box_no']
        emp_name = selected_row['employee_name']

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            diff_date = st.date_input("تاريخ الفرق", now_local().date(), key="diff_date_val")
        with col_d2:
            diff_amount = st.number_input("قيمة الفرق (النقص)", min_value=0.0, step=0.1, key="diff_amount_val")

        if st.button("➕ إضافة البيان إلى جدول الإقفال", use_container_width=True):
            c = conn.cursor()
            c.execute('''
                INSERT INTO shortage_closings (closing_date, branch_no, branch_name, box_no, employee_name, diff_date, amount, username, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (str(form_date), str(b_no), str(b_name), str(box_no), str(emp_name), str(diff_date), float(diff_amount), st.session_state.username, now_local().strftime("%Y-%m-%d %I:%M:%S %p")))
            conn.commit()
            st.success("✅ تمت إضافة البيان إلى قائمة الإقفال بنجاح!")
            st.rerun()

    st.write("---")
    st.markdown("##### 📋 البيان الحالي لإقفال النقصانات المسجلة لهذا النموذج:")
    
    df_closings = pd.read_sql_query("SELECT id, box_no AS 'رقم الصندوق', branch_name AS 'الفرع', employee_name AS 'اسم صاحب العهدة', diff_date AS 'تاريخ الفرق', amount AS 'قيمة الفرق' FROM shortage_closings WHERE closing_date = ?", conn, params=(str(form_date),))
    
    if df_closings.empty:
        st.info("لا توجد بيانات مسجلة في هذا النموذج حتى الآن.")
    else:
        st.dataframe(df_closings.drop(columns=['id']), use_container_width=True, hide_index=True)

        item_to_delete = st.selectbox("اختر البيان المراد حذفه من القائمة (إن وجد):", options=df_closings['رقم الصندوق'].tolist(), key="del_closing_item")
        if st.button("🗑️ حذف البيان المختار", use_container_width=True):
            conn.execute("DELETE FROM shortage_closings WHERE closing_date = ? AND box_no = ?", (str(form_date), item_to_delete))
            conn.commit()
            st.success("تم حذف البيان بنجاح.")
            st.rerun()

        st.write("---")
        pdf_closing_data = generate_closing_pdf(df_closings, str(form_date), st.session_state.username)
        st.download_button(
            label="📄 تحميل نموذج إقفال النقصانات المعتمد (PDF)",
            data=pdf_closing_data,
            file_name=f"shortage_closing_report_{form_date}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
