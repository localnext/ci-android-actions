import subprocess
import json
import statistics
import time
import csv

NODE_URL = "https://github-readme-stats-nu-six-29.vercel.app/api?username=shiinasaku"
BUN_URL = "https://card.shiina.xyz/card/shiinasaku"

TOTAL_REQUESTS = 20000
CONCURRENCY = 200
RUNS = 20

def warmup(url):
    print(f"Warming up {url} ...")
    subprocess.run([
        "oha",
        "-n", "2000",
        "-c", "50",
        "--no-http2",
        url
    ], stdout=subprocess.DEVNULL)

def run_oha(url):
    result = subprocess.run([
        "oha",
        "-n", str(TOTAL_REQUESTS),
        "-c", str(CONCURRENCY),
        "--no-http2",
        "-j",
        url
    ], capture_output=True, text=True)

    data = json.loads(result.stdout)

    return {
        "rps": data["requests"]["average"],
        "p50": data["latency"]["percentiles"]["50"],
        "p95": data["latency"]["percentiles"]["95"],
        "p99": data["latency"]["percentiles"]["99"],
    }

def benchmark(name, url):
    results = []
    for i in range(RUNS):
        print(f"{name} Run {i+1}/{RUNS}")
        stats = run_oha(url)
        results.append(stats)
        time.sleep(5)  # small cooldown between runs
    return results

def median_stats(results):
    return {
        "median_rps": statistics.median(r["rps"] for r in results),
        "median_p50": statistics.median(r["p50"] for r in results),
        "median_p95": statistics.median(r["p95"] for r in results),
        "median_p99": statistics.median(r["p99"] for r in results),
    }

def save_csv(node_results, bun_results):
    with open("benchmark_results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["runtime", "run", "rps", "p50", "p95", "p99"])

        for i, r in enumerate(node_results):
            writer.writerow(["node", i+1, r["rps"], r["p50"], r["p95"], r["p99"]])

        for i, r in enumerate(bun_results):
            writer.writerow(["bun", i+1, r["rps"], r["p50"], r["p95"], r["p99"]])

if __name__ == "__main__":
    warmup(NODE_URL)
    warmup(BUN_URL)

    node_results = benchmark("Node", NODE_URL)
    bun_results = benchmark("Bun", BUN_URL)

    save_csv(node_results, bun_results)

    node_median = median_stats(node_results)
    bun_median = median_stats(bun_results)

    print("\n===== MEDIAN RESULTS =====")
    print("Node:", node_median)
    print("Bun :", bun_median)

    rps_improvement = (
        (bun_median["median_rps"] - node_median["median_rps"])
        / node_median["median_rps"]
    ) * 100

    print(f"\nBun RPS improvement: {rps_improvement:.2f}%")
