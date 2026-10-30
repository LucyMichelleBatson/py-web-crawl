import unittest
from crawl import (
    normalize_url,
    get_heading_from_html,
    get_first_paragraph_from_html,
    get_urls_from_html,
    get_images_from_html,
    extract_page_data,
)


class TestCrawl(unittest.TestCase):
    def test_normalize_url(self):
        input_url = "https://www.boot.dev/blog/path"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_trailing_slash(self):
        input_url = "https://www.boot.dev/blog/path/"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_http(self):
        input_url = "http://www.boot.dev/blog/path"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_http_trailing_slash(self):
        input_url = "http://www.boot.dev/blog/path/"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_capitals(self):
        input_url = "https://WWW.Boot.dev/Blog/Path"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_root(self):
        input_url = "https://www.boot.dev/"
        actual = normalize_url(input_url)
        expected = "www.boot.dev"
        self.assertEqual(actual, expected)

    def test_normalize_url_no_path(self):
        input_url = "https://www.boot.dev"
        actual = normalize_url(input_url)
        expected = "www.boot.dev"
        self.assertEqual(actual, expected)

    def test_normalize_url_query_and_fragment(self):
        input_url = "https://www.boot.dev/blog/path?page=2#section"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_basic(self):
        input_body = "<html><body><h1>Test Title</h1></body></html>"
        actual = get_heading_from_html(input_body)
        expected = "Test Title"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_h2_fallback(self):
        input_body = "<html><body><h2>Subtitle</h2></body></html>"
        actual = get_heading_from_html(input_body)
        expected = "Subtitle"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_h1_over_h2(self):
        input_body = "<html><body><h2>Second</h2><h1>First</h1></body></html>"
        actual = get_heading_from_html(input_body)
        expected = "First"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_nested_and_whitespace(self):
        input_body = "<html><body><h1>\n  Hello <span>World</span>  \n</h1></body></html>"
        actual = get_heading_from_html(input_body)
        expected = "HelloWorld"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_missing(self):
        input_body = "<html><body><p>No heading here.</p></body></html>"
        actual = get_heading_from_html(input_body)
        expected = ""
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_main_priority(self):
        input_body = """<html><body>
            <p>Outside paragraph.</p>
            <main>
                <p>Main paragraph.</p>
            </main>
        </body></html>"""
        actual = get_first_paragraph_from_html(input_body)
        expected = "Main paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_no_main(self):
        input_body = "<html><body><p>First.</p><p>Second.</p></body></html>"
        actual = get_first_paragraph_from_html(input_body)
        expected = "First."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_main_without_p(self):
        input_body = """<html><body>
            <main><div>No paragraph in main.</div></main>
            <p>Fallback paragraph.</p>
        </body></html>"""
        actual = get_first_paragraph_from_html(input_body)
        expected = "Fallback paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_missing(self):
        input_body = "<html><body><h1>Title only</h1></body></html>"
        actual = get_first_paragraph_from_html(input_body)
        expected = ""
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_absolute(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="https://crawler-test.com"><span>Boot.dev</span></a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_relative(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="/path/one"><span>Boot.dev</span></a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/path/one"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_multiple(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <a href="/path/one">One</a>
            <div><a href="https://other.com/path/two">Two</a></div>
        </body></html>"""
        actual = get_urls_from_html(input_body, input_url)
        expected = [
            "https://crawler-test.com/path/one",
            "https://other.com/path/two",
        ]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_missing_href(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a>No link</a><a href="/ok">OK</a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/ok"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_none(self):
        input_url = "https://crawler-test.com"
        input_body = "<html><body><p>No links here.</p></body></html>"
        actual = get_urls_from_html(input_body, input_url)
        expected = []
        self.assertEqual(actual, expected)

    def test_get_images_from_html_relative(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="/logo.png" alt="Logo"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/logo.png"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_absolute(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="https://cdn.example.com/logo.png"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://cdn.example.com/logo.png"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_multiple(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <img src="/one.png">
            <div><img src="two.jpg"></div>
        </body></html>"""
        actual = get_images_from_html(input_body, input_url)
        expected = [
            "https://crawler-test.com/one.png",
            "https://crawler-test.com/two.jpg",
        ]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_missing_src(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img alt="No src"><img src="/ok.png"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/ok.png"]
        self.assertEqual(actual, expected)

    def test_extract_page_data_basic(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h1>Test Title</h1>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://crawler-test.com/link1"],
            "image_urls": ["https://crawler-test.com/image1.jpg"],
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_main_and_h2(self):
        input_url = "https://crawler-test.com/blog/post"
        input_body = """<html><body>
            <h2>Fallback Heading</h2>
            <p>Sidebar text.</p>
            <main>
                <p>Main content.</p>
                <a href="next">Next</a>
                <a href="https://other.com/page">Other</a>
            </main>
            <img src="pic.png">
            <img alt="no src">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com/blog/post",
            "heading": "Fallback Heading",
            "first_paragraph": "Main content.",
            "outgoing_links": [
                "https://crawler-test.com/blog/next",
                "https://other.com/page",
            ],
            "image_urls": ["https://crawler-test.com/blog/pic.png"],
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_empty(self):
        input_url = "https://crawler-test.com"
        input_body = "<html><body></body></html>"
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "",
            "first_paragraph": "",
            "outgoing_links": [],
            "image_urls": [],
        }
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
