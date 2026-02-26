import streamlit as st
import requests

API_URL = "http://localhost:8000"

def check_backend_connection():
    """Check if backend is running."""
    try:
        response = requests.get(f"{API_URL}/docs", timeout=2)
        return response.status_code == 200
    except:
        return False

def show_dashboard_overview():
    """Show admin dashboard overview with key metrics."""
    st.markdown("## 📊 Admin Dashboard Overview")
    
    # Connection status
    is_connected = check_backend_connection()
    if is_connected:
        st.success("🟢 Backend Connected")
    else:
        st.error("🔴 Backend Disconnected - Make sure server is running on port 8000")
        return
    
    # Get data for overview
    try:
        # Get medicines count
        meds_response = requests.get(f"{API_URL}/medicines")
        medicines = meds_response.json() if meds_response.status_code == 200 else []
        
        # Get patients count
        patients_response = requests.get(f"{API_URL}/patients")
        patients = patients_response.json() if patients_response.status_code == 200 else []
        
        # Get orders count
        orders_response = requests.get(f"{API_URL}/orders")
        orders = orders_response.json() if orders_response.status_code == 200 else []
        
        # Get refill alerts
        alerts_response = requests.get(f"{API_URL}/check-refills", params={"days_ahead": 7})
        alerts_data = alerts_response.json() if alerts_response.status_code == 200 else {"alerts": []}
        alerts = alerts_data.get("alerts", [])
        
        # Calculate metrics
        total_medicines = len(medicines)
        low_stock_count = len([m for m in medicines if 0 < m.get("stock", 0) < 10])
        out_of_stock_count = len([m for m in medicines if m.get("stock", 0) == 0])
        total_patients = len(patients)
        total_orders = len(orders)
        pending_refills = len(alerts)
        
        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Medicines", total_medicines)
        with col2:
            st.metric("Total Patients", total_patients)
        with col3:
            st.metric("Total Orders", total_orders)
        with col4:
            st.metric("Pending Refills", pending_refills)
        
        # Second row of metrics
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric("📦 In Stock", total_medicines - low_stock_count - out_of_stock_count)
        with col6:
            st.metric("⚠️ Low Stock", low_stock_count, delta_color="inverse")
        with col7:
            st.metric("❌ Out of Stock", out_of_stock_count, delta_color="inverse")
        with col8:
            if pending_refills > 0:
                st.metric("🔔 Refill Alerts", pending_refills, delta_color="inverse")
            else:
                st.metric("🔔 Refill Alerts", 0)
        
        # Quick overview sections
        st.markdown("---")
        
        # Low Stock Medicines
        if low_stock_count > 0 or out_of_stock_count > 0:
            st.markdown("### ⚠️ Stock Alerts")
            low_stock_meds = [m for m in medicines if m.get("stock", 0) < 10]
            if low_stock_meds:
                st.warning(f"**{len(low_stock_meds)} medicines need attention:**")
                for med in low_stock_meds[:5]:
                    st.write(f"• **{med.get('name')}** - Stock: {med.get('stock')} - Price: ₹{med.get('price', 0):.2f}")
                if len(low_stock_meds) > 5:
                    st.caption(f"...and {len(low_stock_meds) - 5} more")
        
        # Recent Orders
        if orders:
            st.markdown("### 📋 Recent Orders")
            recent_orders = orders[:5]
            for order in recent_orders:
                st.write(f"• Order #{order.get('id')} - {order.get('product_name')} x{order.get('quantity')} - Status: {order.get('status')}")
        
        # Upcoming Refills
        if alerts:
            st.markdown("### 🔔 Upcoming Refills")
            for alert in alerts[:5]:
                st.write(f"• {alert.get('patient_name')} needs {alert.get('product_name')} in {alert.get('days_until_refill')} days")
            if len(alerts) > 5:
                st.caption(f"...and {len(alerts) - 5} more refill alerts")
        
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

