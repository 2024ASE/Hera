# import_test.py
import sys
import traceback
package_name = sys.argv[1]
try:
    __import__(package_name)
    print("Success")
except Exception as e:
    exc = traceback.format_exc()
    # print(f"Error: {exc}")
    print(f"{exc}")
