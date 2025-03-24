import os
import time
import pandas as pd
from pyalma import SshClient
from memory_profiler import memory_usage

MY_FReader = SshClient("alma-app.icr.ac.uk", "msarkis", "lol")

DATA_DIR = "/data/scratch/DCO/DIGOPS/SCIENCOM/msarkis/from_lewis/"

sizes = ["20000", "50000", "100000", "200000"]

# measure execution time and memory usage
def measure_performance(func, *args, **kwargs):
    """Measures execution time and peak memory usage of a function."""
    
    start_time = time.time()
    mem_usage = memory_usage((func, args, kwargs), max_usage=True)
    end_time = time.time()

    return {
        "time_sec": round(end_time - start_time, 4),
        "memory_MB": round(mem_usage, 2)
    }

if __name__ == "__main__": 
    results = []
    for size in sizes:
        path = os.path.join(DATA_DIR, f"adata_subsample_{size}.h5ad")
        local_path = f"adata_local_copy_{size}.h5ad"

        print(f"\n📂 Testing dataset size: {size} ({path})")

        # perf for loading the file remotely
        load_perf = measure_performance(MY_FReader.load_h5ad_file, path, local_path)

        # perf for reading the file locally
        read_perf = measure_performance(MY_FReader.read_h5ad, local_path)

        # Store results
        results.append({
            "Dataset Size": size,
            "Load Time (s)": load_perf["time_sec"],
            "Load Memory (MB)": load_perf["memory_MB"],
            "Read Time (s)": read_perf["time_sec"],
            "Read Memory (MB)": read_perf["memory_MB"]
        })

    df_results = pd.DataFrame(results)
    print(df_results)

    # Save results to CSV
    df_results.to_csv("performance_results.csv", index=False)
    print("\n✅ Performance results saved to 'performance_results.csv'")


#/Users/msarkis/Documents/pyalma/.env-py/bin/python -m streamlit run stindex.py
