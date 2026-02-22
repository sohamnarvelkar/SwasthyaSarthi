import streamlit as st
import requests

API_URL = "http://localhost:8000"

def show_inventory():
    """Displays inventory levels from the backend."""
    st.subheader("📦 Current Inventory Levels")
    
    try:
        response = requests.get(f"{API_URL}/medicines")
        if response.status_code == 200:
            medicines = response.json()
            
            # Filter options
            col1, col2 = st.columns([2, 1])
            with col1:
                filter_stock = st.selectbox("Filter by stock:", ["All", "Low Stock (<10)", "Out of Stock", "In Stock"])
            with col2:
                search = st.text_input("Search", "")
            
            # Apply filters
            filtered = medicines
            if filter_stock == "Low Stock (<10)":
                filtered = [m for m in medicines if 0 < m.get("stock", 0) < 10]
            elif filter_stock == "Out of Stock":
                filtered = [m for m in medicines if m.get("stock", 0) == 0]
            elif filter_stock == "In Stock":
                filtered = [m for m in medicines if m.get("stock", 0) > 0]
            
            if search:
                filtered = [m for m in filtered if search.lower() in m.get("name", "").lower()]
            
            # Display table
            if filtered:
                st.table([
                    {
                        "Name": m.get("name", "")[:50] + "..." if len(m.get("name", "")) > 50 else m.get("name", ""),
                        "Stock": m.get("stock", 0),
                        "Price": f"₹{m.get('price', 0):.2f}",
                        "Prescription": "✅ Yes" if m.get("prescription_required") else "❌ No"
                    }
                    for m in filtered[:50]  # Limit to 50 for performance
                ])
                
                st.caption(f"Showing {len(filtered)} of {len(medicines)} medicines")
            else:
                st.info("No medicines match the filter criteria.")
        else:
            st.error("Failed to fetch inventory data")
    except Exception as e:
        st.error(f"Cannot connect to backend: {e}")
        st.info("Make sure the backend server is running at localhost:8000")

def show_refill_alerts():
    """Displays proactive refill alerts from the backend."""
    st.subheader("🔔 Proactive Refill Alerts")
    
    try:
        # Check for refills
        response = requests.get(f"{API_URL}/check-refills", params={"days_ahead": 7})
        if response.status_code == 200:
            data = response.json()
            alerts = data.get("alerts", [])
            
            if alerts:
                st.success(f"Found {len(alerts)} patients who need refills soon!")
                
                # Display alerts
                for alert in alerts:
                    with st.expander(f"📋 {alert.get('patient_name', 'Patient')} - {alert.get('product_name', '')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Patient ID:** {alert.get('patient_id', '')}")
                            st.write(f"**Medicine:** {alert.get('product_name', '')}")
                            st.write(f"**Days until refill:** {alert.get('days_until_refill', 0)}")
                        with col2:
                            st.write(f"**Phone:** {alert.get('patient_phone', 'N/A')}")
                            st.write(f"**Email:** {alert.get('patient_email', 'N/A')}")
                            st.write(f"**Current Stock:** {alert.get('current_stock', 0)}")
                        
                        # Action buttons
                        col_action1, col_action2 = st.columns(2)
                        with col_action1:
                            if st.button(f"📞 Contact Patient", key=f"contact_{alert.get('patient_id')}"):
                                st.success(f"Contact initiated for {alert.get('patient_name')}")
                        with col_action2:
                            if st.button(f"🛒 Create Order", key=f"order_{alert.get('patient_id')}"):
                                st.success(f"Order flow initiated for {alert.get('patient_name')}")
            else:
                st.info("No refill alerts at this time. All patients have sufficient medicine supply.")
        else:
            st.error("Failed to fetch refill alerts")
    except Exception as e:
        st.error(f"Cannot connect to backend: {e}")
        st.info("Make sure the backend server is running at localhost:8000")

def show_patients():
    """Displays patient list."""
    st.subheader("👥 Patient Directory")
    
    try:
        response = requests.get(f"{API_URL}/patients")
        if response.status_code == 200:
            patients = response.json()
            
            if patients:
                # Search
                search = st.text_input("Search patients", "")
                
                filtered = patients
                if search:
                    filtered = [p for p in patients if search.lower() in p.get("name", "").lower() or search.lower() in p.get("patient_id", "").lower()]
                
                st.table([
                    {
                        "ID": p.get("patient_id", ""),
                        "Name": p.get("name", ""),
                        "Age": p.get("age", 0),
                        "Gender": p.get("gender", ""),
                        "Phone": p.get("phone", ""),
                        "Language": p.get("language", "en")
                    }
                    for p in filtered[:30]
                ])
                
                st.caption(f"Showing {len(filtered)} of {len(patients)} patients")
            else:
                st.info("No patients found in database.")
        else:
            st.error("Failed to fetch patients")
    except Exception as e:
        st.error(f"Cannot connect to backend: {e}")

def show_orders():
    """Displays recent orders."""
    st.subheader("📋 Recent Orders")
    
    try:
        response = requests.get(f"{API_URL}/orders")
        if response.status_code == 200:
            orders = response.json()
            
            if orders:
                st.table([
                    {
                        "Order ID": o.get("id", ""),
                        "Patient ID": o.get("patient_id", ""),
                        "Product": o.get("product_name", "")[:40] + "..." if len(o.get("product_name", "")) > 40 else o.get("product_name", ""),
                        "Quantity": o.get("quantity", 0),
                        "Status": o.get("status", ""),
                        "Date": o.get("order_date", "")[:10] if o.get("order_date") else "N/A"
                    }
                    for o in orders[:30]
                ])
                
                st.caption(f"Showing {len(orders)} recent orders")
            else:
                st.info("No orders found.")
        else:
            st.error("Failed to fetch orders")
    except Exception as e:
        st.error(f"Cannot connect to backend: {e}")

def show_admin_dashboard():
    """Main admin dashboard with tabs."""
    st.header("🏥 Admin Dashboard")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Inventory", "🔔 Refill Alerts", "👥 Patients", "📋 Orders"])
    
    with tab1:
        show_inventory()
    
    with tab2:
        show_refill_alerts()
    
    with tab3:
        show_patients()
    
    with tab4:
        show_orders()
