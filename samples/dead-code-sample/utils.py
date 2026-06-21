import json
import numpy
import os

temp = 123
active = True

def format_date():
    return "2026-01-01"

def main():
    print(json.dumps({"active": active}))

if __name__ == "__main__":
    main()
