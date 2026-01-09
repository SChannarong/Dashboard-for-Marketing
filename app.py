import datetime as dt
import random

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html, callback_context


random.seed(7)

APP_TITLE = "Marketing Dashboard"
MONTH_MAP = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}
MONTH_ORDER = list(MONTH_MAP.values())


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
    purchase_types = ["Normal", "Package", "B2B", "Cold.Cafe", "Internal-Use"]
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

    orders_df["time_stamp"] = pd.to_datetime(orders_df["time_stamp"])
    orders_df["shipdate"] = pd.to_datetime(orders_df["shipdate"]).dt.date
    merged_df["time_stamp"] = pd.to_datetime(merged_df["time_stamp"])

    return orders_df, merged_df


ORDERS_DF, ORDER_ITEMS_DF = make_mock_data()


# ---- Helpers ----

def apply_date_filter(df, start_date, end_date):
    mask = (df["time_stamp"].dt.date >= start_date) & (df["time_stamp"].dt.date <= end_date)
    return df.loc[mask].copy()


def group_period(df, period):
    if period == "monthly":
        df["period"] = df["time_stamp"].dt.to_period("M").dt.to_timestamp()
        df["period_label"] = df["time_stamp"].dt.strftime("%b")
        label = "Month"
    elif period == "daily":
        df["period"] = df["time_stamp"].dt.date
        df["period_label"] = df["time_stamp"].dt.strftime("%a")
        label = "Day"
    else:
        df["period"] = df["time_stamp"].dt.date
        df["period_label"] = df["time_stamp"].dt.strftime("%d %b %Y")
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
available_years = sorted({d.year for d in ORDERS_DF["time_stamp"].dt.date})
default_year = dt.date.today().year if dt.date.today().year in available_years else max(available_years)


