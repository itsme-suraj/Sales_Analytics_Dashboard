"""
Generates a realistic synthetic Indian retail sales dataset for the dashboard.
Run once: python data/generate_data.py
Produces data/sales_data.csv (committed to the repo so the app works instantly,
no need to regenerate on every deploy).

This is SYNTHETIC data (clearly documented as such in the README) built with
real-world structure: regional seasonality (Diwali, Republic Day, EOSS sales),
category-specific margins, and realistic Indian geography — not a copy of the
generic Kaggle Superstore dataset everyone else uses.
"""

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

# ---------------------------------------------------------------------
# REFERENCE DATA
# ---------------------------------------------------------------------
REGIONS = {
    "North": {"states": ["Delhi", "Punjab", "Haryana", "Uttar Pradesh"],
              "cities": ["New Delhi", "Ludhiana", "Gurugram", "Lucknow"]},
    "South": {"states": ["Karnataka", "Tamil Nadu", "Telangana", "Kerala"],
              "cities": ["Bengaluru", "Chennai", "Hyderabad", "Kochi"]},
    "East":  {"states": ["West Bengal", "Odisha", "Bihar", "Jharkhand"],
              "cities": ["Kolkata", "Bhubaneswar", "Patna", "Ranchi"]},
    "West":  {"states": ["Maharashtra", "Gujarat", "Rajasthan", "Goa"],
              "cities": ["Mumbai", "Ahmedabad", "Jaipur", "Panaji"]},
}

CATEGORIES = {
    "Electronics": {
        "products": ["Smartphone", "Laptop", "Bluetooth Earbuds", "Smartwatch",
                     "Television", "Tablet", "Power Bank", "Digital Camera"],
        "price_range": (1500, 60000), "margin_range": (0.06, 0.16),
    },
    "Clothing": {
        "products": ["Cotton T-Shirt", "Denim Jeans", "Kurta Set", "Silk Saree",
                     "Winter Jacket", "Ethnic Wear", "Sportswear Set", "Casual Shoes"],
        "price_range": (299, 4500), "margin_range": (0.30, 0.48),
    },
    "Grocery": {
        "products": ["Basmati Rice 5kg", "Wheat Atta 10kg", "Cooking Oil 1L",
                     "Spice Combo Pack", "Namkeen Snacks", "Soft Drinks Pack",
                     "Dairy Combo", "Pulses Combo Pack"],
        "price_range": (49, 1200), "margin_range": (0.04, 0.11),
    },
    "Furniture": {
        "products": ["3-Seater Sofa", "Dining Table Set", "Office Chair", "Queen Size Bed",
                     "3-Door Wardrobe", "Bookshelf", "Study Table", "Recliner"],
        "price_range": (2500, 45000), "margin_range": (0.18, 0.30),
    },
    "Beauty & Personal Care": {
        "products": ["Skincare Combo Set", "Herbal Shampoo", "Perfume 100ml",
                     "Makeup Kit", "Hair Dryer", "Trimmer", "Face Wash Combo", "Hair Oil Pack"],
        "price_range": (99, 3500), "margin_range": (0.35, 0.52),
    },
}

SEGMENTS = ["Consumer", "Corporate", "SME"]
PAYMENT_MODES = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Cash on Delivery"]

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Reyansh", "Ishaan",
               "Sai", "Krishna", "Ayaan", "Priya", "Ananya", "Diya", "Saanvi", "Anika",
               "Riya", "Aadhya", "Myra", "Kiara", "Isha", "Rohan", "Karan", "Amit",
               "Neha", "Pooja", "Rahul", "Sneha", "Vikram", "Deepika", "Manish"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Iyer", "Nair", "Reddy", "Patel", "Singh",
              "Kumar", "Rao", "Mehta", "Joshi", "Chatterjee", "Bose", "Pillai", "Desai"]

# ---------------------------------------------------------------------
# CUSTOMERS
# ---------------------------------------------------------------------
N_CUSTOMERS = 900
customer_ids = [f"CUST-{i:05d}" for i in range(1, N_CUSTOMERS + 1)]
customer_names = [f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}" for _ in range(N_CUSTOMERS)]
customer_region = [rng.choice(list(REGIONS.keys())) for _ in range(N_CUSTOMERS)]
customer_lookup = pd.DataFrame({
    "Customer ID": customer_ids, "Customer Name": customer_names, "Home Region": customer_region
})

