# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    from werkzeug.security import check_password_hash

    hash_from_db = "scrypt:32768:8:1$6o90YBzUcNZDhsst$e9ba0584c8a41597e5483bc46eacc762413f07929fa6edaf6dfea4b2447d9edc051137cd5d78b147d15fb47fed857fa712d4d6bd7cc90b8a75b056faab099fe0"

    print(check_password_hash(hash_from_db, "1234"))
    import secrets; print(secrets.token_hex(16))

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
