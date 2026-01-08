import pandas as pd
import json
import numpy as np

df = pd.read_csv("PV S3-DSI_2024-2025_finale.xls - Worksheet.csv", header=None)
# df = pd.read_csv("PV S3-DSI_2024-2025_finale.xls - Worksheet.csv", header=None)

year = "2024-2025"
# دالة لتحويل NaN إلى 0
def clean_value(value):
    """تحويل NaN/None إلى 0 للقيم الرقمية، أو None للقيم النصية"""
    if pd.isna(value) or value is None:
        return 0
    # إذا كانت القيمة نصية فارغة
    if isinstance(value, str) and value.strip() == "":
        return 0
    return value

semester = "S" + str(df.iloc[0, 1])

modules = []
col_idx = 4

while True:
    try:
        value = df.iloc[1, col_idx]
    except:
        break

    if isinstance(value, str) and ":" in value:
        code, name = value.split(":", 1)
        modules.append({
            "code": code.strip(),
            "name": name.strip(),
            "start_col": col_idx
        })

    col_idx += 1

# إضافة end_col تلقائياً
for i in range(len(modules)):
    if i < len(modules) - 1:
        modules[i]["end_col"] = modules[i + 1]["start_col"] - 1
    else:
        modules[i]["end_col"] = col_idx - 2  # آخر module

# ========== استخراج بيانات الطلاب ==========
students = {}  

for row in range(6, len(df)):
    dept = df.iloc[row, 0]
    matricule = df.iloc[row, 1]
    prenom = df.iloc[row, 2]
    nom = df.iloc[row, 3]

    if pd.isna(matricule):
        continue

    students[int(matricule)] = {  
        "matricule": int(matricule),
        "department": dept,
        "prenom": prenom,
        "nom": nom,
        semester: {
            "year": year,
            "isPublic": False
        }
    }

    # البحث عن أعمدة Moy General, Credit total, Decision في header
    header_row = 5
    moy_general_col = None
    credit_total_col = None
    decision_col = None
    
    for col in range(len(df.columns)):
        header_val = df.iloc[header_row, col]
        if isinstance(header_val, str):
            header_upper = str(header_val).upper()
            if "MOY GENERAL" in header_upper or "MOYENNE GENERAL" in header_upper:
                moy_general_col = col
            elif "CREDIT TOTAL" in header_upper or "CREDIT TOT" in header_upper:
                credit_total_col = col
            elif "DECISION" in header_upper:
                decision_col = col

    for module in modules:

        module_code = module["code"]
        module_name = module["name"]

        start = module["start_col"]
        end = module["end_col"]

        matieres = {}
        last_matiere_col = None  # لتتبع آخر عمود مادة (Capit)

        col = start
        header_row = 5  # السطر 6 في CSV (index 5)
        
        # معالجة جميع المواد في module
        while col <= end:
            m_full = df.iloc[4, col]
            coef = df.iloc[3, col]

            if not isinstance(m_full, str) or ":" not in m_full:
                col += 1
                continue

            code, mat_name = m_full.split(":", 1)
            code = code.strip()
            mat_name = mat_name.strip()

            notes = {
                "NCC": clean_value(df.iloc[row, col]),
                "NSN": clean_value(df.iloc[row, col+1]),
                "NSR": clean_value(df.iloc[row, col+2]),
                "Moy": clean_value(df.iloc[row, col+3]),
                "Capit": df.iloc[row, col+4] if not pd.isna(df.iloc[row, col+4]) else None
            }

            matieres[code] = {
                "name": mat_name,
                "notes": notes,
                "coef": clean_value(coef) if coef is not None else 0
            }

            last_matiere_col = col + 4  # آخر عمود في هذه المادة (Capit)
            col += 5
        
        # البحث عن MOYENNE UE و UE Valide بعد آخر مادة
        moyenne_col = None
        UE_valide_col = None
        
        if last_matiere_col is not None:
            # البحث في نطاق module عن "MOYENNE UE" و "UE Valide"
            for search_col in range(start, min(end + 5, len(df.columns))):
                header_val = df.iloc[header_row, search_col]
                if isinstance(header_val, str):
                    header_upper = str(header_val).upper()
                    if "MOYENNE UE" in header_upper and moyenne_col is None:
                        moyenne_col = search_col
                    elif "UE VALIDE" in header_upper or "UE VALID" in header_upper:
                        UE_valide_col = search_col
                        if moyenne_col is None:
                            # إذا وجدنا UE Valide قبل MOYENNE UE، فالمتوسط في العمود السابق
                            moyenne_col = search_col - 1
                        break
            
            # إذا لم نجد، نستخدم العمودين التاليين مباشرة بعد آخر مادة
            if moyenne_col is None:
                moyenne_col = last_matiere_col + 1
            if UE_valide_col is None:
                UE_valide_col = moyenne_col + 1
        
        moyenne = clean_value(df.iloc[row, moyenne_col]) if moyenne_col is not None and moyenne_col < len(df.columns) else 0
        UE_valide = df.iloc[row, UE_valide_col] if UE_valide_col is not None and UE_valide_col < len(df.columns) and not pd.isna(df.iloc[row, UE_valide_col]) else None

        students[int(matricule)][semester][module_code] = {
            "name": module_name,
            "matieres": matieres,
            "moyenne": moyenne,
            "UE_valide": UE_valide
        }
    
    # إضافة Moy General, Credit total, Decision في الـ semester
    if moy_general_col is not None:
        moy_gen = df.iloc[row, moy_general_col] if moy_general_col < len(df.columns) else None
        students[int(matricule)][semester]["moyenne_generale"] = clean_value(moy_gen)
    if credit_total_col is not None:
        credit_total = df.iloc[row, credit_total_col] if credit_total_col < len(df.columns) else None
        # تحويل إلى int إذا كان رقم
        try:
            if credit_total is not None and not pd.isna(credit_total) and str(credit_total).strip():
                students[int(matricule)][semester]["credit_total"] = int(float(str(credit_total).replace(',', '.')))
            else:
                students[int(matricule)][semester]["credit_total"] = 0
        except:
            students[int(matricule)][semester]["credit_total"] = 0
    if decision_col is not None:
        decision = df.iloc[row, decision_col] if decision_col < len(df.columns) else None
        students[int(matricule)][semester]["decision"] = decision if not pd.isna(decision) else None

