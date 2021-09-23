# arxiv-daily-nlp
A python script which sends email of NLP papers on arxiv everyday

## 0. Quick start

First, you should add receivers' information into `files/receivers_list.txt`, with following format `name|email|keywords`, for example:

```
Donald Trump|trump@maga.com|translation,dialogue,generation
```

Then, you should make a directory `logs/` to save the logs:

```
mkdir logs
```

Finally, replace `xxx` and `yyy` in `run.sh` with your email account and email license code:

```
date=$(date +"%a, %d %b %Y")
python3 run.py --date "${date}" \
    --mail-sender xxx@163.com \
    --mail-license yyy >> logs/${date}.txt
```

Now just type `sh run.sh` in the command-line!

## 1. Daily notification

If you want a daily notification, please search the usage of `crontab` command in Linux and help yourself!