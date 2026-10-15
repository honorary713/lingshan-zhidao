import sys
sys.path.insert(0, ".")
from app.knowledge.indexer import build_index

n = build_index()
print("BUILD_DONE chunks=", n)
