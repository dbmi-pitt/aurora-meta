import re 

from django import template
register = template.Library()

@register.filter('replace')

def replace ( string, args ): 
    search  = args.split(args[0])[1]
    replace = args.split(args[0])[2]
    return re.sub( search, replace, str(string) )

@register.filter('cut')

def cut(value,arg):
    """Removes all values of arg from the given string"""
    if re.search(arg, str(value)) is None:
        return value
    return str(value).replace(arg, ' ')