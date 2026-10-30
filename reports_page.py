import streamlit as st
import pandas as pd
import urllib.request
import os
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

def generate_pdf_report_generic(df_data, report_title):
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
    
    pdf.cell(190, 10, text=ar("شركة سويس للصرافة - تقرير المؤشرات والإحصاءات"), new_x="LMARGIN", new_y="NEXT", align='C')
    
    if os.path.exists(font_path):
        pdf.set_font("Amiri", size=12)
    else:
        pdf.set_font("Arial", size=12)
        
    pdf.cell(190, 8, text=ar(report_title), new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(8)
    
    if df_data.empty:
        pdf.cell(190, 10, text=ar("لا توجد بيانات متاحة لهذا التقرير."), new_x="LMARGIN", new_y="NEXT", align='C')
    else:
        if os.path.exists(font_path):
            pdf.set_font("Amiri", size=9)
        else:
            pdf.set_font("Arial", size=9)
            
        columns = list(df_data.columns)
        col_width = 190 / len(columns) if len(columns) > 0 else 190
        
        for i, col_name in enumerate(columns):
            last = i == len(columns) - 1
            pdf.cell(col_width, 8, ar(str(col_name)), border=1, align='C',
                     new_x="LMARGIN" if last else "RIGHT",
                     new_y="NEXT" if last else "TOP")
            
        for _, row in df_data.iterrows():
            for i, col_name in enumerate(columns):
                last = i == len(columns) - 1
                val = str(row[col_name])
                pdf.cell(col_width, 8, ar(val), border=1, align='C',
                         new_x="LMARGIN" if last else "RIGHT",
                         new_y="NEXT" if last else "TOP")

    # توقيع اسم المستخدم في أسفل التقرير
    pdf.ln(15)
    if os.path.exists(font_path):
        pdf.set_font("Amiri", size=10)
    else:
        pdf.set_font("Arial", size=10)
        
    current_user = st.session_state.get("username", "ADMIN")
    sign_text = f"تم التدقيق والاعتماد الرقمي بواسطة المستخدم: {current_user}"
    pdf.cell(190, 8, text=ar(sign_text), new_x="LMARGIN", new_y="NEXT", align='R')
    
    return bytes(pdf.output())

def show_reports_page(conn):
    st.markdown("### 📊 لوحة المؤشرات والتقارير الإحصائية (Metro Dashboard)")
    st.caption("مركز التقارير التحليلية وتقييم المخاطر والأداء لشركة سويس للصرافة")
    st.write("---")

    # تقسيم الواجهة إلى 3 مربعات متساوية بجانب بعضها (طراز ويندوز فون)
    col1, col2, col3 = st.columns(3)

    # المربع الأول: الحالات المتكررة
    with col1:
        st.markdown('''
            <div style="background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%); padding: 20px; border-radius: 12px; border: 2px solid #feb2b2; text-align: center; height: 240px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <h3 style="color: #9b2c2c; margin: 0 0 10px 0; font-size: 18px;">🚨 الحالات المتكررة</h3>
                    <p style="color: #742a2a; font-size: 12px; margin: 0;">رصد الموظفين والصناديق التي حصلت على 3 مخالفات فأكثر.</p>
                </div>
                <div style="background-color: #ffffff; padding: 10px; border-radius: 8px; font-weight: bold; color: #9b2c2c; font-size: 13px;">
                    تقرير المخالفات المتكررة
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        btn_box1 = st.button("عرض مربع الحالات المتكررة", use_container_width=True, key="btn_tile_1")

    # المربع الثاني: الأداء الشامل
    with col2:
        st.markdown('''
            <div style="background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%); padding: 20px; border-radius: 12px; border: 2px solid #90cdf4; text-align: center; height: 240px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <h3 style="color: #2b6cb0; margin: 0 0 10px 0; font-size: 18px;">📊 الأداء الشامل</h3>
                    <p style="color: #2c5282; font-size: 12px; margin: 0;">مقارنة التزام الفروع والموظفين بناءً على المطابقة والإجازات.</p>
                </div>
                <div style="background-color: #ffffff; padding: 10px; border-radius: 8px; font-weight: bold; color: #2b6cb0; font-size: 13px;">
                    تقرير نسب الالتزام
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        btn_box2 = st.button("عرض مربع الأداء الشامل", use_container_width=True, key="btn_tile_2")

    # المربع الثالث: مصفوفة المخاطر
    with col3:
        st.markdown('''
            <div style="background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%); padding: 20px; border-radius: 12px; border: 2px solid #cbd5e0; text-align: center; height: 240px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <h3 style="color: #2d3748; margin: 0 0 10px 0; font-size: 18px;">⚠️ مصفوفة المخاطر</h3>
                    <p style="color: #4a5568; font-size: 12px; margin: 0;">تحليل درجة الخطر لكل فرع واستهداف الجولات التفتيشية.</p>
                </div>
                <div style="background-color: #ffffff; padding: 10px; border-radius: 8px; font-weight: bold; color: #2d3748; font-size: 13px;">
                    تقرير مصفوفة المخاطر
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        btn_box3 = st.button("عرض مربع مصفوفة المخاطر", use_container_width=True, key="btn_tile_3")

    st.write("---")

    # عرض محتوى المربع المحدد تفاعلياً عند الضغط عليه
    if btn_box1 or "active_tile" not in st.session_state:
        st.session_state.active_tile = 1

    if btn_box2:
        st.session_state.active_tile = 2

    if btn_box3:
        st.session_state.active_tile = 3

    # محتوى المربع الأول
    if st.session_state.active_tile == 1:
        st.markdown("#### 🚨 تفاصيل تقرير الحالات غير المطابقة المتكررة (3 مرات فأكثر)")
        df_repeat = pd.read_sql_query('''
            SELECT employee_name AS "اسم الموظف", branch_name AS "اسم الفرع", box_no AS "رقم الصندوق", COUNT(*) AS "عدد المخالفات"
            FROM monthly_audit_archive
            WHERE status = 'غير مطابق'
            GROUP BY employee_name, branch_name, box_no
            HAVING COUNT(*) >= 3
            ORDER BY COUNT(*) DESC
        ''', conn)
        
        if df_repeat.empty:
            st.info("🎉 لا توجد حالياً أي حالات لموظفين تجاوزوا 3 مخالفات غير مطابقة في الأرشيف الشهري.")
        else:
            st.dataframe(df_repeat, use_container_width=True, hide_index=True)
            pdf_data = generate_pdf_report_generic(df_repeat, "تقرير الحالات المتكررة (3 مرات فأكثر)")
            st.download_button("📥 تحميل التقرير كملف PDF", data=pdf_data, file_name="repeat_violations_report.pdf", mime="application/pdf", use_container_width=True)

    # محتوى المربع الثاني
    elif st.session_state.active_tile == 2:
        st.markdown("#### 📊 تفاصيل تقرير الأداء الشامل ونسب الالتزام للموظفين")
        df_all_arch = pd.read_sql_query("SELECT employee_name, status FROM monthly_audit_archive WHERE employee_name IS NOT NULL AND employee_name != ''", conn)
        
        if df_all_arch.empty:
            st.info("⚠️ لا توجد بيانات مؤرشفة كافية لحساب نسبة الأداء.")
        else:
            summary_list = []
            for emp in df_all_arch['employee_name'].unique():
                emp_df = df_all_arch[df_all_arch['employee_name'] == emp]
                total = len(emp_df)
                matches = len(emp_df[emp_df['status'] == 'مطابق'])
                leaves = len(emp_df[emp_df['status'] == 'مجاز'])
                effective_days = total - leaves
                rate = round((matches / effective_days * 100), 1) if effective_days > 0 else 100.0
                summary_list.append({"اسم الموظف": emp, "إجمالي الأيام": total, "أيام المطابقة": matches, "أيام الإجازات/المجاز": leaves, "نسبة الالتزام %": rate})
            
            df_scorecard = pd.DataFrame(summary_list).sort_values(by="نسبة الالتزام %", ascending=False)
            st.dataframe(df_scorecard, use_container_width=True, hide_index=True)
            pdf_data = generate_pdf_report_generic(df_scorecard, "تقرير الأداء الشامل ونسب الالتزام")
            st.download_button("📥 تحميل التقرير كملف PDF", data=pdf_data, file_name="comprehensive_performance_report.pdf", mime="application/pdf", use_container_width=True)

    # محتوى المربع الثالث
    elif st.session_state.active_tile == 3:
        st.markdown("#### ⚠️ تفاصيل تقرير مصفوفة المخاطر وأولويات التفتيش الميداني")
        df_risk = pd.read_sql_query('''
            SELECT branch_name AS "اسم الفرع", 
                   SUM(CASE WHEN status = 'غير مطابق' THEN 1 ELSE 0 END) as "عدد المخالفات",
                   COUNT(*) as "إجمالي التدقيقات"
            FROM monthly_audit_archive
            GROUP BY branch_name
            ORDER BY "عدد المخالفات" DESC
        ''', conn)
        
        if df_risk.empty:
            st.info("ℹ️ جميع الفروع ضمن نطاق المخاطر المنخفض حالياً.")
        else:
            st.dataframe(df_risk, use_container_width=True, hide_index=True)
            pdf_data = generate_pdf_report_generic(df_risk, "تقرير مصفوفة المخاطر والأولويات الميدانية")
            st.download_button("📥 تحميل التقرير كملف PDF", data=pdf_data, file_name="risk_matrix_report.pdf", mime="application/pdf", use_container_width=True)
