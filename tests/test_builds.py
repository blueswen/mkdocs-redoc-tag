# standard lib
import logging
import os
import re
import shutil

# other 3rd party
from bs4 import BeautifulSoup
from click.testing import CliRunner

# MkDocs
from mkdocs.__main__ import build_command

# ##################################
# ######## Globals #################
# ##################################

# custom log level to get plugin info messages
logging.basicConfig(level=logging.INFO)

# ##################################
# ########## Helpers ###############
# ##################################


def setup_clean_mkdocs_folder(
    mkdocs_yml_path: str, output_path: str, docs_path: str = "tests/fixtures/docs"
):
    """
    Sets up a clean mkdocs directory
    outputpath/testproject
    ├── docs/
    └── mkdocs.yml
    Args:
        mkdocs_yml_path (Path): Path of mkdocs.yml file to use
        output_path (Path): Path of folder in which to create mkdocs project
    Returns:
        testproject_path (Path): Path to test project
    """

    testproject_path = output_path / "testproject"

    # Create empty 'testproject' folder
    if os.path.exists(str(testproject_path)):
        logging.warning(
            """This command does not work on windows.
        Refactor your test to use setup_clean_mkdocs_folder() only once"""
        )
        shutil.rmtree(str(testproject_path))

    # Copy correct mkdocs.yml file and our test 'docs/'
    shutil.copytree(docs_path, str(testproject_path / docs_path.split("/")[-1]))

    shutil.copyfile(mkdocs_yml_path, str(testproject_path / "mkdocs.yml"))

    return testproject_path


def build_docs_setup(testproject_path: str):
    """
    Runs the `mkdocs build` command
    Args:
        testproject_path (Path): Path to test project
    Returns:
        command: Object with results of command
    """

    # TODO: Try specifying path in CliRunner, this function could be one-liner
    cwd = os.getcwd()
    os.chdir(str(testproject_path))

    try:
        runner = CliRunner()
        run = runner.invoke(build_command)
        os.chdir(cwd)
        return run
    except:
        os.chdir(cwd)
        raise


def validate_build(testproject_path: str, plugin_config: dict = {}):
    """
    Validates a build from a testproject
    Args:
        testproject_path (Path): Path to test project
    """
    assert os.path.exists(str(testproject_path / "site"))

    # Make sure index file exists
    index_file = testproject_path / "site/index.html"
    assert index_file.exists(), "%s does not exist" % index_file


def validate_mkdocs_file(
    temp_path: str, mkdocs_yml_file: str, docs_path: str = "tests/fixtures/docs"
):
    """
    Creates a clean mkdocs project
    for a mkdocs YML file, builds and validates it.
    Args:
        temp_path (PosixPath): Path to temporary folder
        mkdocs_yml_file (PosixPath): Path to mkdocs.yml file
    """
    testproject_path = setup_clean_mkdocs_folder(
        mkdocs_yml_path=mkdocs_yml_file, output_path=temp_path, docs_path=docs_path
    )
    result = build_docs_setup(
        testproject_path,
    )
    assert result.exit_code == 0, "'mkdocs build' command failed"

    # validate build with locale retrieved from mkdocs config file
    validate_build(testproject_path)

    return testproject_path


def validate_static(html_content: str, path: str = "", exist: bool = True):
    """
    Validate redoc files have been loaded or not
    """
    assert exist == (
        re.search(
            rf'<script src="{path}assets\/javascripts\/redoc\.standalone\.js"><\/script>',
            html_content,
        )
        is not None
    )
    assert exist == (
        re.search(
            rf'<script src="{path}assets\/javascripts\/redark\.js"><\/script>',
            html_content,
        )
        is not None
    )
    assert exist == (
        re.search(
            rf'<link href="{path}assets\/stylesheets\/redark\.css" rel="stylesheet"\/>',
            html_content,
        )
        is not None
    )


def validate_iframe(html_content, iframe_src_dir):
    """
    Validate target iframe html exist
    """
    iframe_content_list = []
    # <iframe class="redoc-iframe" frameborder="0" id="767c835c" src="redoc-767c835c.html" style="overflow: hidden; width: 100%; height: 80vh;" width="100%"></iframe>
    iframe_list = re.findall(
        r'<iframe class="redoc-iframe" .*><\/iframe>',
        html_content,
    )
    iframe_id_list = []
    validate_additional_script_code(html_content)
    for iframe in iframe_list:
        iframe_tag = BeautifulSoup(iframe, "html.parser").iframe
        iframe_id = iframe_tag.attrs.get("id")
        iframe_src = iframe_tag.attrs.get("src")
        assert iframe_id is not None
        assert iframe_src is not None
        assert f"redoc-{iframe_id}.html" == iframe_src
        iframe_file = iframe_src_dir / iframe_src
        assert iframe_file.exists()
        iframe_content = iframe_file.read_text(encoding="utf8")
        iframe_content_list.append(iframe_content)
        iframe_id_list.append(iframe_id)

    return iframe_content_list


