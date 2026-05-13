import asyncio
import time


zadachi = 8
n = 10_000_000_000_000

results = [0] * zadachi


async def calculate_sum(first, last):
    await asyncio.sleep(0)
    return (first + last) * (last - first + 1) // 2


async def worker(i, first, last):
    results[i] = await calculate_sum(first, last)


async def main():
    tasks = []
    chunk = n // zadachi

    start_time = time.perf_counter()


    for i in range(zadachi):
        first = i * chunk + 1

        if i == zadachi - 1:
            last = n
        else:
            last = (i + 1) * chunk

        print(f"Задача {i + 1}: от {first} до {last}")

        task = asyncio.create_task(worker(i, first, last))
        tasks.append(task)

    await asyncio.gather(*tasks)

    total = sum(results)

    end_time = time.perf_counter()

    print("Ответ:", await calculate_sum(1, n))
    print("Сумма:", total)
    print("Проверка:", total == await calculate_sum(1, n))
    print("Время:", end_time - start_time)


asyncio.run(main())
