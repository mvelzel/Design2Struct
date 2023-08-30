import os
import shutil
import sys


def translate_pix2code(path):
    f = open(path, "r")
    content = f.read()
    f.close()

    translated = content.replace("body", "Body").replace("header", "Header").replace("btn-inactive", "Link") \
        .replace("btn-active", "Button").replace("btn-green", "Button").replace("btn-orange", "Button") \
        .replace("btn-red", "Button").replace("big-title", "Title").replace("small-title", "Subtitle") \
        .replace("row", "Row").replace("single", "Column").replace("double", "Column") \
        .replace("quadruple", "Column").replace("text", "Paragraph").replace(", ", "\n").replace(",", "\n")

    if "Body" not in translated:
        result = "Body {\n" + translated + "}"
    else:
        result = translated

    f = open(path, "w")
    f.write(result)
    f.close()


if __name__ == "__main__":
    root = os.getcwd() + "/"
    args = sys.argv

    if "-f" not in args:
        print("Provide a website subdirectory")
        sys.exit(0)
    else:
        webdir = args[args.index("-f") + 1]
        if not os.path.exists(root + "webpages/" + webdir):
            print("Directory does not exist")
            sys.exit(0)
    fullwebdir = root + "webpages/" + webdir

    if "-d" in args:
        for subdir, dirs, files in os.walk(root + "webpages/" + webdir):
            for file in files:
                if file.endswith(".gui") or file.endswith(".png") or file.endswith(".html"):
                    unext = os.path.splitext(file)[0]
                    if subdir == fullwebdir:
                        if not os.path.exists(subdir + "/" + unext):
                            os.makedirs(subdir + "/" + unext)
                        os.rename(os.path.join(subdir, file), os.path.join(subdir + "/" + unext, file))

    if "-fl" in args:
        for subdir, dirs, files in os.walk(root + "webpages/" + webdir):
            for file in files:
                if file.endswith(".gui") or file.endswith(".png") or file.endswith(".html"):
                    unext = os.path.splitext(file)[0]
                    if subdir != fullwebdir:
                        os.rename(os.path.join(subdir, file), os.path.join(subdir + "/..", file))
                        if (not os.path.exists(subdir + "/" + unext + ".png") and
                           not os.path.exists(subdir + "/" + unext + ".gui") and
                           not os.path.exists(subdir + "/" + unext + ".html")):
                            shutil.rmtree(subdir)

    if "-t" in args:
        for subdir, dirs, files in os.walk(root + "webpages/" + webdir):
            for file in files:
                if file.endswith(".gui"):
                    translate_pix2code(os.path.join(subdir, file))
