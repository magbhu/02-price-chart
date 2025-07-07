import streamlit as st
import pandas as pd
import os
from datetime import datetime

REMARKS_FILE = "REMARKS.csv"

st.set_page_config(page_title="🛠️ Maintain Remarks", layout="wide")
st.title("🛠️ Event Remarks Maintenance Panel")

# --- Load existing remarks ---
if os.path.exists(REMARKS_FILE):
    df = pd.read_csv(REMARKS_FILE)
    df.columns = [c.strip().capitalize() for c in df.columns]
    df = df.dropna(subset=["Date", "Comment"])
else:
    df = pd.DataFrame(columns=["Date", "Comment"])

# --- New remark entry ---
st.markdown("### ➕ Add New Event Remark")
with st.form("add_form", clear_on_submit=True):
    col1, col2 = st.columns([1, 4])
    new_date = col1.date_input("Event Date", value=datetime.today())
    new_comment = col2.text_input("Event Description")
    submitted = st.form_submit_button("✅ Add Remark")
    if submitted and new_comment.strip():
        df.loc[len(df)] = [new_date.strftime("%Y-%m-%d"), new_comment.strip()]
        df = df.drop_duplicates(subset=["Date", "Comment"])
        df.to_csv(REMARKS_FILE, index=False)
        st.success("✅ Remark added successfully!")

# --- Display & Edit Table ---
st.markdown("### 📝 Existing Remarks")
edited_df = st.data_editor(
    df.sort_values("Date"),
    num_rows="dynamic",
    use_container_width=True,
    key="editor"
)

# --- Save Changes Button ---
if st.button("💾 Save All Changes"):
    edited_df.to_csv(REMARKS_FILE, index=False)
    st.success("✅ Changes saved to REMARKS.csv")

# --- Delete row by date & text (optional helper) ---
st.markdown("### 🗑️ Delete Specific Remark")
with st.form("delete_form"):
    col1, col2 = st.columns([1, 4])
    del_date = col1.text_input("Event Date (YYYY-MM-DD)")
    del_comment = col2.text_input("Exact Comment Text")
    delete_btn = st.form_submit_button("🗑️ Delete")
    if delete_btn:
        original_len = len(df)
        df = df[~((df["Date"] == del_date.strip()) & (df["Comment"] == del_comment.strip()))]
        df.to_csv(REMARKS_FILE, index=False)
        if len(df) < original_len:
            st.success("✅ Remark deleted.")
        else:
            st.warning("⚠️ No matching remark found.")
