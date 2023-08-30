from selenium import webdriver
from slugify import slugify
from selenium.webdriver.chrome.options import Options
from lxml import etree
from io import StringIO
import time
import re
import sys
import os


def fullpage_screenshot(url, path, _driver=None, save_html=False):
    driver = None
    if _driver is None:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--no-sandbox')

        driver = webdriver.Chrome('/usr/bin/chromedriver', chrome_options=chrome_options)
    else:
        driver = _driver
    driver.get(url)
    time.sleep(1)

    def S(X):
        return driver.execute_script('return document.body.parentNode.scroll'+X)
    driver.set_window_size(1920, 1080)
    driver.set_window_size(max(1920, S('Width')), S('Height'))
    driver.save_screenshot(path + ".png")

    if save_html:
        html = driver.page_source

        f = open(path + ".html", "w")
        f.write(html)
        f.close()

    if _driver is None:
        driver.quit()


def html_to_dsl(html, path, html_is_path):
    tree = None
    parser = etree.HTMLParser()
    if html_is_path:
        tree = etree.parse(html, parser)
    else:
        tree = etree.parse(StringIO(html), parser)
    root = tree.getroot()

    body = root.find("body")

    if body is None:
        return

    dsl = parse_html_node(body, "", None)

    if dsl is not None:
        f = open(path, "w")
        f.write(dsl)
        f.close()


def parse_html_node(node, indent, parent_class):
    cls = node_to_class(node)
    if cls == "Empty":
        return None
    pcls = cls

    if parent_class == cls:
        cls = None
        pcls = parent_class

    if cls is None:
        nindent = indent
    else:
        nindent = indent + "    "

    ress = []
    for child in node:
        ress.append(parse_html_node(child, nindent, pcls))
    ress = list(filter(None, ress))

    if cls is None:
        if len(ress) <= 0:
            return None
        return "\n".join(ress)

    if (cls == "Container" or cls == "Row" or cls == "Column") and len(ress) <= 0:
        return None

    result = indent + cls
    if len(ress) > 0:
        result += " {\n"

    result += "\n".join(ress)

    if len(ress) > 0:
        result += "\n" + indent + "}"

    return result


def node_to_class(node):
    if not hasattr(node, "tag") or not isinstance(node.tag, str):
        return None

    if "style" in node.attrib:
        s = node.attrib["style"]
        if ("display" in s and "none" in s) or "hidden" in s:
            return "Empty"
    if node.tag == "body":
        return "Body"
    elif node.tag == "ul":
        if "class" in node.attrib:
            c = node.attrib["class"]
            if "dropdown-menu" in c:
                return "Empty"
    elif node.tag == "div" or node.tag == "section":
        if "id" in node.attrib:
            i = node.attrib["id"]
            if "footer" in i:
                return "Footer"
        if "class" in node.attrib:
            c = node.attrib["class"]
            if "dropdown-menu" in c or "modal" in c:
                return "Empty"
            if "row" in c:
                return "Row"
            elif "col" in c.split(" ") or "col-" in c or "col_" in c:
                if "col-" in c and "-12" in c:
                    return "Row"
                return "Column"
            elif "navbar" in c.split(" "):
                return "Header"
            elif "footer" in c:
                return "Footer"
            elif "card" in c.split(" ") or "panel" in c.split(" "):
                return "Block"
            elif "container" in c:
                return "Container"
    elif node.tag == "header":
        return "Header"
    elif node.tag == "nav":
        if "class" in node.attrib:
            c = node.attrib["class"]
            if "navbar" in c:
                return "Header"
    elif node.tag == "footer":
        return "Footer"
    elif node.tag == "p":
        return "Paragraph"
    elif node.tag == "button":
        if "class" in node.attrib:
            c = node.attrib["class"]
            if "navbar-toggle" in c.split(" "):
                return "Empty"
        return "Button"
    elif node.tag == "a":
        if "class" in node.attrib:
            c = node.attrib["class"]
            if "button" in c:
                return "Button"
            elif "btn" in c:
                return "Button"
        for child in node:
            if not hasattr(node, "tag") or not isinstance(node.tag, str):
                continue
            elif child.tag == "img":
                return "Block"
            elif child.tag == "div":
                return "Container"
        return "Link"
    elif node.tag == "img":
        return "Image"
    elif re.match(r"h[1-3]", node.tag):
        return "Title"
    elif re.match(r"h[4-6]", node.tag):
        return "Subtitle"
    elif node.tag == "input":
        if "type" in node.attrib:
            t = node.attrib["type"]
            if t == "text" or t == "date" or t == "email" or t == "number" or t == "password" or t == "search":
                return "TextBox"
            elif t == "checkbox":
                return "CheckBox"
            elif t == "radio":
                return "RadioBox"
            elif t == "range":
                return "Range"
        return None
    elif node.tag == "textarea":
        return "TextBox"
    elif "src" in node.attrib and "script" not in node.tag:
        return "Image"
    else:
        return None


