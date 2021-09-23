import time
import json
import argparse
import requests
import smtplib
import email
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


parser = argparse.ArgumentParser(description="This script will crawl papers related to NLP on arxiv everyday")
parser.add_argument("--date", type=str, help="The date today in RFC 2822 format, e.g. Thu, 23 Sep 2021")
parser.add_argument("--mail-sender", type=str, help="The email address of sender, e.g. xxx@163.com")
parser.add_argument("--mail-license", type=str, help="License of sender")
args = parser.parse_args()
# files_dir = "/home/ubuntu/ArxivDailyMT/files/"
files_dir = "files/"


def get_page(url):
    response = requests.get(url)
    if response.status_code == 200:
        html = response.text
    else:
        raise RequestException

    return html


def extract(html):
    soup = BeautifulSoup(html, "html.parser")
    entry = soup.find("h3")
    date = entry.next_element
    assert date == args.date, "Not today's papers"
    content = date.next_element.next_element
    all_dt = content.find_all("dt")
    all_dd = content.find_all("dd")
    assert len(all_dt) == len(all_dd), "Different numbers of link info and paper info"
    all_info = []
    for idx in range(len(all_dt)):
        dt = all_dt[idx]
        dd = all_dd[idx]
        # link info
        info = {}
        abstract = dt.select('[title="Abstract"]')
        pdf = dt.select('[title="Download PDF"]')
        other = dt.select('[title="Other formats"]')
        link = {
            "abstract": "https://arxiv.org" + abstract[0].get("href") if abstract else "",
            "pdf": "https://arxiv.org" + pdf[0].get("href") if pdf else "",
            "other": "https://arxiv.org" + other[0].get("href") if other else "",
        }
        info["id"] = abstract[0].text if abstract else ""
        info["url"] = link
        # paper info
        meta = dd.select("div.meta")
        assert meta, "Meta info not exist"
        title = meta[0].select(".list-title")
        authors = meta[0].select(".list-authors")
        subjects = meta[0].select(".list-subjects")
        comments = meta[0].select(".list-comments")

        title = title[0].text.strip().replace("Title: ", "") if title else ""
        author_list = []
        if authors:
            for author in authors[0].find_all("a"):
                link = "https://arxiv.org" + author.get("href")
                name = author.text.strip()
                author_list.append({
                    "name": name,
                    "url": link
                })
        subjects = subjects[0].text.strip().replace("Subjects: ", "") if subjects else ""
        comments = comments[0].text.strip().replace("Comments: ", "") if comments else ""
        info["title"] = title
        info["authors"] = author_list
        info["comments"] = comments
        info["subjects"] = subjects
        all_info.append(info)
    
    return all_info


def filter(all_info, keywords):
    filtered_info = []
    for info in all_info:
        flag = False
        for keyword in keywords:
            if keyword in info["title"].lower():
                flag = True
                break
        if flag:
            filtered_info.append(info)

    return filtered_info


def save_file(all_info, filepath, keywords=[]):
    filtered_info = filter(all_info, keywords)
    with open(filepath, "w") as f:
        json.dump(filtered_info, f, indent=4)


def make_html(all_info, keywords):
    filtered_info = filter(all_info, keywords)
    body_html = ""
    for idx, info in enumerate(filtered_info):
        url = info["url"]["abstract"]
        title = info["title"]
        author_list = [author["name"] for author in info["authors"]]
        authors = ", ".join(author_list)
        comments = info["comments"]
        html = f"""
        <p>[{idx + 1}] <a href='{url}'>{title}</a></p>
        <p>{authors}</p>
        <p>Comments: {comments}</p>
        """
        body_html += html

    return body_html


def send_emails(all_info):
    mail_host = "smtp.163.com"
    mail_sender = args.mail_sender
    mail_license = args.mail_license

    stp = smtplib.SMTP()
    stp.connect(mail_host, 25)
    stp.set_debuglevel(1)
    stp.login(mail_sender, mail_license)

    receivers_info = []
    with open(files_dir + "receivers_list.txt", "r") as f:
        for item in f.readlines():
            name, address, keywords = item.strip().split("|")
            receivers_info.append((name, address, keywords))
    
    for receiver in receivers_info:
        name, address, keywords = receiver
        mail_receiver = [address]
        mm = MIMEMultipart("related")
        mm["From"] = f"ArxivDaily<{mail_sender}>"
        mm["Subject"] = Header(f"Arxiv Daily ({args.date})", "utf-8")
        mm["To"] = f"{name}<{address}>"
        body_content = make_html(all_info, keywords.split(','))
        message_text = MIMEText(body_content, "html", "utf-8")
        mm.attach(message_text)
        stp.sendmail(mail_sender, mail_receiver, mm.as_string())
        localtime = time.asctime(time.localtime(time.time()))
        print(f"{localtime} | Successfully send email to {name}<{address}>")

    stp.quit()


def main():
    url = "https://arxiv.org/list/cs.CL/pastweek?skip=0&show=200"
    html = get_page(url)
    all_info = extract(html)
    date_title = "-".join(args.date.split(" ")[1:])
    save_file(all_info, files_dir + f"{date_title}.json", keywords=[])
    save_file(all_info, files_dir + f"{date_title}-MT.json", keywords=["translation"])
    send_emails(all_info)

if __name__ == "__main__":
    main()