from django import template

register = template.Library()


@register.filter
def get_total_amount_for_date(summary, date):
    return sum(data['amount'] for data in summary.values() if date in data)


@register.filter
def get_total_count_for_date(summary, date):
    return sum(data['count'] for data in summary.values() if date in data)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_nested_item(dictionary, keys):
    keys = keys.split(',')
    value = dictionary
    for key in keys:
        value = value.get(key)
        if value is None:
            break
    return value