def generate_from_file(fullpath, webdir, root, _driver=None):
    r = None
    with open(fullpath) as fp:
        line = fp.readline()
        while line:
            if len(line) > 200:
                line = fp.readline()
                continue
            line = line.strip()
            fname = slugify(line)
            if not os.path.exists(root + "webpages/" + webdir + "/" + fname):
                os.makedirs(root + "webpages/" + webdir + "/" + fname)
            else:
                line = fp.readline()
                continue
            try:
                fullpage_screenshot(line, root + "webpages/" + webdir + "/" + fname + "/" + fname, _driver, True)
            except:
                print("failed on " + line)
                _driver.quit()
                chrome_options = Options()
                chrome_options.add_argument('enable-automation')
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--start-maximized')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument("--disable-infobars")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-browser-side-navigation")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--dns-prefetch-disable")

                _driver = webdriver.Chrome('/usr/bin/chromedriver', chrome_options=chrome_options)
                _driver.set_page_load_timeout(15)
                r = _driver
            print("generated screenshot and html from " + line)
            line = fp.readline()
    return r


if __name__ == "__main__":
    root = os.getcwd() + "/"
    args = sys.argv

    if "-f" not in args and "-g" not in args:
        print("Provide a website subdirectory")
        sys.exit(0)
    elif "-g" in args:
        webdir = args[args.index("-g") + 1]
        if not os.path.exists(root + "webpages/" + webdir):
            os.makedirs(root + "webpages/" + webdir)
    else:
        webdir = args[args.index("-f") + 1]
        if not os.path.exists(root + "webpages/" + webdir):
            os.makedirs(root + "webpages/" + webdir)

    if "-s" in args:
        chrome_options = Options()
        chrome_options.add_argument('enable-automation')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-browser-side-navigation")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--dns-prefetch-disable")

        driver = webdriver.Chrome('/usr/bin/chromedriver', chrome_options=chrome_options)
        driver.set_page_load_timeout(15)

    if "-g" in args:
        r = generate_from_file(root + "website_lists/" + args[args.index("-g") + 1], webdir, root, driver)
        if r is not None:
            driver = r

    print(root + "webpages/" + webdir)

    for subdir, dirs, files in os.walk(root + "webpages/" + webdir):
        for file in files:
            if file.endswith(".html"):
                fullpath = os.path.join(subdir, file)
                if "-s" in args and "-g" not in args:
                    if not os.path.exists(os.path.splitext(fullpath)[0] + ".png"):
                        try:
                            fullpage_screenshot("file:///" + fullpath,
                                                os.path.splitext(fullpath)[0],
                                                driver)
                            print("taken screenshot of " + fullpath)
                        except:
                            print("failed on " + fullpath)
                            driver.quit()
                            chrome_options = Options()
                            chrome_options.add_argument('enable-automation')
                            chrome_options.add_argument('--headless')
                            chrome_options.add_argument('--start-maximized')
                            chrome_options.add_argument('--no-sandbox')
                            chrome_options.add_argument('--disable-gpu')
                            chrome_options.add_argument("--disable-infobars")
                            chrome_options.add_argument("--disable-dev-shm-usage")
                            chrome_options.add_argument("--disable-browser-side-navigation")
                            chrome_options.add_argument("--disable-extensions")
                            chrome_options.add_argument("--dns-prefetch-disable")

                            driver = webdriver.Chrome('/usr/bin/chromedriver', chrome_options=chrome_options)
                            driver.set_page_load_timeout(15)

                if "-d" in args:
                    html_to_dsl(fullpath,
                                os.path.splitext(fullpath)[0] + ".gui",
                                True)
                    print("generated dsl of " + fullpath)

    if "-s" in args:
        driver.quit()

    # fullpage_screenshot("file:///" + os.getcwd() + "/" + filepath + "/index.html",
    #             filepath + "/screenshot.png")
