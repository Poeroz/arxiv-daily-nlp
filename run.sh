date=$(date +"%a, %d %b %Y")
python3 run.py --date "${date}" \
    --mail-sender xxx@163.com \
    --mail-license yyy >> logs/${date}.txt