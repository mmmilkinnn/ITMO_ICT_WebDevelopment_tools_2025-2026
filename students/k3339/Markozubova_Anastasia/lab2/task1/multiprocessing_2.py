import multiprocessing
import time


processi = 8
n = 10_000_000_000_000


def calculate_sum(first, last):
    return (first + last) * (last - first + 1) // 2


def worker(i, first, last, results):
    results[i] = calculate_sum(first, last)


if __name__ == "__main__":
    manager = multiprocessing.Manager()
    results = manager.list([0] * processi)

    processes = []
    chunk = n // processi

    start_time = time.perf_counter()

    for i in range(processi):
        first = i * chunk + 1

        if i == processi - 1:
            last = n
        else:
            last = (i + 1) * chunk

        print(f"Процесс {i + 1}: от {first} до {last}")

        process = multiprocessing.Process(
            target=worker,
            args=(i, first, last, results)
        )
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    total = sum(results)

    end_time = time.perf_counter()

    print("Ответ:", calculate_sum(1, n))
    print("Сумма:", total)
    print("Проверка:", total == calculate_sum(1, n))
    print("Время:", end_time - start_time)
