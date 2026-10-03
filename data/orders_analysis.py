import pandas as pd
import matplotlib.pyplot as plt

data = {
    'OrderID': [1001, 1002, 1003],
    'Customer': ['Alice', 'Bob', 'Alice'],
    'Product': ['Laptop', 'Chair', 'Mouse'],
    'Category': ['Electronics', 'Furniture', 'Electronics'],
    'Quantity': [1, 2, 3],
    'Price': [1500, 180, 25],
    'OrderDate': ['2023-06-01', '2023-06-03', '2023-06-05']
}

df = pd.DataFrame(data)
df['OrderDate'] = pd.to_datetime(df['OrderDate'])

df['TotalAmount'] = df['Quantity'] * df['Price']

print("--- Завдання 3 ---")
total_revenue = df['TotalAmount'].sum()
print(f"a. Сумарний дохід магазину: {total_revenue}")

average_amount = df['TotalAmount'].mean()
print(f"b. Середнє значення TotalAmount: {average_amount}")

orders_per_customer = df.groupby('Customer')['OrderID'].count()
print("c. Кількість замовлень по кожному клієнту:")
print(orders_per_customer)
print()

print("--- Завдання 4 ---")
print("Замовлення, в яких сума покупки перевищує 500:")
print(df[df['TotalAmount'] > 500])
print()

print("--- Завдання 5 ---")
print("Таблиця, відсортована за OrderDate у зворотному порядку:")
print(df.sort_values(by='OrderDate', ascending=False))
print()

print("--- Завдання 6 ---")
print("Замовлення, зроблені у період з 5 по 10 червня включно:")
june_orders = df[(df['OrderDate'] >= '2023-06-05') & (df['OrderDate'] <= '2023-06-10')]
print(june_orders)
print()

print("--- Завдання 7 ---")
category_grouped = df.groupby('Category').agg(
    ProductsCount=('Quantity', 'sum'),
    TotalSales=('TotalAmount', 'sum')
)
print("Групування за Category:")
print(category_grouped)
print()

print("--- Завдання 8 ---")
top_3_customers = df.groupby('Customer')['TotalAmount'].sum().sort_values(ascending=False).head(3)
print("ТОП-3 клієнтів за загальною сумою покупок:")
print(top_3_customers)
print()

orders_by_date = df.groupby('OrderDate').size()
plt.figure(figsize=(10, 5))
orders_by_date.plot(kind='bar', color='skyblue')
plt.title('Кількість замовлень по датах')
plt.xlabel('Дата замовлення')
plt.ylabel('Кількість замовлень')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('orders_by_date.png')
print("Графік 'orders_by_date.png' збережено.")

revenue_by_category = df.groupby('Category')['TotalAmount'].sum()
plt.figure(figsize=(8, 8))
revenue_by_category.plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff'])
plt.title('Розподіл доходів по категоріях')
plt.ylabel('')
plt.tight_layout()
plt.savefig('revenue_by_category.png')
print("Графік 'revenue_by_category.png' збережено.")
