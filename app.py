import datetime as dt
import random

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html, callback_context, no_update


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
PRODUCT_GROUPS = [
    "Cold brew",
    "Cold drip",
    "Duo set",
    "Matcha",
    "Bakery",
    "Coffee Bean",
    "Drip Bag",
    "Others",
]


# ---- Mock data (based on schema fields) ----

def make_mock_data():
    base_date = dt.date.today() - dt.timedelta(days=180)
    platforms = ["Shopee", "Lazada", "Tiktok", "LineOA", "Facebook", "LineShopping"]
    platform_weights = {
        "Facebook": 2,
        "Lazada": 10,
        "LineOA": 3,
        "LineShopping": 5,
        "Shopee": 50,
        "Tiktok": 30,
    }
    product_groups = PRODUCT_GROUPS
    order_statuses = ["Pending", "Shipped"]
    shipping_methods = ["EMS", "Flash"]
    purchase_types = ["Normal", "Package", "B2B", "Cold.Cafe", "Internal-Use"]
    order_types = ["Normal", "Claim"]
    group_weights = {
        "Cold brew": 40,
        "Cold drip": 20,
        "Duo set": 15,
        "Matcha": 10,
        "Bakery": 3,
        "Coffee Bean": 5,
        "Drip Bag": 2,
        "Others": 5,
    }

    product_registry_by_id = {}
    product_registry_by_name = {}
    products_by_group = {group: [] for group in product_groups}
    product_counter = 1

    def add_product(name, group, price, size_ml=None, base_name=None, include_in_selection=True):
        nonlocal product_counter
        product_id = f"P{product_counter:03d}"
        product_counter += 1
        product = {
            "product_id": product_id,
            "product_name": name,
            "product_category": group,
            "group_name": group,
            "price": price,
            "size_ml": size_ml,
            "base_name": base_name or name,
        }
        product_registry_by_id[product_id] = product
        product_registry_by_name[name] = product
        if include_in_selection:
            products_by_group[group].append(product)
        return product

    def add_sized_products(base_name, group, sizes):
        for size_label, price in sizes:
            size_ml = 1000 if size_label == "1L" else int(size_label.replace("ml", ""))
            name = f"{base_name} {size_label}"
            add_product(name, group, price, size_ml=size_ml, base_name=base_name)

    add_sized_products("Original", "Cold brew", [("200ml", 75), ("1L", 265)])
    add_sized_products("Dark Edition", "Cold brew", [("200ml", 75), ("1L", 265)])
    add_sized_products("Fruity Delight", "Cold brew", [("200ml", 75), ("1L", 279)])
    add_sized_products("Milky", "Cold brew", [("200ml", 85), ("1L", 299)])
    add_product("Peachful", "Cold brew", 420)
    add_product("Saen Chai", "Cold brew", 420)
    add_product("Namwhan", "Cold brew", 380)
    add_product("Small Set", "Cold brew", 310)

    add_sized_products("On the rock", "Cold drip", [("500ml", 325), ("1L", 550)])
    add_sized_products("Monday Morning", "Cold drip", [("500ml", 335), ("1L", 590)])
    add_sized_products("Natural wonder", "Cold drip", [("500ml", 420)])
    add_sized_products("Vanilla Sundae", "Cold drip", [("500ml", 445)])
    add_sized_products("Itim Kati", "Cold drip", [("500ml", 445)])

    add_product("Duo set Original", "Duo set", 170)
    add_product("Duo set Dark", "Duo set", 170)
    add_product("Duo set Fruity", "Duo set", 170)
    add_product("Duo set Milky", "Duo set", 170)

    add_product("umiro", "Matcha", 650)
    add_product("haruno", "Matcha", 650)
    add_product("rinro", "Matcha", 1280)
    add_product("asumi", "Matcha", 720)

    add_product("Mini Crosaint", "Bakery", 100)

    add_product("Original", "Coffee Bean", 235)
    add_product("Dark", "Coffee Bean", 235)
    add_product("Fruity", "Coffee Bean", 235)
    add_product("Milky", "Coffee Bean", 255)

    add_product("Coffee Drip D", "Drip Bag", 25)
    add_product("Coffee Drip MD", "Drip Bag", 25)
    add_product("Coffee Drip ML", "Drip Bag", 25)
    add_product("Coffee Drip M", "Drip Bag", 35)

    add_product("Tumbler", "Others", 350)
    add_product("Lamoon cup", "Others", 95)

    lamoon = product_registry_by_name["Lamoon cup"]
    eligible_cold_brew = ["Original", "Dark Edition", "Fruity Delight", "Milky"]
    eligible_cold_drip = ["On the rock", "Monday Morning", "Natural wonder", "Vanilla Sundae"]

    for base_name in eligible_cold_brew:
        product = product_registry_by_name[f"{base_name} 1L"]
        duo_name = f"Duo set {base_name} 1L"
        add_product(
            duo_name,
            "Duo set",
            product["price"] + lamoon["price"],
            size_ml=product["size_ml"],
            base_name=base_name,
            include_in_selection=False,
        )

    for base_name in eligible_cold_drip:
        product = product_registry_by_name[f"{base_name} 500ml"]
        duo_name = f"Duo set {base_name}"
        add_product(
            duo_name,
            "Duo set",
            product["price"] + lamoon["price"],
            size_ml=product["size_ml"],
            base_name=base_name,
            include_in_selection=False,
        )

    orders = []
    product_orders = []

    group_names = list(group_weights.keys())
    group_weight_values = [group_weights[name] for name in group_names]
    eligible_channels = {"Shopee", "Tiktok", "LineShopping", "Lazada"}
    platform_weight_values = [platform_weights[name] for name in platforms]

    def add_order_item(order_items, product, quantity):
        entry = order_items.get(product["product_id"])
        item_sales = product["price"] * quantity
        if entry:
            entry["quantity"] += quantity
            entry["item_sales"] += item_sales
        else:
            order_items[product["product_id"]] = {
                "product_id": product["product_id"],
                "product_name": product["product_name"],
                "product_category": product["product_category"],
                "base_name": product["base_name"],
                "size_ml": product["size_ml"],
                "quantity": quantity,
                "item_sales": item_sales,
            }

    def apply_duo_conversion(order_items, channel):
        if channel not in eligible_channels:
            return order_items

        lamoon_entry = order_items.get(lamoon["product_id"])
        if not lamoon_entry:
            return order_items

        lamoon_qty = lamoon_entry["quantity"]
        eligible_ids = []

        for entry in order_items.values():
            product = product_registry_by_id[entry["product_id"]]
            if (
                product["group_name"] == "Cold brew"
                and product["size_ml"] == 1000
                and product["base_name"] in eligible_cold_brew
            ):
                eligible_ids.extend([product["product_id"]] * entry["quantity"])
            elif (
                product["group_name"] == "Cold drip"
                and product["size_ml"] == 500
                and product["base_name"] in eligible_cold_drip
            ):
                eligible_ids.extend([product["product_id"]] * entry["quantity"])

        if not eligible_ids:
            return order_items

        random.shuffle(eligible_ids)
        pairs = min(lamoon_qty, len(eligible_ids))

        for index in range(pairs):
            product_id = eligible_ids[index]
            product = product_registry_by_id[product_id]
            order_items[product_id]["quantity"] -= 1
            order_items[product_id]["item_sales"] -= product["price"]
            if order_items[product_id]["quantity"] <= 0:
                del order_items[product_id]

            lamoon_qty -= 1

            if product["group_name"] == "Cold brew":
                duo_name = f"Duo set {product['base_name']} 1L"
            else:
                duo_name = f"Duo set {product['base_name']}"
            duo_product = product_registry_by_name[duo_name]
            add_order_item(order_items, duo_product, 1)

        if lamoon_qty <= 0:
            del order_items[lamoon["product_id"]]
        else:
            lamoon_entry["quantity"] = lamoon_qty
            lamoon_entry["item_sales"] = lamoon_qty * lamoon["price"]

        return order_items

    def pick_order_items():
        order_items = {}
        total_qty = 0
        continuation_prob = 0.9
        while total_qty < 10:
            group = random.choices(group_names, weights=group_weight_values, k=1)[0]
            product = random.choice(products_by_group[group])
            add_order_item(order_items, product, 1)
            total_qty += 1

            if total_qty >= 10:
                break
            if random.random() >= continuation_prob:
                break
            continuation_prob = max(0.0, continuation_prob - 0.1)

        return order_items

    for index in range(50000):
        order_id = f"ORD{10001 + index}"
        order_date = base_date + dt.timedelta(days=random.randint(0, 180))
        time_stamp = dt.datetime.combine(order_date, dt.time(hour=random.randint(8, 21)))
        shipdate = order_date + dt.timedelta(days=random.randint(0, 3))
        platform = random.choices(platforms, weights=platform_weight_values, k=1)[0]
        customer_status = random.choices(["New", "Returning"], weights=[0.45, 0.55])[0]
        order_status = random.choice(order_statuses)

        order_items = pick_order_items()
        order_items = apply_duo_conversion(order_items, platform)
        total_sales = sum(item["item_sales"] for item in order_items.values())
        group_sales = {}
        for item in order_items.values():
            group_sales[item["product_category"]] = (
                group_sales.get(item["product_category"], 0) + item["item_sales"]
            )
        group_name = max(group_sales, key=group_sales.get) if group_sales else random.choice(product_groups)

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
                "sales": round(total_sales, 2),
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

        for item_index, item in enumerate(order_items.values()):
            product_id = item["product_id"]
            product_name = item["product_name"]
            product_category = item["product_category"]
            quantity = item["quantity"]
            product_orders.append(
                {
                    "id": f"POL{order_id}-{item_index + 1}",
                    "order_id": order_id,
                    "product_id": product_id,
                    "product_name": product_name,
                    "product_category": product_category,
                    "base_name": item["base_name"],
                    "size_ml": item["size_ml"],
                    "quantity": quantity,
                    "item_sales": round(item["item_sales"], 2),
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
available_groups = PRODUCT_GROUPS

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
                            className="year-range",
                            children=[
                                dcc.Dropdown(
                                    id="year-select",
                                    options=[{"label": str(y), "value": y} for y in available_years],
                                    value=default_year,
                                    clearable=False,
                                    className="dropdown",
                                ),
                                html.Details(
                                    className="month-dropdown",
                                    children=[
                                        html.Summary(f"Selected months: {len(MONTH_ORDER)}", id="month-summary"),
                                        html.Div(
                                            className="month-actions",
                                            children=[
                                                html.Button(
                                                    "Select all",
                                                    id="month-select-all",
                                                    className="week-btn",
                                                    n_clicks=0,
                                                )
                                            ],
                                        ),
                                        dcc.Checklist(
                                            id="month-checklist",
                                            options=[{"label": m, "value": m} for m in MONTH_ORDER],
                                            value=MONTH_ORDER,
                                            className="checklist month-checklist",
                                        ),
                                    ],
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
                            id="platform-select-all",
                            options=[{"label": "Select all", "value": "all"}],
                            value=["all"],
                            className="checklist",
                        ),
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
                            id="group-select-all",
                            options=[{"label": "Select all", "value": "all"}],
                            value=["all"],
                            className="checklist",
                        ),
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
                                html.Div("Total Sales (Last Month)", className="kpi-label"),
                                html.Div(id="kpi-sales", className="kpi-value"),
                            ],
                        ),
                        html.Div(
                            className="kpi-card",
                            children=[
                                html.Div("Total Order (Last Month)", className="kpi-label"),
                                html.Div(id="kpi-orders", className="kpi-value"),
                            ],
                        ),
                        html.Div(
                            className="kpi-card",
                            children=[
                                html.Div("Average Per Order", className="kpi-label"),
                                html.Div(id="kpi-aov", className="kpi-value"),
                            ],
                        ),
                        html.Div(
                            className="kpi-card",
                            children=[
                                html.Div("New Customers (Last Month)", className="kpi-label"),
                                html.Div(id="kpi-new", className="kpi-value"),
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
                        html.Div(
                            className="panel span-12",
                            children=[
                                html.Div("Top 5 Products", className="panel-title"),
                                dcc.Graph(id="top-products", className="graph"),
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
    Output("month-summary", "children"),
    [Input("month-checklist", "value")],
)
def update_month_summary(selected_months):
    count = len(selected_months) if selected_months else 0
    return f"Selected months: {count}"


@app.callback(
    Output("month-checklist", "value"),
    [Input("month-select-all", "n_clicks")],
    [State("month-checklist", "value")],
)
def select_all_months(n_clicks, current_value):
    if not n_clicks:
        return no_update
    return MONTH_ORDER


@app.callback(
    [
        Output("platform-filter", "value"),
        Output("platform-select-all", "value"),
    ],
    [
        Input("platform-select-all", "value"),
        Input("platform-filter", "value"),
    ],
)
def sync_platform_selection(select_all_value, selected_platforms):
    selected_platforms = selected_platforms or []
    triggered = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else ""
    if triggered == "platform-select-all":
        if select_all_value and "all" in select_all_value:
            return available_platforms, ["all"]
        return [], []
    all_selected = set(selected_platforms) == set(available_platforms)
    return selected_platforms, (["all"] if all_selected else [])


@app.callback(
    [
        Output("group-filter", "value"),
        Output("group-select-all", "value"),
    ],
    [
        Input("group-select-all", "value"),
        Input("group-filter", "value"),
    ],
)
def sync_group_selection(select_all_value, selected_groups):
    selected_groups = selected_groups or []
    triggered = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else ""
    if triggered == "group-select-all":
        if select_all_value and "all" in select_all_value:
            return available_groups, ["all"]
        return [], []
    all_selected = set(selected_groups) == set(available_groups)
    return selected_groups, (["all"] if all_selected else [])


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
        Output("top-products", "figure"),
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
        Input("month-checklist", "value"),
        Input("platform-filter", "value"),
        Input("group-filter", "value"),
        Input("theme-toggle", "value"),
    ],
)

def refresh_dashboard(period, start_date, end_date, selected_year, week_offset, selected_months, platforms, groups, theme_value):
    is_dark = theme_value == "dark"
    font_color = "#ffffff" if is_dark else "#000000"
    grid_color = font_color
    legend_bg = "rgba(16,14,12,0.7)" if is_dark else "rgba(255,255,255,0.6)"
    hover_bg = "#111111" if is_dark else "#ffffff"
    hover_font = "#ffffff" if is_dark else "#000000"
    hover_border = "#ffffff" if is_dark else "#000000"

    def build_blank_figure():
        fig = go.Figure()
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_family="Noto Sans",
            font_color=font_color,
            hovermode="x unified",
            legend_title_text="",
            legend_bgcolor=legend_bg,
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return fig

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
        platforms = []
    if not groups:
        groups = []

    if not platforms or not groups:
        blank = build_blank_figure()
        return (
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            blank,
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
        )

    items_base = ORDER_ITEMS_DF[ORDER_ITEMS_DF["channel"].isin(platforms)]
    items_base = items_base[items_base["product_category"].isin(groups)]

    if items_base.empty:
        blank = build_blank_figure()
        return (
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            blank,
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
            build_blank_figure(),
        )

    reference_date = max_date
    first_of_current_month = dt.date(reference_date.year, reference_date.month, 1)
    last_month_end = first_of_current_month - dt.timedelta(days=1)
    last_month_start = dt.date(last_month_end.year, last_month_end.month, 1)
    last_month_items = apply_date_filter(items_base, last_month_start, last_month_end)

    items_for_charts = apply_date_filter(items_base, start, end)
    if period == "monthly":
        months = selected_months or MONTH_ORDER
        items_for_charts = items_for_charts[
            items_for_charts["time_stamp"].dt.month.map(MONTH_MAP).isin(months)
        ]

    items_for_charts = items_for_charts.copy()
    items_for_charts["product_rollup"] = items_for_charts["product_name"]
    size_mask = items_for_charts["size_ml"].notna()
    items_for_charts.loc[size_mask, "product_rollup"] = items_for_charts.loc[size_mask, "base_name"]
    coffee_mask = (
        (items_for_charts["product_category"] == "Coffee Bean")
        & (items_for_charts["product_rollup"].isin(["Original", "Dark", "Fruity", "Milky"]))
    )
    items_for_charts.loc[coffee_mask, "product_rollup"] = (
        "Coffee Bean " + items_for_charts.loc[coffee_mask, "product_rollup"].astype(str)
    )

    total_sales = last_month_items["item_sales"].sum()
    total_orders = last_month_items["order_id"].nunique()

    monthly_orders = items_for_charts.copy()
    monthly_orders["year"] = monthly_orders["time_stamp"].dt.year
    monthly_orders["month"] = monthly_orders["time_stamp"].dt.month
    monthly_aov = (
        monthly_orders.groupby(["year", "month"], as_index=False)
        .agg(total_sales=("item_sales", "sum"), total_orders=("order_id", "nunique"))
    )
    if not monthly_aov.empty:
        monthly_aov["aov"] = monthly_aov["total_sales"] / monthly_aov["total_orders"].replace(0, pd.NA)
        aov = monthly_aov["aov"].mean()
        if pd.isna(aov):
            aov = 0
    else:
        aov = 0
    new_customers = last_month_items[last_month_items["customer_status"] == "New"][
        "order_id"
    ].nunique()
    new_share = (new_customers / total_orders) * 100 if total_orders else 0

    kpi_sales = f"THB {total_sales:,.0f}"
    kpi_orders = f"{total_orders:,}"
    kpi_aov = f"THB {aov:,.0f}"
    kpi_new = f"{new_customers:,} ({new_share:.0f}%)"
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
    if period == "monthly":
        chosen_months = selected_months or MONTH_ORDER
        month_order_used = [m for m in MONTH_ORDER if m in chosen_months]
    else:
        month_order_used = MONTH_ORDER

    orders_for_charts = items_for_charts.drop_duplicates("order_id")[
        ["order_id", "time_stamp", "customer_status", "channel"]
    ].copy()

    if period == "monthly":
        items_for_charts["period_label"] = items_for_charts["time_stamp"].dt.month.map(MONTH_MAP)
        orders_for_charts["period_label"] = orders_for_charts["time_stamp"].dt.month.map(MONTH_MAP)
        period_label_title = "Month"
        x_order = month_order_used
    elif period == "daily":
        items_for_charts["period_label"] = items_for_charts["time_stamp"].dt.dayofweek.map(day_map)
        orders_for_charts["period_label"] = orders_for_charts["time_stamp"].dt.dayofweek.map(day_map)
        period_label_title = "Day"
        x_order = week_order
    else:
        period_label_title = "Date"
        items_for_charts["period_date"] = items_for_charts["time_stamp"].dt.date
        items_for_charts["period_label"] = items_for_charts["time_stamp"].dt.strftime("%d %b %Y")
        orders_for_charts["period_date"] = orders_for_charts["time_stamp"].dt.date
        orders_for_charts["period_label"] = orders_for_charts["time_stamp"].dt.strftime("%d %b %Y")
        x_order = (
            items_for_charts.drop_duplicates("period_date")
            .sort_values("period_date")["period_label"]
            .tolist()
        )

    sales_trend = items_for_charts.groupby("period_label", as_index=False)["item_sales"].sum()
    if x_order:
        sales_trend = sales_trend.set_index("period_label").reindex(x_order).reset_index()
    fig_sales = px.bar(
        sales_trend,
        x="period_label",
        y="item_sales",
        color_discrete_sequence=["#4979ff"],
        labels={"period_label": period_label_title, "item_sales": "Sales"},
    )
    fig_sales.update_layout(margin=dict(l=10, r=10, t=10, b=20))
    if x_order:
        fig_sales.update_xaxes(categoryorder="array", categoryarray=x_order)

    platform_sales = (
        items_for_charts.groupby("channel", as_index=False)["item_sales"]
        .sum()
        .sort_values("item_sales", ascending=False)
    )
    platform_color_map = {
        "Shopee": "#f6a343",
        "Tiktok": "#111111",
        "Lazada": "#6ea8ff",
        "LineShopping": "#7fd6b5",
        "LineOA": "#5aa986",
        "Facebook": "#d7e6ff",
    }
    fig_platform = px.pie(
        platform_sales,
        values="item_sales",
        names="channel",
        color="channel",
        color_discrete_map=platform_color_map,
        hole=0.35,
    )
    platform_text_colors = [
        "#ffffff" if channel == "Tiktok" else font_color
        for channel in platform_sales["channel"]
    ]
    fig_platform.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont=dict(color=font_color),
        insidetextfont=dict(color=platform_text_colors),
        marker=dict(line=dict(color="#ffffff", width=1.5)),
        insidetextorientation="horizontal",
    )
    fig_platform.update_layout(margin=dict(l=10, r=10, t=10, b=10), showlegend=True)

    group_sales = (
        items_for_charts.groupby("product_category", as_index=False)["item_sales"]
        .sum()
        .sort_values("item_sales")
    )
    fig_group = px.bar(
        group_sales,
        x="item_sales",
        y="product_category",
        orientation="h",
        color_discrete_sequence=["#2bb3a5"],
        labels={"item_sales": "Sales", "product_category": "Group"},
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

    top_products = (
        items_for_charts.groupby("product_rollup", as_index=False)["item_sales"]
        .sum()
        .sort_values("item_sales", ascending=False)
        .head(5)
    )
    fig_top_products = px.bar(
        top_products,
        x="item_sales",
        y="product_rollup",
        orientation="h",
        color_discrete_sequence=["#1d2b45"],
        labels={"item_sales": "Sales", "product_rollup": "Product"},
    )
    fig_top_products.update_layout(margin=dict(l=20, r=10, t=10, b=20))
    fig_top_products.update_yaxes(categoryorder="total ascending")

    product_sales = (
        items_for_charts.groupby("product_rollup", as_index=False)["item_sales"].sum()
        .sort_values("item_sales", ascending=False)
        .head(8)
    )
    fig_product_sales = px.bar(
        product_sales,
        x="item_sales",
        y="product_rollup",
        orientation="h",
        color_discrete_sequence=["#7c5cff"],
        labels={"item_sales": "Sales", "product_rollup": "Product"},
    )
    fig_product_sales.update_layout(margin=dict(l=20, r=10, t=10, b=20))
    fig_product_sales.update_yaxes(categoryorder="total ascending")

    product_qty = (
        items_for_charts.groupby("product_rollup", as_index=False)["quantity"].sum()
        .sort_values("quantity", ascending=False)
        .head(8)
    )
    fig_product_qty = px.bar(
        product_qty,
        x="quantity",
        y="product_rollup",
        orientation="h",
        color_discrete_sequence=["#4cc38a"],
        labels={"quantity": "Units", "product_rollup": "Product"},
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
        fig_top_products,
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
        fig_top_products,
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
