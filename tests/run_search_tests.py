import os
import sys
from dotenv import load_dotenv

# Support both:
# - python tests/run_search_tests.py
# - python -m tests.run_search_tests
if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tests.search_test_suite import SearchTestSuite
else:
    from .search_test_suite import SearchTestSuite

print("FILE IS RUNNING...")  # debug

def main():
    # Ensure Vietnamese text prints correctly on Windows terminals.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # Load environment variables from .env in project root.
    load_dotenv()
    print("START TESTING...")

    suite = SearchTestSuite()
    results = suite.run()

    print("DONE RUNNING\n")

    for r in results:
        print("="*50)
        print("Category:", r["category"])
        print("Q:", r["question"])
        print("Expected:", r["expected"])
        print("Answer:", r["answer"])

if __name__ == "__main__":
    main()