# ========== إضافة الترتيب حسب moyenne_generale ==========
print("جاري حساب الترتيب...")

# دالة لتحويل moyenne_generale إلى رقم للترتيب
def parse_moyenne(moy):
    """تحويل moyenne من نص إلى رقم للترتيب"""
    if moy is None:
        return 0.0
    try:
        # تحويل "11,01" إلى 11.01
        if isinstance(moy, str):
            moy = moy.replace(',', '.')
        return float(moy)
    except:
        return 0.0

# تجميع الطلاب حسب الفصل
semester_students = {}
for matricule, student_data in students.items():
    if semester in student_data:
        semester_students[matricule] = student_data

# الترتيب العام حسب moyenne_generale (تنازلي)
sorted_all = sorted(
    semester_students.items(),
    key=lambda x: parse_moyenne(x[1][semester].get("moyenne_generale", 0)),
    reverse=True
)

# إضافة الترتيب العام
for rank, (matricule, student_data) in enumerate(sorted_all, start=1):
    students[matricule][semester]["rang_general"] = rank

# الترتيب حسب department
departments = {}
for matricule, student_data in semester_students.items():
    dept = student_data.get("department")
    if dept not in departments:
        departments[dept] = []
    departments[dept].append((matricule, student_data))

# إضافة الترتيب حسب department
for dept, dept_students in departments.items():
    # ترتيب الطلاب في هذا القسم حسب moyenne_generale (تنازلي)
    sorted_dept = sorted(
        dept_students,
        key=lambda x: parse_moyenne(x[1][semester].get("moyenne_generale", 0)),
        reverse=True
    )
    
    # إضافة الترتيب في القسم
    for rank, (matricule, student_data) in enumerate(sorted_dept, start=1):
        students[matricule][semester]["rang_department"] = rank

with open("students.json", "w", encoding="utf-8") as f:
    json.dump(students, f, ensure_ascii=False, indent=4)

print("تم استخراج JSON كامل ✔️ مع الترتيب حسب moyenne_generale 🎯")
