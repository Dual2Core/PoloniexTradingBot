def log(msg, preserve_line=True):
    end = '\n' if preserve_line else ''
    start = '\r'  # '\n' if preserve_line else '\r'
    print(start + str(msg), end=end)
