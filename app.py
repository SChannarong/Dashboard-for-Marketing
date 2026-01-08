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
    start_date = dt.date.today() - dt.timedelta(days=210)
    date_range = [start_date + dt.timedelta(days=i) for i in range(211)]

    platforms = ["Shopee", "Lazada", "Tiktok", "Website"]
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

    orders = []
    product_orders = []
    order_id_counter = 10000

    for date in date_range:
        daily_orders = random.randint(12, 36)
        for _ in range(daily_orders):
            order_id_counter += 1
            order_id = f"ORD{order_id_counter}"
            platform = random.choice(platforms)
            group_name = random.choice(product_groups)
            customer_status = random.choices(["New", "Returning"], weights=[0.45, 0.55])[0]
            items_count = random.randint(1, 3)

            base_sales = random.uniform(180, 1200)
            sales = round(base_sales * items_count, 2)

            orders.append(
                {
                    "order_id": order_id,
                    "time_stamp": dt.datetime.combine(date, dt.time(hour=random.randint(8, 21))),
                    "channel": platform,
                    "group_name": group_name,
                    "sales": sales,
                    "customer_status": customer_status,
                }
            )

            for _ in range(items_count):
                product_id, product_name, product_category = random.choice(products)
                quantity = random.randint(1, 4)
                product_orders.append(
                    {
                        "order_id": order_id,
                        "product_id": product_id,
                        "product_name": product_name,
                        "product_category": product_category,
                        "quantity": quantity,
                        "item_sales": round(random.uniform(80, 420) * quantity, 2),
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
    className="page",
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
                                html.Div("La Moon", className="brand-title"),
                                html.Div("Marketing Dashboard", className="brand-subtitle"),
                            ]
                        ),
                    ],
                ),
                html.Div(
                    className="nav",
                    children=[
                        html.Span("Overview", className="nav-pill active"),
                        html.Span("Paid Ads", className="nav-pill"),
                        html.Span("Funnel", className="nav-pill"),
                        html.Span("Creative & Audience", className="nav-pill"),
                        html.Span("Orders & Customers", className="nav-pill"),
                    ],
                ),
                html.Div(
                    className="topbar-actions",
                    children=[
                        html.Div("Moise Sitman", className="user-pill"),
                        html.Div("Satri", className="user-pill"),
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
                        html.Div("ยอดขายตามช่วงเวลา", className="panel-title"),
                        dcc.Graph(id="sales-trend", className="graph"),
                    ],
                ),
                html.Div(
                    className="panel span-5",
                    children=[
                        html.Div("ยอดขายตาม Platform", className="panel-title"),
                        dcc.Graph(id="sales-platform", className="graph"),
                    ],
                ),
                html.Div(
                    className="panel span-5",
                    children=[
                        html.Div("ยอดขายตาม Product Group", className="panel-title"),
                        dcc.Graph(id="sales-group", className="graph"),
                    ],
                ),
                html.Div(
                    className="panel span-7",
                    children=[
                        html.Div("ลูกค้าใหม่ / ลูกค้าเก่า", className="panel-title"),
                        dcc.Graph(id="customer-mix", className="graph"),
                    ],
                ),
                html.Div(
                    className="panel span-6",
                    children=[
                        html.Div("เปรียบเทียบรายเดือน: ลูกค้าใหม่", className="panel-title"),
                        dcc.Graph(id="customer-monthly", className="graph"),
                    ],
                ),
                html.Div(
                    className="panel span-6",
                    children=[
                        html.Div("ยอดขายแยกรายสินค้า (มูลค่า)", className="panel-title"),
                        dcc.Graph(id="product-sales", className="graph"),
                    ],
                ),
                html.Div(
                    className="panel span-6",
                    children=[
                        html.Div("ยอดขายแยกรายสินค้า (จำนวนชิ้น)", className="panel-title"),
                        dcc.Graph(id="product-qty", className="graph"),
                    ],
                ),
                html.Div(
                    className="panel span-6",
                    children=[
                        html.Div("เปรียบเทียบรายเดือน: รายสินค้า", className="panel-title"),
                        dcc.Graph(id="product-monthly", className="graph"),
                    ],
                ),
            ],
        ),
    ],
)


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
        Output("customer-monthly", "figure"),
        Output("product-sales", "figure"),
        Output("product-qty", "figure"),
        Output("product-monthly", "figure"),
    ],
    [
        Input("period-toggle", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("platform-filter", "value"),
        Input("group-filter", "value"),
    ],
)

def refresh_dashboard(period, start_date, end_date, platforms, groups):
    start = pd.to_datetime(start_date).date()
    end = pd.to_datetime(end_date).date()

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

    kpi_sales = f"฿{total_sales:,.0f}"
    kpi_orders = f"{total_orders:,}"
    kpi_aov = f"฿{aov:,.0f}"
    kpi_new = f"{new_customers:,} ({new_share:.0f}%)"

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
        filtered_orders.groupby("channel", as_index=False)["sales"].sum().sort_values("sales")
    )
    fig_platform = px.bar(
        platform_sales,
        x="sales",
        y="channel",
        orientation="h",
        color_discrete_sequence=["#f9a64a"],
        labels={"sales": "Sales", "channel": "Platform"},
    )
    fig_platform.update_layout(margin=dict(l=20, r=10, t=10, b=20))

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
            font_family="Palatino Linotype",
            hovermode="x unified",
            legend_title_text="",
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor="#e7e1db")

    return (
        kpi_sales,
        kpi_orders,
        kpi_aov,
        kpi_new,
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
