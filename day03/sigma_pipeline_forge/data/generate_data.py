"""
Sigma DataTech — Electronics Sales Data Generator
Generates customers, products, and 5 days of sales orders across top Indian cities.
Day 3 has planted data quality issues for students to discover.
Dates: 2026-05-01 to 2026-05-05
"""
import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

# ── Reference data ─────────────────────────────────────────────────────────────
CITIES = [
    'Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad',
    'Pune', 'Kolkata', 'Ahmedabad', 'Jaipur', 'Surat'
]

TIERS = ['Gold', 'Silver', 'Bronze']
PAYMENT_METHODS = ['UPI', 'Net Banking', 'Credit Card', 'Debit Card', 'EMI']
STATUSES = ['completed', 'pending', 'failed', 'returned']

CATEGORIES = ['Smartphones', 'Laptops', 'Tablets', 'Audio', 'Cameras',
              'Wearables', 'Gaming', 'Accessories', 'Smart Home', 'Television']

FIRST_NAMES = [
    'Rahul', 'Priya', 'Arjun', 'Sneha', 'Vikram', 'Ananya', 'Rohan', 'Kavya',
    'Aditya', 'Divya', 'Kiran', 'Meera', 'Sanjay', 'Neha', 'Amit', 'Pooja',
    'Rajesh', 'Sunita', 'Deepak', 'Anjali', 'Suresh', 'Ritu', 'Manoj', 'Swati',
    'Ajay', 'Nisha', 'Vikas', 'Preeti', 'Nitin', 'Smita', 'Ravi', 'Lakshmi',
    'Ganesh', 'Padma', 'Harish', 'Rekha', 'Mohan', 'Usha', 'Vinod', 'Geeta'
]
LAST_NAMES = [
    'Sharma', 'Gupta', 'Patel', 'Singh', 'Kumar', 'Joshi', 'Rao', 'Nair',
    'Iyer', 'Reddy', 'Shah', 'Mehta', 'Verma', 'Agarwal', 'Mishra', 'Tiwari',
    'Pandey', 'Dubey', 'Jain', 'Malhotra', 'Chopra', 'Bose', 'Das', 'Mukherjee'
]

PRODUCT_NAMES = [
    # Smartphones
    'Samsung Galaxy S25', 'iPhone 16 Pro', 'OnePlus 13', 'Pixel 9 Pro', 'Vivo X200',
    'Realme 14 Pro', 'Redmi Note 14 Pro', 'iQOO 13', 'Motorola Edge 50', 'Oppo Reno 13',
    # Laptops
    'Dell XPS 15', 'MacBook Air M4', 'HP Spectre x360', 'Lenovo ThinkPad X1', 'Asus ZenBook 14',
    'Acer Swift 5', 'Microsoft Surface Pro 11', 'MSI Prestige 16', 'Razer Blade 15', 'LG Gram 17',
    # Tablets
    'iPad Pro M4', 'Samsung Galaxy Tab S10', 'OnePlus Pad 2', 'Lenovo Tab P12 Pro', 'Realme Pad X',
    # Audio
    'Sony WH-1000XM6', 'Bose QC Ultra', 'Apple AirPods Pro 3', 'Sennheiser Momentum 4', 'JBL Live 770',
    'boAt Airdopes 800', 'Noise Buds VS204', 'Realme Buds Air 6', 'OnePlus Buds Pro 3', 'Nothing Ear 3',
    # Cameras
    'Sony Alpha ZV-E10 II', 'Canon EOS R50', 'Fujifilm X-T50', 'GoPro Hero 13', 'DJI Osmo Pocket 3',
    # Wearables
    'Apple Watch Ultra 3', 'Samsung Galaxy Watch 7', 'Garmin Fenix 8', 'Fitbit Charge 7', 'Noise ColorFit Ultra',
    # Gaming
    'PlayStation 5 Slim', 'Xbox Series X', 'Nintendo Switch 2', 'Razer DeathAdder V3', 'Logitech G Pro X',
    # Smart Home
    'Amazon Echo Show 15', 'Google Nest Hub Max', 'Ring Video Doorbell Pro', 'Philips Hue Starter Kit',
    # Television
    'Samsung QLED 65"', 'LG OLED C4 55"', 'Sony Bravia X90L 75"'
]


def generate_customers(n=200):
    customers = []
    for i in range(n):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        email = f"{first.lower()}.{last.lower()}{i}@gmail.com"
        phone = f"+91{random.randint(7000000000, 9999999999)}"
        tier = random.choices(TIERS, weights=[0.20, 0.35, 0.45])[0]
        signup = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 500))
        customers.append({
            'customer_id': f'CUST{str(i + 1).zfill(4)}',
            'name': f'{first} {last}',
            'email': email,
            'phone': phone,
            'city': random.choice(CITIES),
            'tier': tier,
            'signup_date': signup.strftime('%Y-%m-%d'),
        })
    return pd.DataFrame(customers)


