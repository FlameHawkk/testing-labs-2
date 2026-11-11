#include <iostream>
#include <vector>
#include <thread>
#include <chrono>
#include <atomic>
#include <mutex>
#include <random>
#include <numeric>
#include <algorithm> // Сортировка (для задания 2)
#include <locale>

using namespace std;
using namespace chrono;


// --- 1. Эмуляция целевой системы (Target System) ---
// Имитируем обращение к БД или вызов внешнего API
bool simulate_network_request() {
    // Генерируем случайную задержку от 10 до 50 мс
    thread_local mt19937 generator(random_device{}());
    uniform_int_distribution<int> distribution(10, 50);

    int delay = distribution(generator);
    this_thread::sleep_for(milliseconds(delay));

    // Имитируем 5% вероятность ошибки (HTTP 500)
    return distribution(generator) > 12;
}

// --- 2. Глобальные счетчики метрик ---
atomic<int> successful_requests(0);
atomic<int> failed_requests(0);
mutex latencies_mutex;
vector<double> latencies; // Хранение времени отклика каждого запроса

// --- 3. Логика виртуального пользователя (Worker) ---
void load_worker(int requests_per_thread) {
    vector<double> local_latencies;
    local_latencies.reserve(requests_per_thread);

    for (int i = 0; i < requests_per_thread; ++i) {
        auto start_time = high_resolution_clock::now();

        bool success = simulate_network_request();

        auto end_time = high_resolution_clock::now();
        duration<double, milli> elapsed = end_time - start_time;

        local_latencies.push_back(elapsed.count());

        if (success) {
            successful_requests++;
        }
        else {
            failed_requests++;
        }
    }

    // Добавляем локальные метрики в глобальный вектор
    lock_guard<mutex> lock(latencies_mutex);
    latencies.insert(latencies.end(), local_latencies.begin(), local_latencies.end());
}

// --- 4. Координатор нагрузочного тестирования ---
int main() {
    setlocale(LC_ALL, "");

    // ЗАДАНИЕ 1: Проверка масштабируемости - измените константу num_threads с 50 на 500.
    const int num_threads = 500;            // Количество одновременных пользователей
    const int requests_per_thread = 20;    // Запросов на каждого пользователя
    const int total_requests = num_threads * requests_per_thread;

    cout << "Starting Load Test...\n";
    cout << "Virtual Users (Threads): " << num_threads << "\n";
    cout << "Requests per User: " << requests_per_thread << "\n";
    cout << "Total Requests planned: " << total_requests << "\n\n";

    auto test_start = high_resolution_clock::now();

    // Запуск потоков генерации нагрузки
    vector<thread> threads;
    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back(load_worker, requests_per_thread);

        // ЗАДАНИЕ 3: реализация Ramp-up (запуск с шагом 100 мс)
        this_thread::sleep_for(milliseconds(100));
    }

    // Ожидание завершения всех потоков
    for (auto& t : threads) {
        t.join();
    }

    auto test_end = high_resolution_clock::now();
    duration<double> test_duration = test_end - test_start;

    // --- 5. Анализ и вывод результатов ---
    double avg_latency = accumulate(latencies.begin(), latencies.end(), 0.0) / latencies.size();
    double tps = successful_requests.load() / test_duration.count();

    cout << "=== Результаты нагрузочного теста ===\n";
    cout << "Время выполения:               " << test_duration.count() << " секунд\n";
    cout << "Успешные запросы:              " << successful_requests.load() << "\n";
    cout << "Неудачные запросы:             " << failed_requests.load() << "\n";
    cout << "Пропускная способность (TPS):  " << tps << " запросов/сек\n";
    cout << "Средняя задержка:              " << avg_latency << " мс\n";

    // ЗАДАНИЕ 2: Расчет перцентилей (P95 и P99)
    sort(latencies.begin(), latencies.end()); // Сортируем по возрастанию

    // Вычисляем индексы для перцентилей
    size_t index95 = static_cast<size_t>(latencies.size() * 0.95);
    size_t index99 = static_cast<size_t>(latencies.size() * 0.99);

    // Защита от выхода за пределы массива
    if (index95 >= latencies.size()) index95 = latencies.size() - 1;
    if (index99 >= latencies.size()) index99 = latencies.size() - 1;

    double p95 = latencies[index95];
    double p99 = latencies[index99];
    
    // Вывод P95
    cout << "P95 задержка:   " << p95 << " мс\n"; 
    // Вывод P99
    cout << "P99 задержка:   " << p99 << " мс\n"; 

    return 0;
}