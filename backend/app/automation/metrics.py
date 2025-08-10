from prometheus_client import Counter

runs_started = Counter("auto_runs_started", "Automation runs started", ["intent"])
runs_success = Counter("auto_runs_succeeded", "Automation runs succeeded", ["intent"])
runs_failed = Counter("auto_runs_failed", "Automation runs failed", ["intent"])
runs_retried = Counter("auto_runs_retried", "Automation runs retried", ["intent"])
