import sys
import os

# Ensure project root directory is in Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# Vercel serverless function entrypoint
if __name__ == '__main__':
    app.run()