def validate_additional_script_code(html_content, exists=True):
    pass


def validate_additional_script_code_for_material(html_content, exists=True):
    assert exists == (
        'window.scheme = document.body.getAttribute("data-md-color-scheme")'
        in html_content
    )
    assert exists == (
        """document$.subscribe(() => {
            const dark_scheme_name = """
        in html_content
    )


# ##################################
# ########### Tests ################
# ##################################


def test_basic(tmp_path):
    """
    Minimal sample
    """
    mkdocs_file = "mkdocs.yml"
    testproject_path = validate_mkdocs_file(tmp_path, f"tests/fixtures/{mkdocs_file}")
    file = testproject_path / "site/index.html"
    contents = file.read_text(encoding="utf8")
    validate_additional_script_code_for_material(contents, exists=False)

    iframe_content_list = validate_iframe(contents, file.parent)
    assert len(iframe_content_list) == 1
    iframe_contents = iframe_content_list[0]

    # validate OpenAPI spec exist
    regex_obj = re.search(
        r"const openapi_spec_url = \"(.*)\";",
        iframe_contents,
    )
    assert regex_obj
    openapi_spec_url = regex_obj.group(1)
    assert (file.parent / openapi_spec_url).resolve().exists()


def test_basic_sub_dir(tmp_path):
    """
    Minimal sample
    """
    mkdocs_file = "mkdocs.yml"
    testproject_path = validate_mkdocs_file(tmp_path, f"tests/fixtures/{mkdocs_file}")
    file = testproject_path / "site/sub_dir/page_in_sub_dir/index.html"
    contents = file.read_text(encoding="utf8")

    iframe_content_list = validate_iframe(contents, file.parent)
    assert len(iframe_content_list) == 1
    iframe_contents = iframe_content_list[0]

    # validate OpenAPI spec exists
    regex_obj = re.search(
        r"const openapi_spec_url = \"(.*)\";",
        iframe_contents,
    )
    assert regex_obj
    openapi_spec_url = regex_obj.group(1)
    assert (file.parent / openapi_spec_url).resolve().exists()


def test_use_directory_urls(tmp_path):
    """
    Compatible with use_directory_urls is false or with --use-directory-urls and --use-directory-urls as args
    https://www.mkdocs.org/user-guide/configuration/#use_directory_urls
    https://www.mkdocs.org/user-guide/cli/
    """
    mkdocs_file = "mkdocs-target-file.yml"
    testproject_path = validate_mkdocs_file(tmp_path, f"tests/fixtures/{mkdocs_file}")
    file = testproject_path / "site/index.html"
    contents = file.read_text(encoding="utf8")

    iframe_content_list = validate_iframe(contents, file.parent)
    assert len(iframe_content_list) == 1
    iframe_contents = iframe_content_list[0]

    # validate OpenAPI spec exist
    regex_obj = re.search(
        r"const openapi_spec_url = \"(.*)\";",
        iframe_contents,
    )
    assert regex_obj
    openapi_spec_url = regex_obj.group(1)
    assert (file.parent / openapi_spec_url).resolve().exists()


def test_use_directory_urls_sub_dir(tmp_path):
    """
    Compatible with use_directory_urls is false or with --use-directory-urls and --use-directory-urls as args
    https://www.mkdocs.org/user-guide/configuration/#use_directory_urls
    https://www.mkdocs.org/user-guide/cli/
    """
    mkdocs_file = "mkdocs-target-file.yml"
    testproject_path = validate_mkdocs_file(tmp_path, f"tests/fixtures/{mkdocs_file}")
    file = testproject_path / "site/sub_dir/page_in_sub_dir.html"
    contents = file.read_text(encoding="utf8")

    iframe_content_list = validate_iframe(contents, file.parent)
    assert len(iframe_content_list) == 1
    iframe_contents = iframe_content_list[0]

    # validate OpenAPI spec exist
    regex_obj = re.search(
        r"const openapi_spec_url = \"(.*)\";",
        iframe_contents,
    )
    assert regex_obj
    openapi_spec_url = regex_obj.group(1)
    assert (file.parent / openapi_spec_url).resolve().exists()


def test_material(tmp_path):
    """
    Integrate with Material for MkDocs
    """
    mkdocs_file = "mkdocs-material.yml"
    testproject_path = validate_mkdocs_file(tmp_path, f"tests/fixtures/{mkdocs_file}")
    file = testproject_path / "site/index.html"
    contents = file.read_text(encoding="utf8")
    validate_additional_script_code_for_material(contents, exists=True)
    assert 'const dark_scheme_name = "slate"' in contents

    iframe_content_list = validate_iframe(contents, file.parent)
    assert len(iframe_content_list) == 1
    iframe_contents = iframe_content_list[0]

    # validate OpenAPI spec exist
    regex_obj = re.search(
        r"const openapi_spec_url = \"(.*)\";",
        iframe_contents,
    )
    assert regex_obj
    openapi_spec_url = regex_obj.group(1)
    assert (file.parent / openapi_spec_url).resolve().exists()