def show_inventory():
    """Displays inventory levels from the backend."""
    st.subheader("📦 Current Inventory Levels")
    
    try:
        response = requests.get(f"{API_URL}/medicines")
        if response.status_code == 200:
            medicines = response.json()
            
            col1, col2 = st.columns([2, 1])
            with col1:
                filter_stock = st.selectbox("Filter by stock:", ["All", "Low Stock (<10)", "Out of Stock", "In Stock"])
            with col2:
                search = st.text_input("Search", "")
            
            filtered = medicines
            if filter_stock == "Low Stock (<10)":
                filtered = [m for m in medicines if 0 < m.get("stock", 0) < 10]
            elif filter_stock == "Out of Stock":
                filtered = [m for m in medicines if m.get("stock", 0) == 0]
            elif filter_stock == "In Stock":
                filtered = [m for m in medicines if m.get("stock", 0) > 0]
            
            if search:
                filtered = [m for m in filtered if search.lower() in m.get("name", "").lower()]
            
            if filtered:
                st.table([
                    {
                        "Name": m.get("name", "")[:50] + "..." if len(m.get("name", "")) > 50 else m.get("name", ""),
                        "Stock": m.get("stock", 0),
                        "Price": f"₹{m.get('price', 0):.2f}",
                        "Prescription": "✅ Yes" if m.get("prescription_required") else "❌ No"
                    }
                    for m in filtered[:50]
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
        response = requests.get(f"{API_URL}/check-refills", params={"days_ahead": 7})
        if response.status_code == 200:
            data = response.json()
            alerts = data.get("alerts", [])
            
            if alerts:
                st.success(f"Found {len(alerts)} patients who need refills soon!")
                
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
                search = st.text_input("Search patients", "")
                
                filtered = patients
                if search:
                    filtered = [p for p in patients if search.lower() in p.get("name", "").lower() or search.lower() in p.get("patient_id", "").lower()]
                
                st.table([
                    {
                        "Patient ID": p.get("patient_id", ""),
                        "Age": p.get("age", 0),
                        "Gender": p.get("gender", ""),
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

def show_user_history():
    """Displays user chat history and session information."""
    st.subheader("👤 User Session & History")
    
    # Check if there's any user session data available
    if 'history' in st.session_state and st.session_state.history:
        st.write(f"**Total Messages:** {len(st.session_state.history)}")
        
        with st.expander("📝 View Chat History"):
            for i, (speaker, message) in enumerate(st.session_state.history):
                st.markdown(f"**{i+1}. {speaker}:** {message}")
    else:
        st.info("No chat history available for this session.")
    
    # Show agent trace if available
    if 'agent_trace' in st.session_state and st.session_state.agent_trace:
        st.write(f"**Agent Trace Entries:** {len(st.session_state.agent_trace)}")
        
        with st.expander("🔍 View Agent Orchestration Trace"):
            for i, trace in enumerate(st.session_state.agent_trace):
                st.json(trace)
                if i < len(st.session_state.agent_trace) - 1:
                    st.markdown("---")
    else:
        st.info("No agent trace data available.")

def show_observability():
    """Displays observability and system metrics."""
    st.subheader("🔍 Agent Orchestration Trace (Observability)")
    
    # Check for agent trace data
    if 'agent_trace' in st.session_state and st.session_state.agent_trace:
        st.success(f"Found {len(st.session_state.agent_trace)} agent trace entries")
        
        for i, trace in enumerate(st.session_state.agent_trace):
            with st.expander(f"Trace Entry #{i+1}: {trace.get('agent', 'Unknown')}"):
                st.json(trace)
    else:
        st.info("No agent orchestration trace data available.")
        st.caption("Agent traces are captured when users interact with the system.")
    
    # System info
    st.markdown("### 📊 System Information")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Active Sessions", "1")
    with col2:
        st.metric("API Status", "Connected" if check_backend_connection() else "Disconnected")

def show_admin_dashboard():
    """Main admin dashboard with tabs."""
    st.header("🏥 Admin Dashboard")
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Overview", 
        "📦 Inventory", 
        "🔔 Refill Alerts", 
        "👥 Patients", 
        "📋 Orders",
        "👤 User History",
        "🔍 Observability"
    ])
    
    with tab1:
        show_dashboard_overview()
    
    with tab2:
        show_inventory()
    
    with tab3:
        show_refill_alerts()
    
    with tab4:
        show_patients()
    
    with tab5:
        show_orders()
    
    with tab6:
        show_user_history()
    
    with tab7:
        show_observability()
