import re
import string


def absolute_price(price):
    """
    Input/Output are strings
    129.99 -> 12999
    """
    return str(int(float(price) * 100.0))


def relative_price(price):
    """
    Input/Output are strings
    123 -> 1.23
    """
    if is_integer_string(price):
        return two_digit_string(int(price) / 100.0)


def two_digit_string(value):
    if type(value) == str or type(value) == unicode:
        value = float(value)
    return '{0:.2f}'.format(value)


def is_integer_string(input_string):
    return (isinstance(input_string, basestring)
            and input_string.isdigit())


def matches_reg_ex(input_string, reg_ex):
    """
    Checks if input_string is string or unicode object
    and if it matches the regular expression.
    Empty strings return False.
    """
    return (isinstance(input_string, basestring)
            and re.match(reg_ex, input_string) != None)


def validate_content(content):
    # to clean the message we need to remove ' and "
    content = content.replace("'", "")
    content = content.replace('"', '')
    content = content.replace(';', '')
    content = content.replace('(', '')
    content = content.replace(')', '')
    # remove white space
    content = content.strip()
    # make lower case
    content = content.lower()
    content = convert_special_characters(content)
    return content


def convert_special_characters(input_string):
    input_string = string.replace(input_string, '"', '_')
    input_string = string.replace(input_string, "'", "_")
    input_string = string.replace(input_string, '#', '_')
    input_string = string.replace(input_string, '<', '_')
    input_string = string.replace(input_string, '>', '_')
    input_string = string.replace(input_string, '\t', '_')
    input_string = string.replace(input_string, '\n', '_')
    input_string = string.replace(input_string, '/', '_')
    input_string = string.replace(input_string, '\\', '_')
    return input_string


def add_country_code(number, code):
    if number[0] == '0':
        return code + number[1:]
    else:
        return code + number


def strip_number_str(number, code):
    number = number.replace(' ', '')
    # +44777xxxxxxx cases
    if number[0] == '+':
        return number[1:]
    # 0044777xxxxxxx cases
    if number[:2] == '00':
        return number[2:]
    # 0777xxxxxxx cases
    if number[0] == '0':
        return add_country_code(number, code)
    # 777xxxxxxx cases
    if number[0] == '7':  # valid for UK numbers, fix for international numbers
        return add_country_code(number, code)
    return number


def validate_number(number, code='44'):
    if type(number) == int:
        number = str(number)
    return strip_number_str(number, code)