def test_material_dark_scheme_name(tmp_path):
    """
    Integrate with Material for MkDocs
    """
    mkdocs_file = "mkdocs-material-options.yml"
    testproject_path = validate_mkdocs_file(tmp_path, f"tests/fixtures/{mkdocs_file}")
    file = testproject_path / "site/index.html"
    contents = file.read_text(encoding="utf8")
    validate_additional_script_code_for_material(contents, exists=True)
    assert 'const dark_scheme_name = "white"' in contents


def test_url(tmp_path):
    """
    Validate online OpenAPI Spec
    """
    mkdocs_file = "mkdocs.yml"
    testproject_path = validate_mkdocs_file(tmp_path, f"tests/fixtures/{mkdocs_file}")
    file = testproject_path / "site/url/index.html"
    contents = file.read_text(encoding="utf8")

    iframe_content_list = validate_iframe(contents, file.parent)
    assert len(iframe_content_list) == 1
    iframe_contents = iframe_content_list[0]

    # validate OpenAPI spec exist
    regex_obj = re.search(
        r"const openapi_spec_url = \"(.*)\";",
        iframe_contents,
    )
    assert regex_obj
    assert regex_obj.group(1) == "https://petstore.swagger.io/v2/swagger.json"


def test_multiple(tmp_path):
    """
    Validate multiple Redoc in the same page
    """
    mkdocs_file = "mkdocs.yml"
    testproject_path = validate_mkdocs_file(tmp_path, f"tests/fixtures/{mkdocs_file}")
    file = testproject_path / "site/multiple/index.html"
    contents = file.read_text(encoding="utf8")

    iframe_content_list = validate_iframe(contents, file.parent)
    assert len(iframe_content_list) == 3
    for ind, iframe_contents in enumerate(iframe_content_list):
        # validate OpenAPI spec exist
        regex_obj = re.search(
            r"const openapi_spec_url = \"(.*)\";",
            iframe_contents,
        )
        assert regex_obj
        if ind == 0 or ind == 1:
            openapi_spec_url = regex_obj.group(1)
            assert (file.parent / openapi_spec_url).resolve().exists()
        elif ind == 2:
            assert regex_obj.group(1) == "https://petstore.swagger.io/v2/swagger.json"


def test_plugin_options(tmp_path):
    mkdocs_file = "mkdocs-options.yml"
    testproject_path = validate_mkdocs_file(tmp_path, f"tests/fixtures/{mkdocs_file}")
    file = testproject_path / "site/index.html"
    contents = file.read_text(encoding="utf8")
    assert "height:100vh;" in contents

    iframe_content_list = validate_iframe(contents, file.parent)
    assert len(iframe_content_list) == 1
    iframe_content = iframe_content_list[0]
    plugin_options = {
        "background": "gray",
    }
    for key, val in plugin_options.items():
        if key == "background":
            assert f"{key}: {val}" in iframe_content


def test_static(tmp_path):
    """
    Validate static files
    """
    mkdocs_file = "mkdocs.yml"
    testproject_path = validate_mkdocs_file(tmp_path, f"tests/fixtures/{mkdocs_file}")
    js_files = ["redoc.standalone.js", "redark.js"]
    for file_name in js_files:
        assert (testproject_path / "site/assets/javascripts/" / file_name).exists()
    css_files = ["redark.css"]
    for file_name in css_files:
        assert (testproject_path / "site/assets/stylesheets/" / file_name).exists()


def test_empty(tmp_path):
    """
    Validate static files
    """
    mkdocs_file = "mkdocs.yml"
    testproject_path = validate_mkdocs_file(tmp_path, f"tests/fixtures/{mkdocs_file}")
    file = testproject_path / "site/empty/index.html"
    contents = file.read_text(encoding="utf8")

    validate_additional_script_code(contents, exists=True)


def test_error(tmp_path):
    mkdocs_file = "mkdocs-error.yml"
    validate_mkdocs_file(
        tmp_path, f"tests/fixtures/{mkdocs_file}", docs_path="tests/fixtures/error_docs"
    )


def test_template(tmp_path):
    mkdocs_file = "mkdocs-material-template.yml"
    testproject_path = validate_mkdocs_file(
        tmp_path,
        f"tests/fixtures/{mkdocs_file}",
        docs_path="tests/fixtures/template_docs",
    )
    file = testproject_path / "site/index.html"
    contents = file.read_text(encoding="utf8")

    iframe_content_list = validate_iframe(contents, file.parent)
    assert len(iframe_content_list) == 2
