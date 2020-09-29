import re
from hashlib import md5
from typing import AnyStr, Dict

HC_PREFIX = 'HC:'
RULE_PREFIX = 'Rule:'


class Parser:
    PARENTHESES_RE = re.compile(r'\([^(]+?\)')

    def __init__(self):
        self._parentheses_exp = {}

    @staticmethod
    def _split(exp: AnyStr, delimiter: AnyStr):
        return [p.strip() for p in exp.split(delimiter)]

    def _gen_operand(self, exp: AnyStr):
        if exp in self._parentheses_exp:
            return self._parentheses_exp[exp]
        if exp.startswith(HC_PREFIX):
            return {
                'healthcheck_id': exp[len(HC_PREFIX):],
            }
        if exp.startswith(RULE_PREFIX):
            return {
                'rule_id': exp[len(RULE_PREFIX):],
            }
        else:
            return exp

    def _proc_end_value(self, exp: AnyStr) -> Dict:
        """ Генерация конечного значения. Проверка на NOT - если он есть, то
        это оператор с одним операндом, если нет - то значение.
        >>> Parser()._proc_end_value('NOT 1')
        {'operator': 'NOT', 'operands': ['1']}
        >>> Parser()._proc_end_value('HC:1')
        {'healthcheck_id': '1'}
        >>> Parser()._proc_end_value('Rule:1')
        {'rule_id': '1'}
        >>> Parser()._proc_end_value('1 NOT 2')
        Traceback (most recent call last):
            ...
        ValueError: Unexpected first part value (split by NOT)
        >>> Parser()._proc_end_value('1 NOT 2 NOT 3')
        Traceback (most recent call last):
            ...
        ValueError: Unexpected part count (split by NOT)
        """
        not_parts = self._split(exp, 'NOT ')
        if len(not_parts) > 2:
            raise ValueError('Unexpected part count (split by NOT)')
        elif len(not_parts) == 2:
            if not_parts[0] != '':
                raise ValueError('Unexpected first part value (split by NOT)')
            return {
                'operator': 'NOT',
                'operands': [
                    self._gen_operand(not_parts[1])
                ]
            }
        elif len(not_parts) == 1:
            return self._gen_operand(exp)
        else:
            raise ValueError('Unexpected count of split by NOT')

    def _proc_xor(self, exp: AnyStr) -> Dict:
        """ Обработка логического XOR. Если при порезке получилась только
        одна часть - значит XOR не найдено, переходим к получению значения или
        его отрицания (оператор NOT).
        >>> Parser()._proc_and('1 XOR 2')
        {'operator': 'XOR', 'operands': ['1', '2']}
        """
        xor_parts = self._split(exp, ' XOR ')
        if len(xor_parts) > 1:
            return {
                'operator': 'XOR',
                'operands': [
                    self._proc_end_value(xor_part)
                    for xor_part in xor_parts
                ]
            }
        else:
            return self._proc_end_value(xor_parts[0])

    def _proc_and(self, exp: AnyStr) -> Dict:
        """ Обработка логического AND. Если при порезке получилась только
        одна часть - значит AND не найдено, переходим к следующему по иерархии
        XOR.
        >>> Parser()._proc_and('1 AND 2')
        {'operator': 'AND', 'operands': ['1', '2']}
        """
        and_parts = self._split(exp, ' AND ')
        if len(and_parts) > 1:
            return {
                'operator': 'AND',
                'operands': [
                    self._proc_xor(and_part)
                    for and_part in and_parts
                ]
            }
        else:
            return self._proc_xor(and_parts[0])

    def _proc_exp(self, exp: AnyStr) -> Dict:
        """ Обработка логического выражения. На верхнем уровне по иерархии - OR,
        поэтому начинаем резать текст по нему. Если при порезке получилась только
        одна часть - значит OR не найдено, переходим к следующему по иерархии AND.
        >>> Parser()._proc_exp('1 OR 2')
        {'operator': 'OR', 'operands': ['1', '2']}
        """
        or_parts = self._split(exp, ' OR ')
        if len(or_parts) > 1:
            return {
                'operator': 'OR',
                'operands': [
                    self._proc_and(or_part)
                    for or_part in or_parts
                ]
            }
        else:
            return self._proc_and(or_parts[0])

    def _extract_parentheses(self, text: AnyStr):
        """ Извлечение парных скобок, начиная с самых глубоко вложенных.
        Скобочные выражения превращаются в структуры, а их места в тексте
        заменяются на ключи в словаре, где хранятся структуры.
        """
        # Скобочных выражений в тексте нет
        if '(' not in text:
            return text

        # Найти в тексте самое вложенное скобочное выражение, заменить его на ключ
        # сгенерированной из него структуры
        for i in re.findall(self.PARENTHESES_RE, text):
            exp = i[1:-1]  # Отрезаем скобки
            key = 'KEY.{}'.format(md5(exp.encode()).hexdigest())
            self._parentheses_exp[key] = self._proc_exp(exp)
            return self._extract_parentheses(text.replace(i, key))

    def parse(self, exp):
        """ Разбор логического выражения с учетом скобок, и генерация структуры.
        >>> Parser().parse('(1 OR 2) AND NOT 3 XOR 4')
        {'operator': 'AND', 'operands': [{'operator': 'OR', 'operands': ['1', '2']}, {'operator': 'XOR', 'operands': [{'operator': 'NOT', 'operands': ['3']}, '4']}]}
        >>> Parser().parse('1 OR 2 AND NOT 3 XOR 4')
        {'operator': 'OR', 'operands': ['1', {'operator': 'AND', 'operands': ['2', {'operator': 'XOR', 'operands': [{'operator': 'NOT', 'operands': ['3']}, '4']}]}]}
        """
        self._parentheses_exp.clear()
        exp_without_parentheses = self._extract_parentheses(exp)
        return self._proc_exp(exp_without_parentheses)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    """ Пример использования:
    exp = 'HC:1 OR (Rule:2 AND (HC:3 OR Rule:4) AND HC:10) AND (HC:1 AND Rule:2 OR HC:3 OR HC:4 XOR NOT HC:5)'
    print(Parser().parse(exp))
    """
