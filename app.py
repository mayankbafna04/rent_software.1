import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pandas as pd

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="EstateLedger Pro",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ROBUST CSS STYLING (Works in Dark & Light Mode) ---
st.markdown("""
<style>
    /* ISOLATED CARD STYLE 
       This forces the Tenant Cards to ALWAYS be white with dark text,
       preventing Dark Mode from making text invisible.
    */
    .tenant-card {
        background-color: #ffffff;
        color: #1f2937; /* Dark Grey Text */
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        border-left-width: 6px; /* The colored status bar */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
    }

    /* Force headers inside the card to be dark */
    .tenant-card h3 {
        color: #111827 !important;
        margin: 0 0 5px 0;
        padding: 0;
        font-size: 1.2rem;
        font-weight: 700;
    }
    
    /* Force sub-text inside the card to be medium grey */
    .tenant-card .sub-text {
        color: #6b7280 !important;
        font-size: 0.9rem;
        margin-top: 2px;
    }

    /* Force Note box to be light grey with dark text */
    .tenant-card .note-box {
        background-color: #f3f4f6;
        color: #374151 !important;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.85rem;
        margin-top: 12px;
        border: 1px solid #e5e7eb;
    }

    /* Status Badge Styling */
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION ---
# ⚠️ REPLACE 'YOUR_PASSWORD' BELOW with your actual password
uri = "mongodb+srv://mayankbafna04:Complex.16041007@cluster0.yvg5d.mongodb.net/?retryWrites=true&w=majority"

@st.cache_resource
def init_connection():
    return MongoClient(uri)

client = init_connection()
db = client['rent_softs']
collection = db['rent']

# --- 4. LOGIC: SMART COLOR ALGORITHM ---
def get_status_details(billed, paid):
    diff = billed - paid
    # Returns: (Border Color, Badge Background, Badge Text, Status Label)
    if diff <= 0:
        return "#10b981", "#d1fae5", "#064e3b", "✅ PAID"       # Green
    elif diff <= 5000:
        return "#f59e0b", "#fef3c7", "#78350f", "⚠️ PENDING"    # Yellow/Amber
    elif diff <= 15000:
        return "#f97316", "#ffedd5", "#7c2d12", "🟠 OVERDUE"    # Orange
    else:
        return "#ef4444", "#fee2e2", "#7f1d1d", "🚨 CRITICAL"   # Red

# --- 5. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🏢 EstateLedger")
    st.caption("Professional Management Suite")
    st.markdown("---")
    
    page = st.radio(
        "Main Menu", 
        ["Dashboard Overview", "Financial Reports", "Operations Center"],
        captions=["Live Status & Due Amounts", "Charts & Analytics", "Add/Edit/Delete Records"]
    )
    
    st.markdown("---")
    st.info("System Online 🟢")

# ==========================
# PAGE 1: DASHBOARD OVERVIEW
# ==========================
if page == "Dashboard Overview":
    st.header("📢 Real-Time Status Monitor")
    
    # Filters
    c1, c2 = st.columns([1, 2])
    month_filter = c1.selectbox("Select Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
    city_filter = c2.text_input("Filter by City", placeholder="Type city name (e.g. Chennai)")
    
    # Query Data
    query = {"month": month_filter}
    if city_filter:
        query["city"] = {"$regex": city_filter, "$options": "i"}
    
    data = list(collection.find(query))
    
    if data:
        df = pd.DataFrame(data)
        
        # Financial Metrics
        total_billed = df['billed_amount'].sum()
        total_paid = df['paid_amount'].sum()
        outstanding = total_billed - total_paid
        
        # KPI Cards
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Expected", f"₹{total_billed:,.0f}")
        m2.metric("Total Collected", f"₹{total_paid:,.0f}")
        m3.metric("Outstanding Due", f"₹{outstanding:,.0f}", delta=-outstanding, delta_color="inverse")
        
        st.markdown("### 📋 Tenant Accounts")
        
        # Sort by Highest Debt First
        df['diff'] = df['billed_amount'] - df['paid_amount']
        df = df.sort_values('diff', ascending=False)
        
        # RENDER PROFESSIONAL CARDS
        for _, row in df.iterrows():
            border_col, badge_bg, badge_txt, label = get_status_details(row['billed_amount'], row['paid_amount'])
            
            # HTML Injection for the "Fixed Color" Card
            st.markdown(f"""
            <div class="tenant-card" style="border-left-color: {border_col};">
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div>
                        <span class="status-badge" style="background-color: {badge_bg}; color: {badge_txt};">
                            {label}
                        </span>
                        <h3>{row['tenant_name']}</h3>
                        <div class="sub-text">
                            {row['property_name']} • <b>{row['city']}</b> • Unit: {row['unit']}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:1.4rem; font-weight:800; color:{border_col};">
                            ₹{row['diff']:,.0f}
                        </div>
                        <div class="sub-text">
                            Paid: ₹{row['paid_amount']:,.0f}
                        </div>
                    </div>
                </div>
                <div class="note-box">
                    📝 <b>Internal Note:</b> {row.get('notes', 'No notes')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    else:
        st.info(f"No records found for {month_filter}. Please go to 'Operations Center' to add data.")

# ==========================
# PAGE 2: FINANCIAL REPORTS
# ==========================
elif page == "Financial Reports":
    st.header("📈 Analytics Engine")
    
    month_filter = st.selectbox("Analyze Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
    
    data = list(collection.find({"month": month_filter}))
    
    if data:
        df = pd.DataFrame(data)
        
        tab1, tab2 = st.tabs(["Visual Charts", "Master Data Table"])
        
        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Collection by City")
                # Group data to see which city pays how much
                city_group = df.groupby("city")[["billed_amount", "paid_amount"]].sum()
                st.bar_chart(city_group)
            
            with c2:
                st.subheader("Revenue by Category")
                cat_group = df.groupby("category")["billed_amount"].sum()
                st.bar_chart(cat_group)
            
        with tab2:
            st.dataframe(
                df[['city', 'property_name', 'tenant_name', 'category', 'billed_amount', 'paid_amount', 'notes']],
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning("No data available for analysis.")

# ==========================
# PAGE 3: OPERATIONS CENTER
# ==========================
elif page == "Operations Center":
    st.header("🛠 Operations Center")
    
    tab_new, tab_edit = st.tabs(["➕ Add New Invoice", "✏️ Edit/Delete Records"])
    
    # --- SUB-TAB: ADD NEW ---
    with tab_new:
        st.subheader("Create New Entry")
        with st.form("add_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                city = st.text_input("City")
                prop = st.text_input("Property Name")
                unit = st.text_input("Unit No")
                tenant = st.text_input("Tenant Name")
                
            with col2:
                month = st.selectbox("Billing Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
                cat = st.selectbox("Category", ["Rent", "Maintenance", "Electricity", "Commercial", "Other"])
                billed = st.number_input("Billed Amount (₹)", min_value=0.0, step=100.0)
                paid = st.number_input("Paid Amount (₹)", min_value=0.0, step=100.0)
            
            notes = st.text_area("Internal Notes")
            
            if st.form_submit_button("💾 Save Record", type="primary"):
                if city and prop and tenant:
                    collection.insert_one({
                        "city": city, "property_name": prop, "unit": unit,
                        "tenant_name": tenant, "month": month, "category": cat,
                        "billed_amount": billed, "paid_amount": paid, "notes": notes,
                        "timestamp": datetime.now()
                    })
                    st.success("Record saved successfully!")
                else:
                    st.error("Please fill in City, Property, and Tenant Name.")

    # --- SUB-TAB: EDIT/DELETE ---
    with tab_edit:
        st.subheader("Manage Existing Records")
        search_txt = st.text_input("🔍 Search Tenant or Property Name")
        
        if search_txt:
            # Flexible search logic
            results = list(collection.find({
                "$or": [
                    {"tenant_name": {"$regex": search_txt, "$options": "i"}},
                    {"property_name": {"$regex": search_txt, "$options": "i"}}
                ]
            }))
            
            if not results:
                st.warning("No matches found.")
            
            for item in results:
                # Expandable editor for each result
                with st.expander(f"EDIT: {item['tenant_name']} - {item['property_name']} ({item['month']})"):
                    with st.form(key=str(item['_id'])):
                        c1, c2 = st.columns(2)
                        
                        # Editable Fields
                        new_paid = c1.number_input("Update Paid Amount", value=float(item['paid_amount']))
                        new_notes = c2.text_input("Update Notes", value=item.get('notes', ''))
                        
                        btn1, btn2 = st.columns([1, 4])
                        
                        if btn1.form_submit_button("Update Record"):
                            collection.update_one(
                                {"_id": item['_id']},
                                {"$set": {"paid_amount": new_paid, "notes": new_notes}}
                            )
                            st.success("Updated!")
                            st.rerun()
                            
                        if btn2.form_submit_button("Delete Record", type="secondary"):
                            collection.delete_one({"_id": item['_id']})
                            st.error("Record Deleted.")
                            st.rerun()