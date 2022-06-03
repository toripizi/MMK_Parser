from src.api import MWApi
from bs4 import BeautifulSoup, element
from src.data import forbidden_tags, new_line_tags


class MWParser:
    def __init__(self, cache_folder, URL="https://en.wikipedia.org/w/api.php"):
        self.api = MWApi(URL, cache_folder)
        self.parsed = None

    def parse_wikicode(self, text):
        soup = BeautifulSoup(self.api.parse(text), "html.parser")
        root = soup.find("div", {"class": "mw-parser-output"})
        self.parsed = ParserJob(root)
        return self.parsed

    def parse_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        root = soup.find()
        self.parsed = ParserJob(root)
        return self.parsed


class ParserJob:
    def __init__(self, root):
        self.root = root
        self.text = [""]
        self.data = []
        self.textLocation = 0
        self.process(root)
        self.repair_text()

    def repair_text(self):
        if not self.text[-1]:
            self.text.pop()
        self.text = [line.strip() for line in self.text]

    def process(self, section):
        {
            element.Tag: self.process_tag,
            element.NavigableString: self.process_string,
            element.Comment: lambda a: None,
        }[type(section)](section)

    def process_tag(self, tag):
        # TODO zrefactorować to trzeba
        for forbidden_tag in forbidden_tags:
            if forbidden_tag["name"] == tag.name:
                match = True
                for name, value in forbidden_tag["attrs"].items():
                    if not (name in tag.attrs and tag.attrs[name] == value):
                        match = False
                if match:
                    return
        # TODO zrefactorować to trzeba

        if tag.name in new_line_tags:
            if len(self.text[self.textLocation]) > 0:
                self.textLocation += 1
                self.text.append("")
        obj = {
            "tag": tag.name,
            "attrs": tag.attrs,
            "start": [self.textLocation, len(self.text[self.textLocation])],
        }
        for child in tag.children:
            self.process(child)
        obj["end"] = [self.textLocation, len(self.text[self.textLocation]) - 1]
        if tag.name in new_line_tags:
            if len(self.text[self.textLocation]) > 0:
                self.textLocation += 1
                self.text.append("")
        self.data.append(obj)

    def process_string(self, string):
        if string == "\n":
            return
        fixed_str = self.fix_string(string)
        self.text[self.textLocation] += fixed_str

    def fix_string(self, string):
        string = string.replace("\r\n", " ")
        string = string.replace("\n", " ")
        # TODO maybe easier?
        while "  " in string:
            string = string.replace("  ", " ")
        if (
            self.text[self.textLocation]
            and self.text[self.textLocation][-1] == " "
            and string[0] == " "
        ):
            string = string[1:]
        return string

    def find_first_tag(self, expected_tag):
        for tag in self.data:
            if tag["tag"] == expected_tag:
                return tag
        return {"tag": None}