run:
  uv run main.py

proto:
  protoc --python_out=. pricing.proto
