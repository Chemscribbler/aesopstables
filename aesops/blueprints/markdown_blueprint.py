from flask import Blueprint, render_template
import markdown


markdown_blueprint = Blueprint('markdown', __name__)


@markdown_blueprint.route("/about", methods=["GET"])
def about():
    with open("documentation/about.md", "r") as f:
        text = f.read()
        html = markdown.markdown(text)
    return render_template(
        "markdown_page.html", markdown_content=markdown.markdown(html)
    )


@markdown_blueprint.route("/howto", methods=["GET"])
def howto():
    with open("documentation/howto.md", "r") as f:
        text = f.read()
        html = markdown.markdown(text, extensions=["tables"])
    return render_template(
        "markdown_page.html", markdown_content=markdown.markdown(html)
    )
