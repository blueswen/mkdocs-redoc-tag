import logging
import os
import uuid
from urllib.parse import unquote as urlunquote
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from markdown.util import AMP_SUBSTITUTE

from mkdocs import utils
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

log = logging.getLogger(__name__)
base_path = os.path.dirname(os.path.abspath(__file__))


class RedocPlugin(BasePlugin):
    """Create Redoc with redoc tag"""

    config_scheme = (
        ("background", config_options.Type(str, default="")),
        ("height", config_options.Type(str, default="80vh")),
        ("dark_scheme_name", config_options.Type(str, default="slate")),
    )

    def on_pre_page(self, page, config, files, **kwargs):
        """Add files for validate redoc tag src"""

        self.files = files
        return page

    def path_to_url(self, page_file, url):
        """Validate redoc tag src and parse url"""

        scheme, netloc, path, query, fragment = urlsplit(url)

        if (
            scheme
            or netloc
            or not path
            or url.startswith("/")
            or url.startswith("\\")
            or AMP_SUBSTITUTE in url
            or "." not in os.path.split(path)[-1]
        ):
            # Ignore URLs unless they are a relative link to a source file.
            # AMP_SUBSTITUTE is used internally by Markdown only for email.
            # No '.' in the last part of a path indicates path does not point to a file.
            return url

        # Determine the filepath of the target.
        target_path = os.path.join(
            os.path.dirname(page_file.src_path), urlunquote(path)
        )
        target_path = os.path.normpath(target_path).lstrip(os.sep)

        # Validate that the target exists in files collection.
        if target_path not in self.files:
            log.warning(
                f"Documentation file '{page_file.src_path}' contains Redoc scr to "
                f"'{target_path}' which is not found in the documentation files."
            )
            return url

        target_file = self.files.get_file_from_path(target_path)
        path = target_file.url_relative_to(page_file)
        components = (scheme, netloc, path, query, fragment)
        return urlunsplit(components)

    def on_post_page(self, output, page, config, **kwargs):
        """Replace redoc tag with iframe
        Add javascript code to update iframe height
        Create a html with Redoc for iframe
        """

        soup = BeautifulSoup(output, "html.parser")
        redoc_list = soup.find_all("redoc")
        iframe_id_list = []

        if len(redoc_list) > 0:
            css_dir = utils.get_relative_url(
                utils.normalize_url("assets/stylesheets/"), page.url
            )
            js_dir = utils.get_relative_url(
                utils.normalize_url("assets/javascripts/"), page.url
            )
            env = Environment(autoescape=True, loader=FileSystemLoader(os.path.join(base_path, "redoc")))
            template = env.get_template("redoc.html")

            page_dir = os.path.dirname(
                os.path.join(config["site_dir"], urlunquote(page.url))
            )
            if not os.path.exists(page_dir):
                os.makedirs(page_dir)

            for redoc_ele in redoc_list:
                cur_id = str(uuid.uuid4())[:8]
                iframe_filename = f"redoc-{cur_id}.html"
                iframe_id_list.append(cur_id)

                openapi_spec_url = self.path_to_url(page.file, redoc_ele.get("src", ""))
                output_from_parsed_template = template.render(
                    css_dir=css_dir,
                    js_dir=js_dir,
                    background=self.config["background"],
                    id=cur_id,
                    openapi_spec_url=openapi_spec_url,
                )
                with open(os.path.join(page_dir, iframe_filename), "w") as f:
                    f.write(output_from_parsed_template)
                self.replace_with_iframe(soup, redoc_ele, cur_id, iframe_filename)

        js_code = soup.new_tag("script")
        js_code.string = ""

        if config["theme"].name == "material":
            # synchronized dark mode with mkdocs-material
            js_code.string += f"""
            const dark_scheme_name = "{self.config['dark_scheme_name']}"
            """
            js_code.string += """
            window.scheme = document.body.getAttribute("data-md-color-scheme")
            const options = {
                attributeFilter: ['data-md-color-scheme'],
            };
            function color_scheme_callback(mutations) {
                for (let mutation of mutations) {
                    if (mutation.attributeName === "data-md-color-scheme") {
                        scheme = document.body.getAttribute("data-md-color-scheme")
                        var iframe_list = document.getElementsByClassName("redoc-iframe")
                        for(var i = 0; i < iframe_list.length; i++) {
                            var ele = iframe_list.item(i);
                            if (ele) {
                                if (scheme === dark_scheme_name) {
                                    ele.contentWindow.enable_dark_mode();
                                } else {
                                    ele.contentWindow.disable_dark_mode();
                                }
                            }
                        }
                    }
                }
            }
            observer = new MutationObserver(color_scheme_callback);
            observer.observe(document.body, options);
            """
            # support compatible with mkdocs-material Instant loading feature
            js_code.string = "document$.subscribe(() => {" + js_code.string + "})"
        soup.body.append(js_code)

        return str(soup)

    def replace_with_iframe(self, soup, redoc_ele, cur_id, iframe_filename):
        """Replace redoc tag with iframe"""
        iframe = soup.new_tag("iframe")
        iframe["id"] = cur_id
        iframe["src"] = iframe_filename
        iframe["frameborder"] = "0"
        iframe["style"] = f"overflow:hidden;width:100%;height:{self.config['height']};"
        iframe["width"] = "100%"
        iframe["class"] = "redoc-iframe"
        redoc_ele.replace_with(iframe)

    def on_post_build(self, config, **kwargs):
        """Copy Redoc css and js files to assets directory"""

        output_base_path = os.path.join(config["site_dir"], "assets")
        css_path = os.path.join(output_base_path, "stylesheets")
        for file_name in os.listdir(os.path.join(base_path, "redoc", "stylesheets")):
            utils.copy_file(
                os.path.join(base_path, "redoc", "stylesheets", file_name),
                os.path.join(css_path, file_name),
            )

        js_path = os.path.join(output_base_path, "javascripts")
        for file_name in os.listdir(os.path.join(base_path, "redoc", "javascripts")):
            utils.copy_file(
                os.path.join(base_path, "redoc", "javascripts", file_name),
                os.path.join(js_path, file_name),
            )

        for file_name in os.listdir(os.path.join(base_path, "redoc", "javascripts")):
            utils.copy_file(
                os.path.join(base_path, "redoc", "javascripts", file_name),
                os.path.join(js_path, file_name),
            )