app.layout = html.Div(
    id="app-root",
    className="page theme-light",
    children=[
        dcc.Store(id="week-offset", data=0),
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
                            className="checklist",
                            options=[
                                {"label": "Daily", "value": "daily"},
                                {"label": "Monthly", "value": "monthly"},
                                {"label": "Custom", "value": "custom"},
                            ],
                            value="daily",
                            inline=False,
                        ),
                    ],
                ),
                html.Div(
                    className="control-card",
                    children=[
                        html.Div("Date Range", id="date-range-title", className="control-title"),
                        html.Div(
                            id="date-range-wrapper",
                            children=[
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
                            id="year-range-wrapper",
                            style={"display": "none"},
                            children=[
                                dcc.Dropdown(
                                    id="year-select",
                                    options=[{"label": str(y), "value": y} for y in available_years],
                                    value=default_year,
                                    clearable=False,
                                    className="dropdown",
                                ),
                                dcc.Dropdown(
                                    id="month-select",
                                    options=[{"label": m, "value": m} for m in MONTH_ORDER],
                                    value=MONTH_ORDER,
                                    multi=True,
                                    className="dropdown",
                                ),
                            ],
                        ),
                        html.Div(
                            id="week-nav",
                            className="week-nav",
                            children=[
                                html.Button("Prev", id="week-prev", className="week-btn", n_clicks=0),
                                html.Button("Next", id="week-next", className="week-btn", n_clicks=0),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className="control-card",
                    children=[
                        html.Div("Platform", className="control-title"),
                        dcc.Checklist(
                            id="platform-filter",
                            options=[{"label": p, "value": p} for p in available_platforms],
                            value=available_platforms,
                            className="checklist",
                        ),
                    ],
                ),
                html.Div(
                    className="control-card",
                    children=[
                        html.Div("Product Group", className="control-title"),
                        dcc.Checklist(
                            id="group-filter",
                            options=[{"label": g, "value": g} for g in available_groups],
                            value=available_groups,
                            className="checklist",
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
    [
        Output("date-range-wrapper", "style"),
        Output("year-range-wrapper", "style"),
        Output("date-range-title", "children"),
        Output("date-range", "disabled"),
        Output("date-range", "start_date"),
        Output("date-range", "end_date"),
        Output("week-nav", "style"),
    ],
    [
        Input("period-toggle", "value"),
        Input("week-offset", "data"),
    ],
    [
        State("date-range", "start_date"),
        State("date-range", "end_date"),
    ],
)
def toggle_date_controls(period_value, week_offset, current_start, current_end):
    latest_start = max_date - dt.timedelta(days=max_date.weekday())
    latest_end = latest_start + dt.timedelta(days=6)
    offset = week_offset or 0
    offset_start = latest_start - dt.timedelta(days=7 * offset)
    offset_end = offset_start + dt.timedelta(days=6)
    if period_value == "monthly":
        return (
            {"display": "none"},
            {"display": "block"},
            "Year & Month",
            True,
            current_start,
            current_end,
            {"display": "none"},
        )
    if period_value == "daily":
        return (
            {"display": "block"},
            {"display": "none"},
            "Latest Week",
            True,
            offset_start.isoformat(),
            offset_end.isoformat(),
            {"display": "flex"},
        )
    start = current_start or min_date.isoformat()
    end = current_end or max_date.isoformat()
    return {"display": "block"}, {"display": "none"}, "Date Range", False, start, end, {"display": "none"}


@app.callback(
    Output("app-root", "className"),
    [Input("theme-toggle", "value")],
)
def switch_theme(theme_value):
    return f"page theme-{theme_value}"


@app.callback(
    Output("week-offset", "data"),
    [
        Input("week-prev", "n_clicks"),
        Input("week-next", "n_clicks"),
        Input("period-toggle", "value"),
    ],
    [State("week-offset", "data")],
)
def update_week_offset(prev_clicks, next_clicks, period_value, current_offset):
    if period_value != "daily":
        return 0
    offset = current_offset or 0
    triggered = callback_context.triggered[0]["prop_id"].split(".")[0]
    if triggered == "week-prev":
        return offset + 1
    if triggered == "week-next":
        return max(0, offset - 1)
    return 0


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
        Input("year-select", "value"),
        Input("week-offset", "data"),
        Input("month-select", "value"),
        Input("platform-filter", "value"),
        Input("group-filter", "value"),
        Input("theme-toggle", "value"),
    ],
)

def refresh_dashboard(period, start_date, end_date, selected_year, week_offset, selected_months, platforms, groups, theme_value):
    if period == "monthly":
        year = selected_year or default_year
        start = dt.date(year, 1, 1)
        end = dt.date(year, 12, 31)
    elif period == "daily":
        latest = max_date
        offset = week_offset or 0
        start = (latest - dt.timedelta(days=latest.weekday())) - dt.timedelta(days=7 * offset)
        end = start + dt.timedelta(days=6)
    else:
        start = pd.to_datetime(start_date).date() if start_date else min_date
        end = pd.to_datetime(end_date).date() if end_date else max_date

    if not platforms:
        platforms = available_platforms
    if not groups:
        groups = available_groups

    filtered_orders = apply_date_filter(ORDERS_DF, start, end)
    filtered_orders = filtered_orders[filtered_orders["channel"].isin(platforms)]
    filtered_orders = filtered_orders[filtered_orders["group_name"].isin(groups)]
    if period == "monthly":
        months = selected_months or MONTH_ORDER
        filtered_orders = filtered_orders[
            filtered_orders["time_stamp"].dt.month.map(MONTH_MAP).isin(months)
        ]

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
    grid_color = font_color
    legend_bg = "rgba(16,14,12,0.7)" if is_dark else "rgba(255,255,255,0.6)"
    hover_bg = "#111111" if is_dark else "#ffffff"
    hover_font = "#ffffff" if is_dark else "#000000"
    hover_border = "#ffffff" if is_dark else "#000000"

    day_map = {
        0: "Mon",
        1: "Tue",
        2: "Wed",
        3: "Thu",
        4: "Fri",
        5: "Sat",
        6: "Sun",
    }
    week_order = list(day_map.values())
    month_order_used = (selected_months or MONTH_ORDER) if period == "monthly" else MONTH_ORDER

    orders_for_charts = filtered_orders.copy()

    if period == "monthly":
        orders_for_charts["period_label"] = orders_for_charts["time_stamp"].dt.month.map(MONTH_MAP)
        period_label_title = "Month"
        x_order = month_order_used
    elif period == "daily":
        orders_for_charts["period_label"] = orders_for_charts["time_stamp"].dt.dayofweek.map(day_map)
        period_label_title = "Day"
        x_order = week_order
    else:
        orders_for_charts["period_date"] = orders_for_charts["time_stamp"].dt.date
        orders_for_charts["period_label"] = orders_for_charts["time_stamp"].dt.strftime("%d %b %Y")
        period_label_title = "Date"
        x_order = (
            orders_for_charts.drop_duplicates("period_date")
            .sort_values("period_date")["period_label"]
            .tolist()
        )

    sales_trend = orders_for_charts.groupby("period_label", as_index=False)["sales"].sum()
    if x_order:
        sales_trend = sales_trend.set_index("period_label").reindex(x_order).reset_index()
    fig_sales = px.bar(
        sales_trend,
        x="period_label",
        y="sales",
        color_discrete_sequence=["#4979ff"],
        labels={"period_label": period_label_title, "sales": "Sales"},
    )
    fig_sales.update_layout(margin=dict(l=10, r=10, t=10, b=20))
    if x_order:
        fig_sales.update_xaxes(categoryorder="array", categoryarray=x_order)

    platform_sales = (
        orders_for_charts.groupby("channel", as_index=False)["sales"]
        .sum()
        .sort_values("sales", ascending=False)
    )
    fig_platform = px.pie(
        platform_sales,
        values="sales",
        names="channel",
        color_discrete_sequence=["#f9a64a", "#6aa5ff", "#9fdfc4", "#ffd9a2"],
        hole=0.35,
    )
    fig_platform.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_color=font_color,
        insidetextorientation="horizontal",
    )
    fig_platform.update_layout(margin=dict(l=10, r=10, t=10, b=10), showlegend=True)

    group_sales = (
        orders_for_charts.groupby("group_name", as_index=False)["sales"].sum().sort_values("sales")
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
    fig_group.update_yaxes(categoryorder="total ascending")

    customer_mix = (
        orders_for_charts.groupby(["period_label", "customer_status"])
        .size()
        .reset_index(name="orders")
    )
    if x_order:
        customer_mix["period_label"] = pd.Categorical(
            customer_mix["period_label"], categories=x_order, ordered=True
        )
        customer_mix = customer_mix.sort_values("period_label")
    fig_customer = px.bar(
        customer_mix,
        x="period_label",
        y="orders",
        color="customer_status",
        barmode="group",
        color_discrete_map={"New": "#4f7cff", "Returning": "#b8c6ff"},
        labels={"period_label": period_label_title, "orders": "Orders"},
    )
    fig_customer.update_layout(margin=dict(l=10, r=10, t=10, b=20))
    if x_order:
        fig_customer.update_xaxes(categoryorder="array", categoryarray=x_order)

    monthly_customer = orders_for_charts.copy()
    monthly_customer["month_label"] = monthly_customer["time_stamp"].dt.month.map(MONTH_MAP)
    monthly_customer = (
        monthly_customer.groupby(["month_label", "customer_status"])
        .size()
        .reset_index(name="orders")
    )
    month_index = pd.MultiIndex.from_product(
        [month_order_used, ["New", "Returning"]], names=["month_label", "customer_status"]
    )
    monthly_customer = (
        monthly_customer.set_index(["month_label", "customer_status"])
        .reindex(month_index, fill_value=0)
        .reset_index()
    )
    fig_customer_monthly = px.line(
        monthly_customer,
        x="month_label",
        y="orders",
        color="customer_status",
        markers=True,
        color_discrete_map={"New": "#f28b6c", "Returning": "#a7b1ff"},
        labels={"month_label": "Month", "orders": "Orders"},
    )
    fig_customer_monthly.update_layout(margin=dict(l=10, r=10, t=10, b=20))
    fig_customer_monthly.update_xaxes(categoryorder="array", categoryarray=month_order_used)

    items_for_charts = filtered_items.copy()

    product_sales = (
        items_for_charts.groupby("product_name", as_index=False)["item_sales"].sum()
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
    fig_product_sales.update_yaxes(categoryorder="total ascending")

    product_qty = (
        items_for_charts.groupby("product_name", as_index=False)["quantity"].sum()
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
    fig_product_qty.update_yaxes(categoryorder="total ascending")

    monthly_product = items_for_charts.copy()
    monthly_product["month_label"] = monthly_product["time_stamp"].dt.month.map(MONTH_MAP)
    monthly_product = (
        monthly_product.groupby(["month_label", "product_category"], as_index=False)["item_sales"].sum()
    )
    fig_product_monthly = px.area(
        monthly_product,
        x="month_label",
        y="item_sales",
        color="product_category",
        color_discrete_sequence=["#9f7aea", "#f9a64a", "#61c1c7", "#cbd4ff"],
        labels={"month_label": "Month", "item_sales": "Sales"},
    )
    fig_product_monthly.update_layout(margin=dict(l=10, r=10, t=10, b=20))
    fig_product_monthly.update_xaxes(categoryorder="array", categoryarray=month_order_used)

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
            hoverlabel=dict(
                bgcolor=hover_bg,
                font=dict(color=hover_font),
                bordercolor=hover_border,
            ),
        )
        fig.update_xaxes(
            showgrid=False,
            tickfont=dict(color=font_color),
            titlefont=dict(color=font_color),
            tickangle=60,
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor=grid_color,
            gridwidth=1,
            tickfont=dict(color=font_color),
            titlefont=dict(color=font_color),
        )
        fig.update_traces(textfont=dict(color=font_color))

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
