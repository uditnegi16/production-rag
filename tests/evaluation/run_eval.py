import json
import requests
import time
from hallucination_checker import check_hallucination, check_keyword_coverage

API_URL = "http://localhost:8000/api/v1/query"
EVAL_PATH = "tests/evaluation/eval_dataset.json"
DOC_ID = None  # set to your doc_id if you want to scope to one document

def run_evaluation():
    with open(EVAL_PATH) as f:
        dataset = json.load(f)

    results = []
    passed = 0
    hallucinated = 0
    fallbacks = 0

    print(f"\nRunning evaluation on {len(dataset)} questions...\n")
    print("-" * 60)

    for entry in dataset:
        response = requests.post(API_URL, json={
            "query": entry["question"],
            "doc_id": DOC_ID,
            "top_k": 10,
            "top_n": 5,
        })

        if response.status_code != 200:
            print(f"[{entry['id']}] API ERROR: {response.status_code}")
            continue

        data = response.json()
        time.sleep(1)  # avoid rate limiting on free Groq tier

        if data.get("is_fallback"):
            fallbacks += 1
            print(f"[{entry['id']}] FALLBACK — {entry['question']}")
            results.append({**entry, "status": "fallback"})
            continue

        hallucination = check_hallucination(
            answer=data.get("answer", ""),
            source_text=data.get("source_text", ""),
        )

        keyword = check_keyword_coverage(
            answer=data.get("answer", ""),
            expected_keywords=entry["expected_keywords"],
        )

        test_passed = not hallucination["hallucinated"] and keyword["passed"]
        if test_passed:
            passed += 1
        if hallucination["hallucinated"]:
            hallucinated += 1

        status = "PASS" if test_passed else "FAIL"
        print(f"[{entry['id']}] {status} — {entry['question']}")
        print(f"         Overlap: {hallucination['overlap_score']} | Keywords: {keyword['coverage']} | Page: {data.get('source_page')}")

        results.append({
            **entry,
            "status": status,
            "answer": data.get("answer"),
            "source_page": data.get("source_page"),
            "confidence": data.get("confidence"),
            "latency_ms": data.get("latency_ms"),
            "hallucination": hallucination,
            "keyword_coverage": keyword,
        })

    print("-" * 60)
    print(f"\nRESULTS SUMMARY")
    print(f"Total:       {len(dataset)}")
    print(f"Passed:      {passed}")
    print(f"Failed:      {len(dataset) - passed - fallbacks}")
    print(f"Fallbacks:   {fallbacks}")
    print(f"Hallucinated:{hallucinated}")
    print(f"Pass rate:   {round(passed / len(dataset) * 100, 1)}%")

    with open("tests/evaluation/eval_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results saved to tests/evaluation/eval_results.json")


if __name__ == "__main__":
    run_evaluation()