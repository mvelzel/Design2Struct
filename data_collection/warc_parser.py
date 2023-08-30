from warcio.archiveiterator import ArchiveIterator
import time
import json
import os


LINES_CHECK_MAX = 500
WHITELIST = ["materialize.min.css", "materialize.css"]
BLACKLIST = []


def filter_warc(warc_filepath):
    f = open(warc_filepath, 'rb')
    f2 = open(warc_filepath, 'rb')

    blacklist = []
    record_list = []

    for record in ArchiveIterator(f):
        if record.rec_type == 'metadata':
            res = str(record.raw_stream.read())
            if "languages-cld2" in res:
                metadata = json.loads(res[res.find("{"):res.rfind("}") + 1])
                if "languages" in metadata:
                    for language in metadata["languages"]:
                        if language["code"] != "en":
                            blacklist.append(record.rec_headers.get_header('WARC-Target-URI'))
                            break

    f.close()

    print("finished metadata of " + warc_filepath)

    for record in ArchiveIterator(f2):
        if record.rec_type == 'response':
            if (record.http_headers is not None and
                    "text/html" in str(record.http_headers.get_header('Content-Type')) and
                    record.rec_headers is not None and
                    "text/html" in str(record.rec_headers.get_header("WARC-Identified-Payload-Type"))):
                uri = record.rec_headers.get_header('WARC-Target-URI')
                block = False
                for b in blacklist:
                    if b in uri:
                        block = True
                        break
                if block:
                    continue
                stream = record.content_stream()
                for i in range(LINES_CHECK_MAX):
                    line = str(stream.readline())
                    done = "</head>" in line
                    if done:
                        break
                    for w in BLACKLIST:
                        if w in line:
                            done = True
                            break
                    if done:
                        break
                    for w in WHITELIST:
                        if w in line:
                            record_list.append(record)
                            done = True
                            break
                    if done:
                        break

    f2.close()

    print("finished " + warc_filepath)
    return record_list


if __name__ == "__main__":
    root = os.getcwd() + "/"

    record_list = []
    for subdir, dirs, files in os.walk(root + "warcs"):
        for file in files:
            if file.endswith(".warc.gz"):
                fullpath = os.path.join(subdir, file)
                record_list += filter_warc(fullpath)
    timestr = time.strftime("%Y%m%d_%H%M%S")
    filename = "WEBSITE_LIST_" + timestr
    fullpath = root + "website_lists/" + filename
    urilist = map(lambda r: str(r.rec_headers.get_header("WARC-Target-URI")) + "\n",
                  record_list)
    f = open(fullpath, "w")
    f.writelines(urilist)
    f.close()
    print(len(record_list))
    print("done")
