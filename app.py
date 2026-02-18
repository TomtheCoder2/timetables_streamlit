import os
import tempfile

import camelot
import streamlit as st

# --- Configuration (VSA Data) ---
final_class_subjects = {
    'K': {'D': 0, 'E': 0, 'F': 0, 'M': 0, 'NMG': 0, 'RKE': 0, 'BG': 0, 'TTG': 0, 'MU': 0, 'BS': 0, 'MI': 0,
          'total': 24},
    '1': {'D': 6, 'E': 0, 'F': 0, 'M': 4, 'NMG': 4, 'RKE': 1, 'BG': 2, 'TTG': 2, 'MU': 2, 'BS': 3, 'MI': 0,
          'total': 24},
    '2': {'D': 5, 'E': 0, 'F': 0, 'M': 5, 'NMG': 4, 'RKE': 1, 'BG': 2, 'TTG': 2, 'MU': 2, 'BS': 3, 'MI': 0,
          'total': 24},
    '3': {'D': 5, 'E': 3, 'F': 0, 'M': 5, 'NMG': 4, 'RKE': 1, 'BG': 2, 'TTG': 2, 'MU': 2, 'BS': 3, 'MI': 0,
          'total': 27},
    '4': {'D': 5, 'E': 3, 'F': 0, 'M': 5, 'NMG': 4, 'RKE': 1, 'BG': 2, 'TTG': 2, 'MU': 2, 'BS': 3, 'MI': 0,
          'total': 27},
    '5': {'D': 5, 'E': 2, 'F': 3, 'M': 5, 'NMG': 4, 'RKE': 1, 'BG': 2, 'TTG': 2, 'MU': 2, 'BS': 3, 'MI': 1,
          'total': 30},
    '6': {'D': 5, 'E': 2, 'F': 3, 'M': 5, 'NMG': 4, 'RKE': 1, 'BG': 2, 'TTG': 2, 'MU': 2, 'BS': 3, 'MI': 1, 'total': 30}
}

st.set_page_config(page_title="Timetable Checker", layout="wide")

st.title("📚 School Timetable Checker, Cycle 2")
st.markdown("""
Upload one or multiple PDF timetables. 
The system will check them against VSA lesson schedule requirements.
""")

# --- File Uploader ---
# accept_multiple_files allows the user to select all files in a folder
uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)

