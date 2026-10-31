import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

# 1. Підготовка даних
np.random.seed(42)
tf.random.set_seed(42)

# Генерація 1000 випадкових точок у діапазоні [0, 1]
X = np.random.rand(1000, 2)
# Клас 1: x1 + x2 >= 1, Клас 0: x1 + x2 < 1
y = (X[:, 0] + X[:, 1] >= 1).astype(int)

# Розділення на навчальну (80%) та тестову (20%) вибірки
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 2. Створення нейронної мережі
model = tf.keras.Sequential([
    tf.keras.layers.Dense(4, activation='relu', input_shape=(2,)), 
    tf.keras.layers.Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# 3. Навчання моделі
# Обрано 100 епох для повної збіжності ваг на цій задачі
history = model.fit(X_train, y_train, epochs=100, validation_split=0.2, verbose=0)

# 4. Оцінка на тестовій вибірці
loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
print(f"Точність (Accuracy) на тестовій вибірці: {accuracy * 100:.2f}%\n")

# 5. Перевірка на 5 нових точках
new_points = np.array([
    [0.2, 0.3], # Сума = 0.5 (Очікується Клас 0)
    [0.8, 0.9], # Сума = 1.7 (Очікується Клас 1)
    [0.5, 0.5], # Сума = 1.0 (Очікується Клас 1)
    [0.1, 0.8], # Сума = 0.9 (Очікується Клас 0)
    [0.9, 0.2]  # Сума = 1.1 (Очікується Клас 1)
])

print("Передбачений клас для 5 нових точок:")
predictions = model.predict(new_points, verbose=0)
# Поріг 0.5 для Sigmoid
predicted_classes = (predictions >= 0.5).astype(int)

for i in range(len(new_points)):
    print(f"Точка (x1, x2): {new_points[i]} -> Передбачений Клас: {predicted_classes[i][0]} (Ймовірність: {predictions[i][0]:.4f})")

# 6. Побудова графіків Loss та Accuracy
plt.figure(figsize=(14, 5))

# Графік Loss
plt.subplot(1, 2, 1)
plt.plot(history.history['loss'], label='Навчальна вибірка')
plt.plot(history.history['val_loss'], label='Валідаційна вибірка')
plt.title('Зміна функції втрат (Loss)')
plt.xlabel('Епохи')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)

# Графік Accuracy
plt.subplot(1, 2, 2)
plt.plot(history.history['accuracy'], label='Навчальна вибірка')
plt.plot(history.history['val_accuracy'], label='Валідаційна вибірка')
plt.title('Зміна точності (Accuracy)')
plt.xlabel('Епохи')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)

plt.show()
