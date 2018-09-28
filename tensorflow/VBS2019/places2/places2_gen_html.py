import os
import search_wordnet


def gen(directory):
    with open("places2.html", "w") as html:
        html.write("<body style=\"font-family:Courier New; font-size:16; width:3000px;\">")
        for cat in os.listdir(directory):
            html.write("<h2>{}</h2>\n".format(cat))
            search_wordnet.search(cat, out=html)

            img_dir = os.path.join(directory, cat)
            html.write("<br>")
            for img in os.listdir(img_dir)[:3]:
                html.write("<img src=\"{}\">\n".format(os.path.abspath(os.path.join(img_dir, img))))
            html.write("<hr>\n")
        html.write("</body>")


if __name__ == "__main__":
    gen("S:/Stahování/places365_standard/val")
