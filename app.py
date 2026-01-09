import datetime as dt
import random

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html


random.seed(7)

APP_TITLE = "Marketing Dashboard"


# ---- Mock data (based on schema fields) ----

def make_mock_data():
    base_date = dt.date.today() - dt.timedelta(days=120)
    platforms = ["Shopee", "Lazada", "Tiktok", "LineOA", "Facebook", "LineShopping"]
    product_groups = ["Skincare", "Haircare", "Supplements", "Accessories"]
    products = [
        ("P001", "Glow Serum", "Skincare"),
        ("P002", "Hydra Cream", "Skincare"),
        ("P003", "Silk Shampoo", "Haircare"),
        ("P004", "Repair Conditioner", "Haircare"),
        ("P005", "Vitamin C", "Supplements"),
        ("P006", "Collagen Plus", "Supplements"),
        ("P007", "Travel Pouch", "Accessories"),
        ("P008", "Silk Headband", "Accessories"),
    ]
    order_statuses = ["Pending", "Shipped"]
    shipping_methods = ["EMS", "Flash"]
    purchase_types = ["Normal", "Package"]
    order_types = ["Normal", "Claim"]

    orders = []
    product_orders = []

    for index in range(50):
        order_id = f"ORD{10001 + index}"
        order_date = base_date + dt.timedelta(days=random.randint(0, 120))
        time_stamp = dt.datetime.combine(order_date, dt.time(hour=random.randint(8, 21)))
        shipdate = order_date + dt.timedelta(days=random.randint(0, 3))
        platform = random.choice(platforms)
        group_name = random.choice(product_groups)
        customer_status = random.choices(["New", "Returning"], weights=[0.45, 0.55])[0]
        items_count = random.randint(1, 3)
        sales = round(random.uniform(300, 2200) * items_count, 2)
        order_status = random.choice(order_statuses)

        orders.append(
            {
                "order_id": order_id,
                "time_stamp": time_stamp,
                "shipdate": shipdate,
                "channel": platform,
                "customer_data": f"CID-{random.randint(1000, 9999)}",
                "name": random.choice(
                    [
                        "Aria Bennett",
                        "Mila Hart",
                        "Noah Brooks",
                        "Ethan Cole",
                        "Luna Morris",
                        "Ava Quinn",
                    ]
                ),
                "address": f"{random.randint(10, 99)} Riverside Ave",
                "zipcode": f"{random.randint(10000, 99999)}",
                "phone": f"09{random.randint(10000000, 99999999)}",
                "shipping": random.choice(shipping_methods),
                "tracking_number": f"TRK{random.randint(100000, 999999)}",
                "remark": random.choice(["", "Gift wrap", "Call before delivery"]),
                "sales": sales,
                "group_name": group_name,
                "order_status": order_status,
                "points_given": random.choice([True, False]),
                "file_export_time": int(time_stamp.timestamp()),
                "customer_status": customer_status,
                "account_username": f"user{random.randint(100, 999)}",
                "purchase_type": random.choice(purchase_types),
                "order_type": random.choice(order_types),
                "package_customer_id": random.randint(1, 120),
                "packing_status": order_status in {"Packed", "Shipped", "Delivered"},
                "packing_time_stamp": time_stamp + dt.timedelta(hours=random.randint(1, 6)),
            }
        )

        for item_index in range(items_count):
            product_id, product_name, product_category = random.choice(products)
            quantity = random.randint(1, 4)
            product_orders.append(
                {
                    "id": f"POL{order_id}-{item_index + 1}",
                    "order_id": order_id,
                    "product_id": product_id,
                    "product_name": product_name,
                    "product_category": product_category,
                    "quantity": quantity,
                    "item_sales": round(random.uniform(80, 420) * quantity, 2),
                    "packed": random.randint(0, quantity),
                    "packed_time_stamp": time_stamp + dt.timedelta(hours=random.randint(2, 8)),
                }
            )

    orders_df = pd.DataFrame(orders)
    products_df = pd.DataFrame(product_orders)
    merged_df = products_df.merge(orders_df, on="order_id", how="left")

    return orders_df, merged_df


