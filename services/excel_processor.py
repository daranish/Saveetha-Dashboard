# import pandas as pd

# def process_student_excel(file) -> pd.DataFrame:

#     df = pd.read_excel(file, header=[0, 1])

#     new_columns = []

#     for main_col, sub_col in df.columns:
#         main_col = str(main_col).strip().lower()
#         sub_col = str(sub_col).strip().lower()

#         if main_col == "grade":
#             if "q1" in sub_col:
#                 new_columns.append("grade_q1")
#             elif "q2" in sub_col:
#                 new_columns.append("grade_q2")
#             elif "q3" in sub_col:
#                 new_columns.append("grade_q3")
#             else:
#                 new_columns.append(sub_col.replace("/", "_"))

#         elif "unnamed" in sub_col.lower():
#             new_columns.append(main_col.replace(".", "_"))

#         else:
#             new_columns.append(f"{main_col}_{sub_col}".replace(".", "_"))

#     df.columns = new_columns

#     df.columns = df.columns.str.strip().str.lower()

#     return df


import pandas as pd

def process_student_excel(file) -> pd.DataFrame:
    df = pd.read_excel(file, header=[0, 1])

    new_columns = []

    for main_col, sub_col in df.columns:
        main_col = str(main_col).strip().lower()
        sub_col = str(sub_col).strip().lower()

        # ✅ Handle grade sub-columns
        if main_col == "grade":
            if "q1" in sub_col:
                new_columns.append("grade_q1")
            elif "q2" in sub_col:
                new_columns.append("grade_q2")
            elif "q3" in sub_col:
                new_columns.append("grade_q3")
            else:
                new_columns.append(sub_col.replace("/", "_"))

        # ✅ Handle normal columns (no sub column)
        elif "unnamed" in sub_col:
            clean_name = main_col.replace(".", "_").replace(" ", "_")

            # ⭐ Normalize total grade column
            if "grade" in clean_name and "300" in clean_name:
                new_columns.append("overall_grade")
            else:
                new_columns.append(clean_name)

        # ✅ Handle combined columns
        else:
            combined = f"{main_col}_{sub_col}".replace(".", "_").replace(" ", "_")

            # ⭐ Normalize total grade column
            if "grade" in combined and "300" in combined:
                new_columns.append("overall_grade")
            else:
                new_columns.append(combined)

    df.columns = new_columns
    df.columns = df.columns.str.strip().str.lower()

    return df
