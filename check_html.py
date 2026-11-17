"""Простая проверка HTML перед публикацией сайта (линтинг).
Ищет грубые ошибки: нет DOCTYPE, нет <title>, не закрыты основные теги,
повторяются id. При ошибках завершается с кодом 1, и тогда workflow
останавливается, а сайт не публикуется."""
import glob
import sys
from html.parser import HTMLParser

PAIRED = {"html", "head", "body", "header", "nav", "main", "section",
          "footer", "div", "form", "ul", "ol", "table", "script",
          "style", "a", "button"}


class Checker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.ids = [], set()
        self.errors, self.warnings = [], []
        self.title, self.in_title = "", False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        line = self.getpos()[0]
        if tag in PAIRED:
            self.stack.append((tag, line))
        if tag == "title":
            self.in_title = True
        if "id" in d:
            if d["id"] in self.ids:
                self.errors.append(f"строка {line}: повторяется id=\"{d['id']}\"")
            self.ids.add(d["id"])
        if tag == "img" and not d.get("alt"):
            self.warnings.append(f"строка {line}: у <img> нет атрибута alt")

    def handle_endtag(self, tag):
        line = self.getpos()[0]
        if tag == "title":
            self.in_title = False
        if tag in PAIRED:
            if not self.stack:
                self.errors.append(f"строка {line}: лишний </{tag}>")
            elif self.stack[-1][0] == tag:
                self.stack.pop()
            else:
                self.errors.append(
                    f"строка {line}: ожидался </{self.stack[-1][0]}>, найден </{tag}>")
                for i in range(len(self.stack) - 1, -1, -1):
                    if self.stack[i][0] == tag:
                        del self.stack[i:]
                        break

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def check_file(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    c = Checker()
    errors = []
    if not text.lstrip().lower().startswith("<!doctype html"):
        errors.append("страница не начинается с <!DOCTYPE html>")
    c.feed(text)
    c.close()
    if not c.title.strip():
        errors.append("нет непустого тега <title>")
    for tag, line in c.stack:
        errors.append(f"строка {line}: тег <{tag}> не закрыт")
    errors += c.errors
    return errors, c.warnings


def main():
    files = sorted(glob.glob("**/*.html", recursive=True))
    failed = False
    for path in files:
        errors, warnings = check_file(path)
        if errors:
            failed = True
            print(f"[ОШИБКА] {path}")
            for e in errors:
                print("   ", e)
        else:
            print(f"[OK] {path}")
        for w in warnings:
            print(f"   [предупреждение] {w}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