ORDERS_DF, ORDER_ITEMS_DF = make_mock_data()


# ---- Helpers ----

def apply_date_filter(df, start_date, end_date):
    mask = (df["time_stamp"].dt.date >= start_date) & (df["time_stamp"].dt.date <= end_date)
    return df.loc[mask].copy()


def group_period(df, period):
    if period == "monthly":
        df["period"] = df["time_stamp"].dt.to_period("M").dt.to_timestamp()
        label = "Month"
    else:
        df["period"] = df["time_stamp"].dt.date
        label = "Date"
    return df, label


# ---- App ----

app = Dash(__name__, assets_folder="assets")
app.title = APP_TITLE
server = app.server

available_platforms = sorted(ORDERS_DF["channel"].unique())
available_groups = sorted(ORDERS_DF["group_name"].unique())

min_date = ORDERS_DF["time_stamp"].min().date()
max_date = ORDERS_DF["time_stamp"].max().date()


app.layout = html.Div(
    id="app-root",
    className="page theme-light",
    children=[
        html.Div(
            className="topbar",
            children=[
                html.Div(
                    className="brand",
                    children=[
                        html.Div(className="brand-mark"),
                        html.Div(
                            children=[
                                html.Div("La.moon", className="brand-title"),
                                html.Div("Marketing Dashboard", className="brand-subtitle"),
                            ]
                        ),
                    ],
                ),
                dcc.Tabs(
                    id="dashboard-tabs",
                    className="tabs tabs-topbar",
                    value="overview",
                    children=[
                        dcc.Tab(label="Overview", value="overview", className="tab", selected_className="tab-selected"),
                        dcc.Tab(label="Total sales", value="total-sales", className="tab", selected_className="tab-selected"),
                        dcc.Tab(label="Number of customers", value="customers", className="tab", selected_className="tab-selected"),
                        dcc.Tab(label="Sales by product", value="products", className="tab", selected_className="tab-selected"),
                    ],
                ),
                html.Div(
                    className="topbar-actions",
                    children=[
                        html.Div("Moise Sitman", className="user-pill"),
                        html.Div("Satri", className="user-pill"),
                        dcc.RadioItems(
                            id="theme-toggle",
                            className="theme-toggle",
                            options=[
                                {"label": "Light", "value": "light"},
                                {"label": "Dark", "value": "dark"},
                            ],
                            value="light",
                            inline=True,
                        ),
                        html.Div(className="avatar"),
                    ],
                ),
            ],
        ),
        html.Div(
            className="controls",
            children=[
                html.Div(
                    className="control-card",
                    children=[
                        html.Div("Period", className="control-title"),
                        dcc.RadioItems(
                            id="period-toggle",
                            className="pill-group",
                            options=[
                                {"label": "Daily", "value": "daily"},
                                {"label": "Monthly", "value": "monthly"},
                                {"label": "Custom", "value": "custom"},
                            ],
                            value="daily",
                            inline=True,
                        ),
                    ],
                ),
                html.Div(
                    className="control-card",
                    children=[
                        html.Div("Date Range", className="control-title"),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=min_date,
                            max_date_allowed=max_date,
                            start_date=max_date - dt.timedelta(days=14),
                            end_date=max_date,
                            display_format="DD MMM YYYY",
                            className="date-picker",
                        ),
                    ],
                ),
                html.Div(
                    className="control-card",
                    children=[
                        html.Div("Platform", className="control-title"),
                        dcc.Dropdown(
                            id="platform-filter",
                            options=[{"label": p, "value": p} for p in available_platforms],
                            value=available_platforms,
                            multi=True,
                            className="dropdown",
                        ),
                    ],
                ),
                html.Div(
                    className="control-card",
                    children=[
                        html.Div("Product Group", className="control-title"),
                        dcc.Dropdown(
                            id="group-filter",
                            options=[{"label": g, "value": g} for g in available_groups],
                            value=available_groups,
                            multi=True,
                            className="dropdown",
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            id="page-overview",
            children=[
                html.Div(
                    className="kpi-grid",
                    children=[
                        html.Div(
                            className="kpi-card",
                            children=[
                                html.Div("Total Sales", className="kpi-label"),
                                html.Div(id="kpi-sales", className="kpi-value"),
                                html.Div("vs prev period", className="kpi-foot"),
                            ],
                        ),
                        html.Div(
                            className="kpi-card",
                            children=[
                                html.Div("Orders", className="kpi-label"),
                                html.Div(id="kpi-orders", className="kpi-value"),
                                html.Div("avg items per order", className="kpi-foot"),
                            ],
                        ),
                        html.Div(
                            className="kpi-card",
                            children=[
                                html.Div("AOV", className="kpi-label"),
                                html.Div(id="kpi-aov", className="kpi-value"),
                                html.Div("basket size", className="kpi-foot"),
                            ],
                        ),
                        html.Div(
                            className="kpi-card",
                            children=[
                                html.Div("New Customers", className="kpi-label"),
                                html.Div(id="kpi-new", className="kpi-value"),
                                html.Div("share of period", className="kpi-foot"),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className="grid",
                    children=[
                        html.Div(
                            className="panel span-7",
                            children=[
                                html.Div("Sales Over Time", className="panel-title"),
                                dcc.Graph(id="sales-trend", className="graph"),
                            ],
                        ),
                        html.Div(
                            className="panel span-5",
                            children=[
                                html.Div("Sales by Platform", className="panel-title"),
                                dcc.Graph(id="sales-platform", className="graph"),
                            ],
                        ),
                        html.Div(
                            className="panel span-5",
                            children=[
                                html.Div("Sales by Product Group", className="panel-title"),
                                dcc.Graph(id="sales-group", className="graph"),
                            ],
                        ),
                        html.Div(
                            className="panel span-7",
                            children=[
                                html.Div("New vs Returning Customers", className="panel-title"),
                                dcc.Graph(id="customer-mix", className="graph"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            id="page-total-sales",
            style={"display": "none"},
            children=[
                html.Div(
                    className="grid",
                    children=[
                        html.Div(
                            className="panel span-7",
                            children=[
                                html.Div("Sales Over Time", className="panel-title"),
                                dcc.Graph(id="sales-trend-total", className="graph"),
                            ],
                        ),
                        html.Div(
                            className="panel span-5",
                            children=[
                                html.Div("Sales by Platform", className="panel-title"),
                                dcc.Graph(id="sales-platform-total", className="graph"),
                            ],
                        ),
                        html.Div(
                            className="panel span-6",
                            children=[
                                html.Div("Sales by Product Group", className="panel-title"),
                                dcc.Graph(id="sales-group-total", className="graph"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            id="page-customers",
            style={"display": "none"},
            children=[
                html.Div(
                    className="grid",
                    children=[
                        html.Div(
                            className="panel span-7",
                            children=[
                                html.Div("New vs Returning Customers", className="panel-title"),
                                dcc.Graph(id="customer-mix-customers", className="graph"),
                            ],
                        ),
                        html.Div(
                            className="panel span-5",
                            children=[
                                html.Div("Monthly Comparison: New Customers", className="panel-title"),
                                dcc.Graph(id="customer-monthly-customers", className="graph"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            id="page-products",
            style={"display": "none"},
            children=[
                html.Div(
                    className="grid",
                    children=[
                        html.Div(
                            className="panel span-6",
                            children=[
                                html.Div("Product Sales (Value)", className="panel-title"),
                                dcc.Graph(id="product-sales-products", className="graph"),
                            ],
                        ),
                        html.Div(
                            className="panel span-6",
                            children=[
                                html.Div("Product Sales (Units)", className="panel-title"),
                                dcc.Graph(id="product-qty-products", className="graph"),
                            ],
                        ),
                        html.Div(
                            className="panel span-6",
                            children=[
                                html.Div("Monthly Comparison: Products", className="panel-title"),
                                dcc.Graph(id="product-monthly-products", className="graph"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)

@app.callback(
    [
        Output("page-overview", "style"),
        Output("page-total-sales", "style"),
        Output("page-customers", "style"),
        Output("page-products", "style"),
    ],
    [Input("dashboard-tabs", "value")],
)
def switch_pages(active_tab):
    visible = {"display": "block"}
    hidden = {"display": "none"}
    return (
        visible if active_tab == "overview" else hidden,
        visible if active_tab == "total-sales" else hidden,
        visible if active_tab == "customers" else hidden,
        visible if active_tab == "products" else hidden,
    )


@app.callback(
    Output("app-root", "className"),
    [Input("theme-toggle", "value")],
)
def switch_theme(theme_value):
    return f"page theme-{theme_value}"


@app.callback(
    [
        Output("kpi-sales", "children"),
        Output("kpi-orders", "children"),
        Output("kpi-aov", "children"),
        Output("kpi-new", "children"),
        Output("sales-trend", "figure"),
        Output("sales-platform", "figure"),
        Output("sales-group", "figure"),
        Output("customer-mix", "figure"),
        Output("sales-trend-total", "figure"),
        Output("sales-platform-total", "figure"),
        Output("sales-group-total", "figure"),
        Output("customer-mix-customers", "figure"),
        Output("customer-monthly-customers", "figure"),
        Output("product-sales-products", "figure"),
        Output("product-qty-products", "figure"),
        Output("product-monthly-products", "figure"),
    ],
    [
        Input("period-toggle", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("platform-filter", "value"),
        Input("group-filter", "value"),
        Input("theme-toggle", "value"),
    ],
)

def refresh_dashboard(period, start_date, end_date, platforms, groups, theme_value):
    start = pd.to_datetime(start_date).date() if start_date else min_date
    end = pd.to_datetime(end_date).date() if end_date else max_date

    filtered_orders = apply_date_filter(ORDERS_DF, start, end)
    if platforms:
        filtered_orders = filtered_orders[filtered_orders["channel"].isin(platforms)]
    if groups:
        filtered_orders = filtered_orders[filtered_orders["group_name"].isin(groups)]

    filtered_items = ORDER_ITEMS_DF.merge(
        filtered_orders[["order_id"]], on="order_id", how="inner"
    )

    total_sales = filtered_orders["sales"].sum()
    total_orders = filtered_orders["order_id"].nunique()
    aov = total_sales / total_orders if total_orders else 0
    new_customers = (filtered_orders["customer_status"] == "New").sum()
    new_share = (new_customers / total_orders) * 100 if total_orders else 0

    kpi_sales = f"THB {total_sales:,.0f}"
    kpi_orders = f"{total_orders:,}"
    kpi_aov = f"THB {aov:,.0f}"
    kpi_new = f"{new_customers:,} ({new_share:.0f}%)"
    is_dark = theme_value == "dark"
    font_color = "#ffffff" if is_dark else "#000000"
    grid_color = "#2c2b2a" if is_dark else "#e7e1db"
    legend_bg = "rgba(16,14,12,0.7)" if is_dark else "rgba(255,255,255,0.6)"

    grouped_orders, label = group_period(filtered_orders.copy(), "monthly" if period == "monthly" else "daily")
    sales_trend = grouped_orders.groupby("period", as_index=False)["sales"].sum()

    fig_sales = px.bar(
        sales_trend,
        x="period",
        y="sales",
        color_discrete_sequence=["#4979ff"],
        labels={"period": label, "sales": "Sales"},
    )
    fig_sales.update_layout(margin=dict(l=10, r=10, t=10, b=20))

    platform_sales = (
        filtered_orders.groupby("channel", as_index=False)["sales"].sum().sort_values("sales", ascending=False)
    )
    fig_platform = px.pie(
        platform_sales,
        values="sales",
        names="channel",
        color_discrete_sequence=["#f9a64a", "#6aa5ff", "#9fdfc4", "#ffd9a2"],
        hole=0.35,
    )
    fig_platform.update_traces(textposition="inside", textinfo="percent+label")
    fig_platform.update_layout(margin=dict(l=10, r=10, t=10, b=10), showlegend=True)

    group_sales = (
        filtered_orders.groupby("group_name", as_index=False)["sales"].sum().sort_values("sales")
    )
    fig_group = px.bar(
        group_sales,
        x="sales",
        y="group_name",
        orientation="h",
        color_discrete_sequence=["#2bb3a5"],
        labels={"sales": "Sales", "group_name": "Group"},
    )
    fig_group.update_layout(margin=dict(l=20, r=10, t=10, b=20))

    customer_mix = grouped_orders.groupby(["period", "customer_status"]).size().reset_index(name="orders")
    fig_customer = px.bar(
        customer_mix,
        x="period",
        y="orders",
        color="customer_status",
        barmode="stack",
        color_discrete_map={"New": "#4f7cff", "Returning": "#b8c6ff"},
        labels={"period": label, "orders": "Orders"},
    )
    fig_customer.update_layout(margin=dict(l=10, r=10, t=10, b=20))

    monthly_customer = filtered_orders.copy()
    monthly_customer["month"] = monthly_customer["time_stamp"].dt.to_period("M").dt.to_timestamp()
    monthly_customer = (
        monthly_customer.groupby(["month", "customer_status"]).size().reset_index(name="orders")
    )
    fig_customer_monthly = px.line(
        monthly_customer,
        x="month",
        y="orders",
        color="customer_status",
        markers=True,
        color_discrete_map={"New": "#f28b6c", "Returning": "#a7b1ff"},
        labels={"month": "Month", "orders": "Orders"},
    )
    fig_customer_monthly.update_layout(margin=dict(l=10, r=10, t=10, b=20))

    product_sales = (
        filtered_items.groupby("product_name", as_index=False)["item_sales"].sum()
        .sort_values("item_sales", ascending=False)
        .head(8)
    )
    fig_product_sales = px.bar(
        product_sales,
        x="item_sales",
        y="product_name",
        orientation="h",
        color_discrete_sequence=["#7c5cff"],
        labels={"item_sales": "Sales", "product_name": "Product"},
    )
    fig_product_sales.update_layout(margin=dict(l=20, r=10, t=10, b=20))

    product_qty = (
        filtered_items.groupby("product_name", as_index=False)["quantity"].sum()
        .sort_values("quantity", ascending=False)
        .head(8)
    )
    fig_product_qty = px.bar(
        product_qty,
        x="quantity",
        y="product_name",
        orientation="h",
        color_discrete_sequence=["#4cc38a"],
        labels={"quantity": "Units", "product_name": "Product"},
    )
    fig_product_qty.update_layout(margin=dict(l=20, r=10, t=10, b=20))

    monthly_product = filtered_items.copy()
    monthly_product["month"] = monthly_product["time_stamp"].dt.to_period("M").dt.to_timestamp()
    monthly_product = (
        monthly_product.groupby(["month", "product_category"], as_index=False)["item_sales"].sum()
    )
    fig_product_monthly = px.area(
        monthly_product,
        x="month",
        y="item_sales",
        color="product_category",
        color_discrete_sequence=["#9f7aea", "#f9a64a", "#61c1c7", "#cbd4ff"],
        labels={"month": "Month", "item_sales": "Sales"},
    )
    fig_product_monthly.update_layout(margin=dict(l=10, r=10, t=10, b=20))

    for fig in [
        fig_sales,
        fig_platform,
        fig_group,
        fig_customer,
        fig_customer_monthly,
        fig_product_sales,
        fig_product_qty,
        fig_product_monthly,
    ]:
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_family="Noto Sans",
            font_color=font_color,
            hovermode="x unified",
            legend_title_text="",
            legend_bgcolor=legend_bg,
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor=grid_color)

    return (
        kpi_sales,
        kpi_orders,
        kpi_aov,
        kpi_new,
        fig_sales,
        fig_platform,
        fig_group,
        fig_customer,
        fig_sales,
        fig_platform,
        fig_group,
        fig_customer,
        fig_customer_monthly,
        fig_product_sales,
        fig_product_qty,
        fig_product_monthly,
    )


if __name__ == "__main__":
    app.run_server(debug=False)
