def should_skip_pdf_tests():
    try:
        import camelot  # noqa

        return False
    except ImportError:
        return True
