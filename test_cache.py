import requests
import time

for i in range(3):
    start = time.time()
    r = requests.post('http://localhost:8000/api/v1/query', json={
        'query': 'What is a large language model?',
        'top_k': 10,
        'top_n': 5
    })
    actual_time = round((time.time() - start) * 1000, 2)
    data = r.json()
    print(f'Run {i+1}: actual={actual_time}ms stored={data["latency_ms"]}ms')