import sys

# Asegurar que 'lib' esté en sys.path tanto en CircuitPython como en IDEs/PC
if "lib" not in sys.path and "/lib" not in sys.path:
    sys.path.insert(0, "lib")

from utils.main import main


if __name__ == "__main__":
    main()