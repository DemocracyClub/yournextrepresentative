def should_skip_pdf_tests():
    try:
        pass

        return False
    except ImportError:
        return True
