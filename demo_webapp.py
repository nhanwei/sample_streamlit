import streamlit as st
import pandas as pd
from datetime import date, timedelta

# Function to recalculate membership status based on current date
def refresh_membership_status(df):
    today = date.today()
    if df.empty:
        return df
    
    def get_status(expiry_date):
        if pd.isna(expiry_date):
            return "Expired"
        if isinstance(expiry_date, pd.Timestamp):
            expiry_date = expiry_date.date()
        return "Expired" if expiry_date < today else "Active"

    df['membership_status'] = df['member_expiry_date'].apply(get_status)
    return df

# 1. Initialize sample membership data in session state
if 'gym_members' not in st.session_state:
    today = date.today()
    initial_data = pd.DataFrame({
        'member_id': ['M001', 'M002', 'M003'],
        'member_name': ['Alice Johnson', 'Bob Smith', 'Charlie Davis'],
        'number': ['555-0101', '555-0102', '555-0103'],
        'member_expiry_date': [today - timedelta(days=10), today + timedelta(days=15), today + timedelta(days=30)],
        'membership_status': ['', '', '']
    })
    
    st.session_state.gym_members = refresh_membership_status(initial_data)

st.title("🏋️ Gym Membership Manager")
st.write("Welcome! Track members, search, modify expiry dates, and manage membership entries.")

# --- Sidebar Management Controls ---
st.sidebar.header("Member Management")

# Section: Add New Member
with st.sidebar.expander("➕ Add New Member", expanded=False):
    with st.form("add_member_form", clear_on_submit=True):
        existing_ids = st.session_state.gym_members['member_id'].tolist() if not st.session_state.gym_members.empty else []
        default_id = f"M{len(existing_ids) + 1:03d}"
        
        new_id = st.text_input("Member ID", value=default_id)
        new_name = st.text_input("Full Name", placeholder="e.g. Jane Doe")
        new_phone = st.text_input("Phone Number", placeholder="e.g. 555-0199")
        new_expiry = st.date_input("Expiry Date", value=date.today() + timedelta(days=30))
        
        submit_add = st.form_submit_button("Add Member")
        
        if submit_add:
            if not new_name.strip():
                st.error("Please enter a valid member name.")
            elif new_id in existing_ids:
                st.error("Member ID already exists. Please use a unique ID.")
            else:
                new_row = pd.DataFrame([{
                    'member_id': new_id,
                    'member_name': new_name,
                    'number': new_phone,
                    'member_expiry_date': new_expiry,
                    'membership_status': ''
                }])
                st.session_state.gym_members = pd.concat(
                    [st.session_state.gym_members, new_row], ignore_index=True
                )
                st.session_state.gym_members = refresh_membership_status(st.session_state.gym_members)
                st.success(f"Added member: {new_name}")
                st.rerun()

# Section: Remove Existing Member
with st.sidebar.expander("🗑️ Remove Member", expanded=False):
    if not st.session_state.gym_members.empty:
        member_options = {
            f"{row['member_id']} - {row['member_name']}": row['member_id']
            for _, row in st.session_state.gym_members.iterrows()
        }
        selected_label = st.selectbox("Select Member to Remove", options=list(member_options.keys()))
        
        if st.button("Delete Selected Member", type="primary"):
            target_id = member_options[selected_label]
            st.session_state.gym_members = st.session_state.gym_members[
                st.session_state.gym_members['member_id'] != target_id
            ].reset_index(drop=True)
            st.success(f"Removed member {target_id}")
            st.rerun()
    else:
        st.info("No members available to remove.")

# --- Search & Table View ---
st.subheader("Member Directory")

# Name Search Input
search_query = st.text_input("🔍 Search Member Name", placeholder="Type a name to filter...")

# Filter dataset by search term (case-insensitive)
if search_query.strip():
    filtered_df = st.session_state.gym_members[
        st.session_state.gym_members['member_name'].str.contains(search_query, case=False, na=False)
    ]
else:
    filtered_df = st.session_state.gym_members.copy()

st.write("Double-click an **Expiry Date** cell to edit. Status updates automatically.")

# Interactive Table Editor
edited_df = st.data_editor(
    filtered_df,
    column_config={
        "member_id": st.column_config.TextColumn("ID", disabled=True),
        "member_name": "Name",
        "number": "Phone Number",
        "member_expiry_date": st.column_config.DateColumn(
            "Expiry Date",
            format="YYYY-MM-DD",
            step=1,
            required=True
        ),
        "membership_status": st.column_config.TextColumn(
            "Status",
            disabled=True
        )
    },
    hide_index=True,
    use_container_width=True,
    key="member_editor"
)

# Synchronize edited rows back to session state when filtered or full view changes
if not edited_df.equals(filtered_df):
    for _, row in edited_df.iterrows():
        m_id = row['member_id']
        st.session_state.gym_members.loc[
            st.session_state.gym_members['member_id'] == m_id,
            ['member_name', 'number', 'member_expiry_date']
        ] = [row['member_name'], row['number'], row['member_expiry_date']]
        
    st.session_state.gym_members = refresh_membership_status(st.session_state.gym_members)
    st.rerun()