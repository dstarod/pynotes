# -*- coding: utf-8 -*-
import copy


class ItemExtractionError(KeyError, IndexError):
    pass


def extract_item(obj, path, exc=True):
    """ Extract element from structure
     >>> extract_item({"a": {"b": [1]}}, 'a')
     {'b': [1]}
     >>> extract_item({"a": {"b": [1]}}, 'a.b')
     [1]
     >>> extract_item({"a": {"b": [1]}}, 'a.b.0')
     1
     >>> extract_item([[True]], '0.0')
     True

    :type obj: dict|list|tuple
    :type path: str
    :type exc: bool
    """
    tmp = copy.copy(obj)
    checked_keys = []

    def incorrect_path():
        if not exc:
            return None
        raise ItemExtractionError(
            "Path '{}' doesn't exists".format('.'.join(checked_keys))
        )

    for path_part in path.split('.'):
        checked_keys.append(path_part)

        if path_part.isdigit():
            seq_index = int(path_part)
            if not type(tmp) in (list, tuple):
                return incorrect_path()
            if seq_index < 0 or seq_index > len(tmp)-1:
                return incorrect_path()
            tmp = tmp[seq_index]
            continue

        if path_part not in tmp:
            return incorrect_path()

        tmp = tmp[path_part]

    return tmp


def ensure_item_exists(obj, path):
    """ Ensure element exists
    >>> ensure_item_exists({'a': {'b': 1}}, 'a.b')
    True
    >>> ensure_item_exists({'a': {'b': [1, 2]}}, 'a.b.2')
    False

    :type obj: dict|list|tuple
    :type path: str
    """
    try:
        extract_item(obj, path, exc=True)
    except ItemExtractionError:
        return False
    return True


if __name__ == '__main__':
    import doctest
    doctest.testmod()
