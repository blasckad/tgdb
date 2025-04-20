import pandas as pd
import time
from datetime import datetime, timedelta
from create import write_node, write_edge, save_all_indexes

# Путь к распакованным CSV
DATA_DIR = "..\data"


def load_instacart_data():
    orders = pd.read_csv(f"{DATA_DIR}/orders.csv")
    products = pd.read_csv(f"{DATA_DIR}/products.csv")
    prior = pd.read_csv(f"{DATA_DIR}/order_products__prior.csv")

    return orders, products, prior


def simulate_unix_timestamp(start_date: datetime, days_offset: float, hour: int):
    dt = start_date + timedelta(days=days_offset, hours=hour)
    return int(dt.timestamp())


def process_instacart_to_tgdb():
    orders, products, prior = load_instacart_data()

    merged = prior.merge(orders, on='order_id', how='left')
    merged = merged.merge(products, on='product_id', how='left')

    print("Записей для обработки:", len(merged))

    base_date = datetime(2015, 1, 1)  # фиктивная стартовая точка во времени
    user_last_seen = {}

    for _, row in merged.iterrows():
        user_id = f"user_{row['user_id']}"
        product_id = f"product_{row['product_id']}"
        product_name = row['product_name']

        # Считаем "дни с начала" как сумму всех days_since_prior_order
        if row['user_id'] not in user_last_seen:
            days_offset = 0
        else:
            days_offset = user_last_seen[row['user_id']] + (
                row['days_since_prior_order'] if pd.notna(row['days_since_prior_order']) else 0)

        user_last_seen[row['user_id']] = days_offset

        timestamp = simulate_unix_timestamp(base_date, days_offset, row['order_hour_of_day'])

        # Узлы
        write_node(name=user_id, timestamp=timestamp, active=True, data={})
        write_node(name=product_id, timestamp=timestamp, active=True, data={"product_name": product_name})

        # Ребро покупки
        write_edge(from_name=user_id, to_name=product_id, timestamp_start=timestamp, active=True,
                   data={"action": "buy"})

    save_all_indexes()
    print("✅ Все данные Instacart записаны в TGDB")


if __name__ == "__main__":
    process_instacart_to_tgdb()
