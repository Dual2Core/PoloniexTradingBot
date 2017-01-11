def log(msg, preserve_line=False):
    end = '\n' if preserve_line else ''
    start = '\r'  # '\n' if preserve_line else '\r'
    print(start + str(msg), end=end)

    try:
        with open('log.txt', 'a') as file:
            log_end = '\n\n' if preserve_line else '\n'
            file.write(str(msg) + log_end)
    except PermissionError:
        log(msg, preserve_line)
