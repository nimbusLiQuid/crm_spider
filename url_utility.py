def is_html_content_valid(page_content):
    bad_patterns = ['Error', 'error', '404', '对不起', u'对不起', 'Bad', 'Forbidden', '出错了', '错误']
    for pattern in bad_patterns:
        if pattern in page_content:
            return False
    else:
        return True

