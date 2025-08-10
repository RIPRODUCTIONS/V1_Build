from tools.web_research.normalize import normalize_text


def test_normalize_html_basic_dedup_and_ids():
    html = b"""
    <html><head><title>Example Page</title></head>
    <body>
      <script>var a=1;</script>
      <nav>Menu</nav>
      <h1>Heading</h1>
      <p>Paragraph one.</p>
      <p>Paragraph one.</p>
      <p>Paragraph two.</p>
    </body></html>
    """
    res = normalize_text("https://example.com/page#frag", "text/html", html)
    assert res.title == "Example Page"
    assert res.canonical_url.endswith("/page")
    assert res.word_count > 0
    ids = [b.id for b in res.blocks]
    assert ids[0] == "p1"
    # dedup removed duplicate paragraph
    texts = [b.text for b in res.blocks]
    assert texts.count("Paragraph one.") == 1


def test_normalize_text_plain():
    txt = b"First para.\n\nSecond para."
    res = normalize_text("https://example.com/t.txt", "text/plain", txt)
    assert len(res.blocks) >= 2
    assert res.blocks[0].id == "p1"