def generate_products():
    products = []
    for i, name in enumerate(PRODUCT_NAMES):
        category = CATEGORIES[i // 5] if i < 50 else random.choice(CATEGORIES)
        # Price ranges by category
        price_ranges = {
            'Smartphones': (8000, 140000),
            'Laptops': (45000, 250000),
            'Tablets': (15000, 120000),
            'Audio': (999, 35000),
            'Cameras': (25000, 90000),
            'Wearables': (2000, 90000),
            'Gaming': (3000, 55000),
            'Accessories': (500, 8000),
            'Smart Home': (2500, 25000),
            'Television': (35000, 280000),
        }
        low, high = price_ranges.get(category, (1000, 50000))
        products.append({
            'product_id': f'PROD{str(i + 1).zfill(3)}',
            'name': name,
            'category': category,
            'price': round(random.uniform(low, high), 2),
            'stock_quantity': random.randint(10, 500),
            'brand': name.split()[0],
            'is_active': random.choices([True, False], weights=[0.92, 0.08])[0],
        })
    return pd.DataFrame(products)


def generate_orders(day_num, date_str, n=200, plant_issues=False):
    customer_ids = [f'CUST{str(i + 1).zfill(4)}' for i in range(200)]
    product_ids = [f'PROD{str(i + 1).zfill(3)}' for i in range(len(PRODUCT_NAMES))]
    base = (day_num - 1) * n + 1

    rows = []
    for i in range(n):
        hour = random.randint(8, 23)      # realistic shopping hours
        minute = random.randint(0, 59)
        quantity = random.choices([1, 2, 3], weights=[0.80, 0.15, 0.05])[0]
        prod_id = random.choice(product_ids)
        prod_idx = int(prod_id.replace('PROD', '')) - 1
        prod_idx = min(prod_idx, len(PRODUCT_NAMES) - 1)
        base_price = round(random.uniform(500, 150000), 2)
        amount = round(base_price * quantity, 2)

        rows.append({
            'order_id': f'ORD{str(base + i).zfill(6)}',
            'customer_id': random.choice(customer_ids),
            'product_id': prod_id,
            'quantity': quantity,
            'amount': amount,
            'status': random.choices(STATUSES, weights=[0.78, 0.10, 0.07, 0.05])[0],
            'payment_method': random.choice(PAYMENT_METHODS),
            'city': random.choice(CITIES),
            'created_at': f"{date_str} {str(hour).zfill(2)}:{str(minute).zfill(2)}:00",
        })

    df = pd.DataFrame(rows)

    if plant_issues:
        # Issue 1: 10 negative amounts (refund misposted as new order)
        for idx in random.sample(range(n), 10):
            df.at[idx, 'amount'] = -abs(df.at[idx, 'amount'])

        # Issue 2: 5 duplicate order_ids (payment retry without idempotency check)
        for k in range(5):
            df.at[n - k - 1, 'order_id'] = df.at[k, 'order_id']

        # Issue 3: 3 null customer_ids (guest checkout — customer linkage failed)
        for idx in random.sample(range(n), 3):
            df.at[idx, 'customer_id'] = None

        # Issue 4: 4 zero-quantity orders (cart bug)
        for idx in random.sample(range(n), 4):
            df.at[idx, 'quantity'] = 0

    return df


if __name__ == '__main__':
    out_dir = os.path.dirname(os.path.abspath(__file__))

    customers = generate_customers(200)
    customers.to_csv(os.path.join(out_dir, 'customers.csv'), index=False)
    print(f"✅ customers.csv     — {len(customers)} rows")

    products = generate_products()
    products.to_csv(os.path.join(out_dir, 'products.csv'), index=False)
    print(f"✅ products.csv      — {len(products)} rows")

    dates = ['2026-05-01', '2026-05-02', '2026-05-03', '2026-05-04', '2026-05-05']
    for day_num, date_str in enumerate(dates, start=1):
        has_issues = (day_num == 3)
        orders = generate_orders(day_num, date_str, n=200, plant_issues=has_issues)
        fname = os.path.join(out_dir, f'orders_day{day_num}.csv')
        orders.to_csv(fname, index=False)
        tag = '⚠️  (10 neg amounts, 5 dup IDs, 3 null customers, 4 zero-qty PLANTED)' if has_issues else ''
        print(f"✅ orders_day{day_num}.csv  — {len(orders)} rows  {tag}")

    print("\n✅ All data ready. Electronics sales data — India cities — May 2026.")
