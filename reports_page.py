import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os
import urllib.request
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display

def ar(text):
    if not text:
        return ""
    try:
        text = str(text)
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return str(text)

# دالة توليد تقرير PDF للمتكررين (3 مرات فأكثر)
def generate_non_matching_pdf(df_data, report_title):
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
        pdf.set_font("Amiri", size=15)
    else:
        pdf.set_font("Arial", size=15)
    
    pdf.cell(190, 10, text=ar("شركة سويس للصرافة - قسم التدقيق الداخلي والرقابة"), new_x="LMARGIN", new_y="NEXT", align='C')
    
    if os.path.exists(font_path):
        pdf.set_font("Amiri", size=12)
    else:
        pdf.set_font("Arial", size=12)
        
    pdf.cell(190, 8, text=ar(report_title), new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(6)
    
    if os.path.exists(font_path):
        pdf.set_font("Amiri", size=9)
    else:
        pdf.set_font("Arial", size=9)
        
    headers = [
        ("عدد أرقام غ.م", 30), 
        ("اسم الموظف", 50), 
        ("رقم الصندوق", 25), 
        ("اسم الفرع", 55), 
        ("رقم الفرع", 30)
    ]
    
    for i, (h, w) in enumerate(headers):
        last = i == len(headers) - 1
        pdf.cell(w, 8, ar(h), border=1, align='C',
                 new_x="LMARGIN" if last else "RIGHT",
                 new_y="NEXT" if last else "TOP")
    
    for _, row in df_data.iterrows():
        values = [
            (str(row.get("non_match_count", 0)), 30),
            (str(row.get("employee_name", "")), 50),
            (str(row.get("box_no", "")), 25),
            (str(row.get("branch_name", "")), 55),
            (str(row.get("branch_no", "")), 30)
        ]
        for i, (v, w) in enumerate(values):
            last = i == len(values) - 1
            pdf.cell(w, 8, ar(v), border=1, align='C',
                     new_x="LMARGIN" if last else "RIGHT",
                     new_y="NEXT" if last else "TOP")
    
    return bytes(pdf.output())

# الدالة الرئيسية لعرض صفحة التقارير والمؤشرات
def show_reports_page(conn):
    st.markdown("### 📊 لوحة المؤشرات والتقارير الإحصائية والرقابية")
    st.caption("مركز التقارير التحليلية وتقييم المخاطر والأداء لشركة سويس للصرافة")
    st.write("---")

    # 1. المربع الأول: تقرير المخالفات المتكررة (3 مرات فأكثر)
    with st.container():
        st.markdown('''
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border-right: 5px solid #c53030; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px;">
                <h4 style="margin:0; color: #c53030;">🚨 1. تقرير الحالات غير المطابقة المتكررة (3 مرات فأكثر)</h4>
                <p style="margin:5px 0 0 0; font-size: 13px; color: #666;">رصد الموظفين والصناديق التي حصلت على 3 شارات غير مطابق أو أكثر واستخراج تقرير PDF عاجل.</p>
            </div>
        ''', unsafe_allow_html=True)
        
        # استعلام محسّن لحساب الأيام الفريدة غير المطابقة من جدول الأرشيف لمنع تضاعف العدد
        query_repeat = '''
            SELECT branch_no, branch_name, box_no, employee_name, COUNT(DISTINCT audit_date) as non_match_count
            FROM monthly_audit_archive
            WHERE status = 'غير مطابق'
            GROUP BY branch_no, box_no, employee_name
            HAVING non_match_count >= 3
            ORDER BY non_match_count DESC
        '''
        df_repeat = pd.read_sql_query(query_repeat, conn)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            if df_repeat.empty:
                st.info("🎉 لا يوجد حالياً أي موظف تجاوز 3 مخالفات غير مطابقة في الأرشيف الشهري.")
            else:
                st.dataframe(df_repeat.rename(columns={
                    "branch_no": "رقم الفرع",
                    "branch_name": "اسم الفرع",
                    "box_no": "رقم الصندوق",
                    "employee_name": "اسم الموظف",
                    "non_match_count": "تكرار غير مطابق"
                }), use_container_width=True, hide_index=True)
        
        with col2:
            if not df_repeat.empty:
                pdf_data = generate_non_matching_pdf(df_repeat, "تقرير الموظفين الأكثر تكراراً لحالات عدم المطابقة (3 فأكثر)")
                st.download_button(
                    label="📄 تحميل تقرير PDF للمتكررين",
                    data=pdf_data,
                    file_name="repeated_non_matching_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

    st.write("---")

    # 2. المربع الثاني: تقرير الأداء الشامل والالتزام
    with st.container():
        st.markdown('''
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border-right: 5px solid #2b6cb0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px;">
                <h4 style="margin:0; color: #2b6cb0;">🏆 2. تقرير الأداء الشامل ونسب الالتزام</h4>
                <p style="margin:5px 0 0 0; font-size: 13px; color: #666;">مقارنة التزام الفروع والموظفين بناءً على أيام المطابقة، عدم المطابقة والإجازات.</p>
            </div>
        ''', unsafe_allow_html=True)
        
        df_perf = pd.read_sql_query('''
            SELECT branch_name, 
                   COUNT(CASE WHEN status = 'مطابق' THEN 1 END) as matches,
                   COUNT(CASE WHEN status = 'غير مطابق' THEN 1 END) as non_matches,
                   COUNT(CASE WHEN status = 'مجاز' THEN 1 END) as leaves
            FROM monthly_audit_archive
            GROUP BY branch_name
        ''', conn)
        
        if df_perf.empty:
            st.info("⚠️ لا توجد بيانات كافية في الأرشيف لحساب نسبة الأداء بعد.")
        else:
            df_perf["إجمالي الأيام"] = df_perf["matches"] + df_perf["non_matches"]
            df_perf["نسبة الالتزام"] = (df_perf["matches"] / df_perf["إجمالي الأيام"] * 100).fillna(0).round(1).astype(str) + "%"
            st.dataframe(df_perf.rename(columns={
                "branch_name": "اسم الفرع",
                "matches": "أيام مطابقة",
                "non_matches": "أيام غير مطابقة",
                "leaves": "أيام مجاز"
            }), use_container_width=True, hide_index=True)

    st.write("---")

    # 3. المربع الثالث: تقرير تقييم المخاطر الرقابية
    with st.container():
        st.markdown('''
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border-right: 5px solid #dd6b20; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px;">
                <h4 style="margin:0; color: #dd6b20;">⚠️ 3. تقرير مصفوفة المخاطر وأولويات التفتيش الميداني</h4>
                <p style="margin:5px 0 0 0; font-size: 13px; color: #666;">تحليل درجة الخطر لكل فرع واستهداف الجولات التفتيشية الميدانية.</p>
            </div>
        ''', unsafe_allow_html=True)
        
        df_risk = pd.read_sql_query('''
            SELECT branch_name, 
                   COUNT(CASE WHEN status = 'غير مطابق' THEN 1 END) as total_non_matches
            FROM monthly_audit_archive
            GROUP BY branch_name
            ORDER BY total_non_matches DESC
        ''', conn)
        
        if df_risk.empty:
            st.info("🟢 جميع الفروع ضمن نطاق المخاطر المنخفض حالياً.")
        else:
            st.dataframe(df_risk.rename(columns={
                "branch_name": "اسم الفرع",
                "total_non_matches": "إجمالي حالات عدم المطابقة"
            }), use_container_width=True, hide_index=True)

    st.write("---")

    # 4. المربع الرابع: نتائج وتطور الفترات السابقة
    with st.container():
        st.markdown('''
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border-right: 5px solid #2f855a; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px;">
                <h4 style="margin:0; color: #2f855a;">📈 4. تقرير نتائج وتطور الفترات السابقة</h4>
                <p style="margin:5px 0 0 0; font-size: 13px; color: #666;">متابعة خط اتجاه الالتزام والمخالفات عبر الأشهر والأيام السابقة.</p>
            </div>
        ''', unsafe_allow_html=True)
        
        df_trends = pd.read_sql_query('''
            SELECT audit_date as التاريخ,
                   COUNT(CASE WHEN status = 'مطابق' THEN 1 END) as المطابق,
                   COUNT(CASE WHEN status = 'غير مطابق' THEN 1 END) as غير_المطابق
            FROM monthly_audit_archive
            GROUP BY audit_date
            ORDER BY audit_date DESC
            LIMIT 30
        ''', conn)
        
        if df_trends.empty:
            st.info("⚠️ لا توجد سجلات تاريخية سابقة لعرض الاتجاهات.")
        else:
            st.line_chart(df_trends.set_index("التاريخ"))
