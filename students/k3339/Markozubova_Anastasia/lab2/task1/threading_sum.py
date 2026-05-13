import threading
import time


potoki = 8
n = 10_000_000_000_000

results = [0] * potoki


def calculate_sum(first, last):
    return (first + last) * (last - first + 1) // 2


def worker(i, first, last):
    results[i] = calculate_sum(first, last)


threads = []
chunk = n // potoki

for i in range(potoki):
    first = i * chunk + 1

    if i == potoki - 1:
        last = n
    else:
        last = (i + 1) * chunk

    print(f"Поток {i + 1}: от {first} до {last}")

    thread = threading.Thread(target=worker, args=(i, first, last))
    threads.append(thread)

start_time = time.perf_counter()

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

total = sum(results)

end_time = time.perf_counter()

print("Подход: threading")
print("Количество потоков:", potoki)
print("Ответ:", calculate_sum(1, n))
print("Сумма:", total)
print("Проверка:", total == calculate_sum(1, n))
print("Время:", end_time - start_time)