# ---------------------------------------------------------------------
# DATE RANGE + SEASONALITY WEIGHTS (3 years, daily)
# ---------------------------------------------------------------------
date_range = pd.date_range("2023-01-01", "2025-12-31", freq="D")

def seasonality_weight(d: pd.Timestamp) -> float:
    w = 1.0
    if d.month == 1 and d.day <= 26:            # Republic Day sale
        w *= 1.4
    if d.month == 6:                             # End of season sale
        w *= 1.3
    if d.month == 8 and d.day <= 15:             # Independence Day sale
        w *= 1.35
    if d.month in (10, 11):                      # Diwali / festive season
        w *= 1.8
    if d.month == 12 and d.day >= 20:            # Christmas / New Year
        w *= 1.5
    if d.weekday() >= 5:                          # weekend bump
        w *= 1.15
    # mild year-over-year growth
    w *= 1 + (d.year - 2023) * 0.12
    return w

weights = np.array([seasonality_weight(d) for d in date_range])
weights = weights / weights.sum()

N_ORDERS = 11000
order_dates = rng.choice(date_range, size=N_ORDERS, p=weights)

# ---------------------------------------------------------------------
# BUILD TRANSACTIONS
# ---------------------------------------------------------------------
rows = []
cat_names = list(CATEGORIES.keys())

for i in range(N_ORDERS):
    cust_idx = rng.integers(0, N_CUSTOMERS)
    cust_id = customer_ids[cust_idx]
    cust_name = customer_names[cust_idx]
    region = customer_region[cust_idx]
    state = rng.choice(REGIONS[region]["states"])
    city = rng.choice(REGIONS[region]["cities"])

    category = rng.choice(cat_names)
    cat_info = CATEGORIES[category]
    product = rng.choice(cat_info["products"])

    unit_price = round(rng.uniform(*cat_info["price_range"]), 2)
    quantity = int(rng.choice([1, 1, 1, 2, 2, 3, 4, 5], p=[0.35, 0.2, 0.15, 0.12, 0.08, 0.05, 0.03, 0.02]))
    discount_pct = round(float(rng.choice([0, 0, 5, 10, 10, 15, 20, 25, 30],
                                           p=[0.28, 0.12, 0.12, 0.15, 0.1, 0.09, 0.07, 0.04, 0.03])), 0)

    order_date = pd.Timestamp(order_dates[i])
    # bigger discounts during festive/sale periods
    if order_date.month in (10, 11) or (order_date.month == 1 and order_date.day <= 26):
        discount_pct = min(discount_pct + rng.choice([0, 5, 10]), 40)

    gross_sales = round(unit_price * quantity, 2)
    sales = round(gross_sales * (1 - discount_pct / 100), 2)
    margin = rng.uniform(*cat_info["margin_range"])
    # heavy discounts can eat into or erase margin -> realistic occasional losses
    effective_margin = margin - (discount_pct / 100) * 0.6
    profit = round(sales * effective_margin, 2)

    ship_delay = int(rng.integers(1, 8))
    ship_date = order_date + pd.Timedelta(days=ship_delay)

    rows.append({
        "Order ID": f"ORD-{i+1:06d}",
        "Order Date": order_date.date().isoformat(),
        "Ship Date": ship_date.date().isoformat(),
        "Customer ID": cust_id,
        "Customer Name": cust_name,
        "Segment": rng.choice(SEGMENTS, p=[0.6, 0.25, 0.15]),
        "Region": region,
        "State": state,
        "City": city,
        "Category": category,
        "Product Name": product,
        "Quantity": quantity,
        "Unit Price": unit_price,
        "Discount %": discount_pct,
        "Sales": sales,
        "Profit": profit,
        "Payment Mode": rng.choice(PAYMENT_MODES, p=[0.42, 0.18, 0.16, 0.09, 0.15]),
        "Ship Mode": rng.choice(["Standard", "Express", "Same Day"], p=[0.6, 0.3, 0.1]),
    })

df = pd.DataFrame(rows).sort_values("Order Date").reset_index(drop=True)
df.to_csv("data/sales_data.csv", index=False)

print(f"Generated {len(df):,} rows -> data/sales_data.csv")
print(df.head())
print("\nDate range:", df["Order Date"].min(), "to", df["Order Date"].max())
print("Total Sales: ₹{:,.0f}".format(df["Sales"].sum()))
print("Total Profit: ₹{:,.0f}".format(df["Profit"].sum()))
