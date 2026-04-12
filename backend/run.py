import sys
sys.path.insert(0, r'C:\Users\bavad\OneDrive\Desktop\Kaal_1\plagiarism-detector')

from uvicorn import run

if __name__ == "__main__":
    run("backend.app.main:app")