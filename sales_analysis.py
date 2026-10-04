import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 1. Page Configuration
st.set_page_config(
    page_title="Retail Sales Analysis Dashboard",
    page_icon="📈",
    layout="wide"
)

# Custom Dashboard Title Styling
st.markdown(
    """
    <style>
    .dashboard-title {
        font-size: 38px;
        font-weight: bold;
        color: #1F4E79;
        text-align: center;
        padding-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="dashboard-title">📈 Retail Sales Analysis Dashboard</div>', unsafe_allow_html=True)
st.write("Analyze your sales data dynamically using native Matplotlib rendering below.")

# 2. Resilient Data Loading & Column Casing Normalization Function
@st.cache_data
def load_data(file_path_or_buffer):
    try:
        df = pd.read_csv(file_path_or_buffer, encoding='utf-8')
    except UnicodeDecodeError:
        if hasattr(file_path_or_buffer, 'seek'):
            file_path_or_buffer.seek(0)
        df = pd.read_csv(file_path_or_buffer, encoding='ISO-8859-1')
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return pd.DataFrame()

    # Dynamic column mapping to clean up whitespace/casing structures
    mapping = {}
    for col in df.columns:
        cleaned = col.strip().lower()
        if cleaned == 'category': mapping[col] = 'Category'
        elif cleaned == 'sales': mapping[col] = 'Sales'
        elif cleaned == 'profit': mapping[col] = 'Profit'
        elif cleaned == 'region': mapping[col] = 'Region'
        elif cleaned == 'state': mapping[col] = 'State'
        elif cleaned == 'segment': mapping[col] = 'Segment'
        elif cleaned in ['order date', 'order_date']: mapping[col] = 'Order Date'
        elif cleaned in ['order id', 'order_id']: mapping[col] = 'Order ID'
        elif cleaned in ['customer id', 'customer_id']: mapping[col] = 'Customer ID'
        elif cleaned in ['customer name', 'customer_name']: mapping[col] = 'Customer Name'
        elif cleaned in ['product name', 'product_name']: mapping[col] = 'Product Name'
        elif cleaned == 'quantity': mapping[col] = 'Quantity'
        
    df.rename(columns=mapping, inplace=True)

    # Convert numeric metrics safely to clean float/int values
    for col in ["Sales", "Profit", "Quantity"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # Convert Order Date to standard datetime object
    if "Order Date" in df.columns:
        df["Order Date"] = pd.to_datetime(df["Order Date"], errors='coerce')

    df.drop_duplicates(inplace=True)
    return df

# 3. Sidebar Configuration
st.sidebar.title("📂 Dashboard Controls")
uploaded_file = st.sidebar.file_uploader("Upload Superstore Dataset", type=["csv"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    try:
        df = load_data("Sample_superstore.csv")
    except:
        df = pd.DataFrame()

# 4. Filters & Calculations Pipeline
if not df.empty:
    def get_options(col_name):
        return ["All"] + sorted(df[col_name].dropna().unique().tolist()) if col_name in df.columns else ["All"]

    selected_region = st.sidebar.selectbox("🌍 Select Region", get_options("Region"))
    selected_state = st.sidebar.selectbox("🏙 Select State", get_options("State"))
    selected_category = st.sidebar.selectbox("📦 Select Category", get_options("Category"))
    selected_segment = st.sidebar.selectbox("👥 Select Segment", get_options("Segment"))

    # Active Filter execution
    filtered_df = df.copy()
    if selected_region != "All" and "Region" in filtered_df.columns: 
        filtered_df = filtered_df[filtered_df["Region"] == selected_region]
    if selected_state != "All" and "State" in filtered_df.columns: 
        filtered_df = filtered_df[filtered_df["State"] == selected_state]
    if selected_category != "All" and "Category" in filtered_df.columns: 
        filtered_df = filtered_df[filtered_df["Category"] == selected_category]
    if selected_segment != "All" and "Segment" in filtered_df.columns: 
        filtered_df = filtered_df[filtered_df["Segment"] == selected_segment]

    # Date Range Filter Execution
    if "Order Date" in df.columns:
        min_date = df["Order Date"].min().date()
        max_date = df["Order Date"].max().date()
        date_range = st.sidebar.date_input("📅 Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            filtered_df = filtered_df[(filtered_df["Order Date"].dt.date >= date_range[0]) & (filtered_df["Order Date"].dt.date <= date_range[1])]

    st.sidebar.success(f"Records Loaded: {len(filtered_df)}")
    st.markdown("---")

    if not filtered_df.empty:
        # ==========================================
        # 5. Key Performance Indicators (KPIs)
        # ==========================================
        st.subheader("📊 Key Performance Indicators")
        m1, m2, m3, m4, m5 = st.columns(5)
        
        total_sales = filtered_df["Sales"].sum() if "Sales" in filtered_df.columns else 0
        total_profit = filtered_df["Profit"].sum() if "Profit" in filtered_df.columns else 0
        total_orders = filtered_df["Order ID"].nunique() if "Order ID" in filtered_df.columns else 0
        total_customers = filtered_df["Customer ID"].nunique() if "Customer ID" in filtered_df.columns else 0
        total_quantity = filtered_df["Quantity"].sum() if "Quantity" in filtered_df.columns else 0

        m1.metric("💰 Total Sales", f"${total_sales:,.2f}")
        m2.metric("📈 Total Profit", f"${total_profit:,.2f}")
        m3.metric("🛒 Orders", f"{total_orders:,}")
        m4.metric("👥 Customers", f"{total_customers:,}")
        m5.metric("📦 Quantity Sold", f"{int(total_quantity):,}")
        st.markdown("---")

        # Global layout parameters for clean visual contrast
        plt.rcParams.update({
            'text.color': '#1F4E79',
            'axes.labelcolor': '#1F4E79',
            'xtick.color': '#333333',
            'ytick.color': '#333333',
            'font.weight': 'bold'
        })

        # ==========================================
        # ROW 1: Sales & Profit by Category
        # ==========================================
        row1_col1, row1_col2 = st.columns(2)

        with row1_col1:
            st.subheader("📦 Sales by Category")
            category_sales = filtered_df.groupby("Category")["Sales"].sum()
            fig1 = plt.figure(figsize=(6, 3.5))
            category_sales.plot(kind="bar", color="#2E75B6", edgecolor="black")
            plt.title("Sales Volumes ($)", fontsize=12)
            plt.xlabel("Category")
            plt.ylabel("Sales ($)")
            plt.xticks(rotation=0)
            plt.grid(axis='y', linestyle='--', alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig1)

        with row1_col2:
            st.subheader("💹 Profit by Category")
            category_profit = filtered_df.groupby("Category")["Profit"].sum()
            fig2 = plt.figure(figsize=(6, 3.5))
            category_profit.plot(kind="bar", color="#32CD32", edgecolor="black")
            plt.title("Profit Volumes ($)", fontsize=12)
            plt.xlabel("Category")
            plt.ylabel("Profit ($)")
            plt.xticks(rotation=0)
            plt.grid(axis='y', linestyle='--', alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig2)

        # ==========================================
        # ROW 2: Regional Distribution & Monthly Trend
        # ==========================================
        row2_col1, row2_col2 = st.columns(2)

        with row2_col1:
            st.subheader("🌍 Sales Distribution by Region")
            if "Region" in filtered_df.columns:
                region_sales = filtered_df.groupby("Region")["Sales"].sum()
                fig3 = plt.figure(figsize=(6, 3.5))
                # Using standard matplotlib pie charting with clean percentage indicators
                region_sales.plot(kind="pie", autopct='%1.1f%%', colors=['#1F4E79', '#2E75B6', '#BDD7EE', '#5B9BD5'], startangle=90, wedgeprops={'edgecolor': 'white'})
                plt.ylabel("") # Clear default pandas ylabel grouping text
                plt.title("Regional Performance Breakdown", fontsize=12)
                plt.tight_layout()
                st.pyplot(fig3)
            else:
                st.info("Region tracking data not present.")

        with row2_col2:
            st.subheader("📅 Monthly Sales Trend")
            if "Order Date" in filtered_df.columns:
                trend_df = filtered_df.copy()
                trend_df["Month"] = trend_df["Order Date"].dt.to_period("M").astype(str)
                monthly_sales = trend_df.groupby("Month")["Sales"].sum()
                
                fig4 = plt.figure(figsize=(6, 3.5))
                # Plotting line chart format
                monthly_sales.plot(kind="line", marker="o", color="#1F4E79", linewidth=2)
                plt.title("Monthly Performance Over Time", fontsize=12)
                plt.xlabel("Timeline (Months)")
                plt.ylabel("Sales ($)")
                plt.xticks(rotation=45)
                plt.grid(True, linestyle='--', alpha=0.3)
                plt.tight_layout()
                st.pyplot(fig4)
            else:
                st.info("Order Date timelines not available.")

        # ==========================================
        # ROW 3: Top 10 Products & Sales vs Profit Scatter
        # ==========================================
        row3_col1, row3_col2 = st.columns(2)

        with row3_col1:
            st.subheader("🏆 Top 10 Products by Sales")
            if "Product Name" in filtered_df.columns:
                top_products = filtered_df.groupby("Product Name")["Sales"].sum().sort_values(ascending=True).tail(10)
                fig5 = plt.figure(figsize=(6, 4.5))
                # Top ranks render cleanly as horizontal bars ('barh') to leave ample room for product labels
                top_products.plot(kind="barh", color="#4472C4", edgecolor="black")
                plt.title("Top Revenue Generator Lines", fontsize=12)
                plt.xlabel("Sales ($)")
                plt.ylabel("")
                plt.grid(axis='x', linestyle='--', alpha=0.3)
                plt.tight_layout()
                st.pyplot(fig5)

        with row3_col2:
            st.subheader("📊 Sales vs Profit Matrix")
            fig6 = plt.figure(figsize=(6, 4.5))
            # Safe matplotlib scatter plotting mapping margins
            plt.scatter(filtered_df["Sales"], filtered_df["Profit"], alpha=0.6, color="#ED7D31", edgecolor="black", s=40)
            plt.title("Margin Distribution Breakdown", fontsize=12)
            plt.xlabel("Individual Ticket Sales ($)")
            plt.ylabel("Profit ($)")
            plt.axhline(0, color='red', linestyle='--', alpha=0.5) # Break-even baseline visibility helper
            plt.grid(True, linestyle='--', alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig6)

        # ==========================================
        # 6. Automated Business Insights Section
        # ==========================================
        st.markdown("---")
        st.markdown("## 💡 Automated Business Insights")
        
        bi_col1, bi_col2 = st.columns(2)
        with bi_col1:
            top_cat = filtered_df.groupby("Category")["Sales"].sum().idxmax() if "Category" in filtered_df.columns else "N/A"
            top_reg = filtered_df.groupby("Region")["Profit"].sum().idxmax() if "Region" in filtered_df.columns else "N/A"
            top_st = filtered_df.groupby("State")["Sales"].sum().idxmax() if "State" in filtered_df.columns else "N/A"
            
            st.info(f"🏆 **Highest Sales Category:** {top_cat}")
            st.info(f"🌍 **Most Profitable Region:** {top_reg}")
            st.info(f"🏙 **Highest Sales State:** {top_st}")
            
        with bi_col2:
            top_prod = filtered_df.groupby("Product Name")["Sales"].sum().idxmax() if "Product Name" in filtered_df.columns else "N/A"
            top_cust = filtered_df.groupby("Customer Name")["Sales"].sum().idxmax() if "Customer Name" in filtered_df.columns else "N/A"
            
            st.info(f"📦 **Best Selling Product:** {top_prod}")
            st.info(f"👤 **Top Customer:** {top_cust}")
            st.info(f"💰 **Selected Scope Revenue:** ${total_sales:,.2f}")
            
    else:
        st.warning("The filters selected produced an empty slice of data.")
else:
    st.info("Awaiting structural dataset loading...")