import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ui.main_page import main

if __name__ == "__main__":
    main()
