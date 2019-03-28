def should_skip_pdf_tests():
    try:
        import camelot

        return False
    except ImportError:
        return True