if st.button("Analyze Timetables") and uploaded_files:

    # Create a temporary directory to store PDFs for Camelot to read
    with tempfile.TemporaryDirectory() as temp_dir:

        results_container = st.container()

        for uploaded_file in uploaded_files:
            # Save uploaded file to temp disk so Camelot can read it
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # --- logic from your script ---
            entry = uploaded_file.name

            # Identify Class Name
            try:
                parts = entry.replace(".pdf", "").split(" ")
                class_name = parts[-2]
                if class_name in ["blau", "rot"]:
                    class_name = " ".join(parts[-3:-1])
            except:
                class_name = "Unknown"

            with st.expander(f"📄 Analysis for: **{class_name}** ({entry})", expanded=True):

                col1, col2 = st.columns([1, 1])

                warning_messages = []
                log_output = []  # store string logs

                try:
                    tables = camelot.read_pdf(temp_path, pages='all', flavor='lattice')
                    # log_output.append(f"Found {len(tables)} tables")

                    lessons_classes = {}  # Store local results for this file

                    for table_i, table in enumerate(tables):
                        day_names = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
                        df = table.df

                        # Logic to find day indices
                        day_indices = []
                        first_row = df.iloc[0]
                        for idx, cell in enumerate(first_row):
                            if cell is not None and cell.strip() in day_names:
                                day_indices.append(idx)

                        amount_lessons_per_day = df.shape[1]
                        lessons = [[[] for _ in range(amount_lessons_per_day + 3)] for _ in range(len(day_indices))]

                        # Parse Grid
                        for hour, row in enumerate(df.itertuples()):
                            row_str = ""
                            last_real_day = -1
                            temp_text = []
                            for col_idx, cell in enumerate(row):
                                if cell is None: cell = ""
                                cell_str = str(cell)

                                real_day = last_real_day
                                subject = cell_str.split(" ")[0]

                                # Find real day
                                for i, day_index in enumerate(day_indices):
                                    if col_idx - 1 < day_index:
                                        real_day = i - 1
                                        break
                                else:
                                    real_day = len(day_indices) - 1

                                if len(lessons) > real_day >= 0 != hour and cell_str != "" and not cell_str[0].isdigit() and cell_str[0] != '(':
                                    lessons[real_day][hour - 1].append(subject.upper())
                                if col_idx != 0:
                                    if last_real_day != real_day:
                                        # Row visual logging
                                        if len(temp_text) > 1:
                                            row_str += str(", ".join(temp_text)).ljust(15)
                                        else:
                                            row_str += str(temp_text[0]).ljust(15)
                                        temp_text = [cell_str.split("\n")[0].split(" ")[0]]
                                    else:
                                        if cell_str != "":
                                            temp_text.append(cell_str.split("\n")[0].split(" ")[0])
                                last_real_day = real_day
                            row_str += str(", ".join(temp_text)).split("\n")[0].ljust(15)
                            log_output.append(row_str)
                            # print()

                        # Count Lessons
                        lesson_count = {}
                        for day, lesson in enumerate(lessons):
                            for hour, subject in enumerate(lesson):
                                if len(subject) == 1:
                                    lesson_count[str(subject[0])] = lesson_count.get(str(subject[0]), 0) + 1
                                if len(subject) == 2:
                                    lesson_count[str(subject[0])] = lesson_count.get(str(subject[0]), 0) + 0.5
                                    lesson_count[str(subject[1])] = lesson_count.get(str(subject[1]), 0) + 0.5

                        lesson_count_sorted = sorted(lesson_count.items(), key=lambda x: x[1], reverse=True)
                        lessons_classes[class_name] = lesson_count_sorted

                    # --- Validation Logic ---
                    if class_name[0] in final_class_subjects:
                        total = 0
                        ref_data = final_class_subjects[class_name[0]]

                        if class_name in lessons_classes:
                            current_counts = lessons_classes[class_name]
                            st.write(f"**Detected Counts:** {dict(current_counts)}")

                            for lesson in current_counts:
                                subj_name = lesson[0]
                                count = lesson[1]
                                total += float(count)

                                # Check Integer
                                if not isinstance(count, int) and not count.is_integer():
                                    warning_messages.append(f"⚠️ Non-integer count: {subj_name} = {count}")

                                # Check vs VSA
                                check_name = "MU" if subj_name == "MGA" else subj_name

                                if check_name in ref_data:
                                    expected = float(ref_data[check_name])
                                    if expected != count:
                                        warning_messages.append(
                                            f"❌ **{check_name}**: Found {count}, Expected {expected}")
                                else:
                                    warning_messages.append(f"❓ **{check_name}**: Subject not in VSA definition")

                            # Check Total
                            if total != ref_data['total']:
                                warning_messages.append(
                                    f"❌ **TOTAL HOURS**: Found {total}, Expected {ref_data['total']}")
                            # else:
                            #     warning_messages.append(f"✅ **TOTAL HOURS**: Correct ({total})")
                    else:
                        warning_messages.append(f"⚠️ Class '{class_name}' not defined in VSA data.")

                except Exception as e:
                    st.error(f"Error processing PDF: {e}")

                # --- Display Results ---
                with col1:
                    st.subheader("Results")
                    if not warning_messages:
                        st.success("Analysis Complete - No issues found. All subject counts match VSA data.")
                    else:
                        for msg in warning_messages:
                            if "✅" in msg:
                                st.write(msg)
                            else:
                                st.error(msg)

                with col2:
                    st.subheader("Found Timetable (Parsed Grid)")
                    # st.text_area("Log", "\n".join(log_output), height=200, key=f"log_{uploaded_file.name}")
                    st.code("\n".join(log_output), height=200)
