#!/bin/bash
for p in 8080 8000 5173; do
  pids=$(lsof -ti:$p 2>/dev/null)
  if [ -n "$pids" ]; then echo "$pids" | xargs kill -9 2>/dev/null; echo "   :$p 종료"; fi
done
echo "── 다 껐다"
