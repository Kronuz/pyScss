def createParserClass(GrammarBase, ruleGlobals):
    if ruleGlobals is None:
        ruleGlobals = {}
    class Grammar(GrammarBase):
        def rule_escape(self):
            _locals = {'self': self}
            self.locals['escape'] = _locals
            self._trace(" '\\\\'", (439, 444), self.input.position)
            _G_exactly_1, lastError = self.exactly('\\')
            self.considerError(lastError, 'escape')
            def _G_or_2():
                self._trace("\n        '\\n'", (446, 459), self.input.position)
                _G_exactly_3, lastError = self.exactly('\n')
                self.considerError(lastError, None)
                _G_python_4, lastError = (''), None
                self.considerError(lastError, None)
                return (_G_python_4, self.currentError)
            def _G_or_5():
                def _G_consumedby_6():
                    def _G_repeat_7():
                        self._trace('hex', (535, 538), self.input.position)
                        _G_apply_8, lastError = self._apply(self.rule_hex, "hex", [])
                        self.considerError(lastError, None)
                        return (_G_apply_8, self.currentError)
                    _G_repeat_9, lastError = self.repeat(1, 6, _G_repeat_7)
                    self.considerError(lastError, None)
                    return (_G_repeat_9, self.currentError)
                _G_consumedby_10, lastError = self.consumedby(_G_consumedby_6)
                self.considerError(lastError, None)
                _locals['cp'] = _G_consumedby_10
                def _G_optional_11():
                    self._trace(' ws', (547, 550), self.input.position)
                    _G_apply_12, lastError = self._apply(self.rule_ws, "ws", [])
                    self.considerError(lastError, None)
                    return (_G_apply_12, self.currentError)
                def _G_optional_13():
                    return (None, self.input.nullError())
                _G_or_14, lastError = self._or([_G_optional_11, _G_optional_13])
                self.considerError(lastError, None)
                _G_python_16, lastError = eval(self._G_expr_15, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_16, self.currentError)
            def _G_or_17():
                self._trace(' anything', (691, 700), self.input.position)
                _G_apply_18, lastError = self._apply(self.rule_anything, "anything", [])
                self.considerError(lastError, None)
                return (_G_apply_18, self.currentError)
            _G_or_19, lastError = self._or([_G_or_2, _G_or_5, _G_or_17])
            self.considerError(lastError, 'escape')
            return (_G_or_19, self.currentError)


        def rule_identifier(self):
            _locals = {'self': self}
            self.locals['identifier'] = _locals
            def _G_consumedby_20():
                self._trace(' letterish', (732, 742), self.input.position)
                _G_apply_21, lastError = self._apply(self.rule_letterish, "letterish", [])
                self.considerError(lastError, None)
                def _G_many_22():
                    def _G_or_23():
                        self._trace('letterish', (744, 753), self.input.position)
                        _G_apply_24, lastError = self._apply(self.rule_letterish, "letterish", [])
                        self.considerError(lastError, None)
                        return (_G_apply_24, self.currentError)
                    def _G_or_25():
                        self._trace(' digit', (755, 761), self.input.position)
                        _G_apply_26, lastError = self._apply(self.rule_digit, "digit", [])
                        self.considerError(lastError, None)
                        return (_G_apply_26, self.currentError)
                    _G_or_27, lastError = self._or([_G_or_23, _G_or_25])
                    self.considerError(lastError, None)
                    return (_G_or_27, self.currentError)
                _G_many_28, lastError = self.many(_G_many_22)
                self.considerError(lastError, None)
                return (_G_many_28, self.currentError)
            _G_consumedby_29, lastError = self.consumedby(_G_consumedby_20)
            self.considerError(lastError, 'identifier')
            return (_G_consumedby_29, self.currentError)


        def rule_number(self):
            _locals = {'self': self}
            self.locals['number'] = _locals
            def _G_consumedby_30():
                def _G_or_31():
                    def _G_many1_32():
                        self._trace(' digit', (776, 782), self.input.position)
                        _G_apply_33, lastError = self._apply(self.rule_digit, "digit", [])
                        self.considerError(lastError, None)
                        return (_G_apply_33, self.currentError)
                    _G_many1_34, lastError = self.many(_G_many1_32, _G_many1_32())
                    self.considerError(lastError, None)
                    def _G_optional_35():
                        self._trace("'.'", (785, 788), self.input.position)
                        _G_exactly_36, lastError = self.exactly('.')
                        self.considerError(lastError, None)
                        def _G_many_37():
                            self._trace(' digit', (788, 794), self.input.position)
                            _G_apply_38, lastError = self._apply(self.rule_digit, "digit", [])
                            self.considerError(lastError, None)
                            return (_G_apply_38, self.currentError)
                        _G_many_39, lastError = self.many(_G_many_37)
                        self.considerError(lastError, None)
                        return (_G_many_39, self.currentError)
                    def _G_optional_40():
                        return (None, self.input.nullError())
                    _G_or_41, lastError = self._or([_G_optional_35, _G_optional_40])
                    self.considerError(lastError, None)
                    return (_G_or_41, self.currentError)
                def _G_or_42():
                    self._trace(" '.'", (799, 803), self.input.position)
                    _G_exactly_43, lastError = self.exactly('.')
                    self.considerError(lastError, None)
                    def _G_many1_44():
                        self._trace(' digit', (803, 809), self.input.position)
                        _G_apply_45, lastError = self._apply(self.rule_digit, "digit", [])
                        self.considerError(lastError, None)
                        return (_G_apply_45, self.currentError)
                    _G_many1_46, lastError = self.many(_G_many1_44, _G_many1_44())
                    self.considerError(lastError, None)
                    return (_G_many1_46, self.currentError)
                _G_or_47, lastError = self._or([_G_or_31, _G_or_42])
                self.considerError(lastError, None)
                return (_G_or_47, self.currentError)
            _G_consumedby_48, lastError = self.consumedby(_G_consumedby_30)
            self.considerError(lastError, 'number')
            return (_G_consumedby_48, self.currentError)


        def rule_variable(self):
            _locals = {'self': self}
            self.locals['variable'] = _locals
            def _G_consumedby_49():
                self._trace(" '$'", (825, 829), self.input.position)
                _G_exactly_50, lastError = self.exactly('$')
                self.considerError(lastError, None)
                self._trace(' identifier', (829, 840), self.input.position)
                _G_apply_51, lastError = self._apply(self.rule_identifier, "identifier", [])
                self.considerError(lastError, None)
                return (_G_apply_51, self.currentError)
            _G_consumedby_52, lastError = self.consumedby(_G_consumedby_49)
            self.considerError(lastError, 'variable')
            return (_G_consumedby_52, self.currentError)


        def rule_expression(self):
            _locals = {'self': self}
            self.locals['expression'] = _locals
            self._trace(' comma_list', (870, 881), self.input.position)
            _G_apply_53, lastError = self._apply(self.rule_comma_list, "comma_list", [])
            self.considerError(lastError, 'expression')
            return (_G_apply_53, self.currentError)


        def rule_comma_list(self):
            _locals = {'self': self}
            self.locals['comma_list'] = _locals
            self._trace(' spaced_list', (895, 907), self.input.position)
            _G_apply_54, lastError = self._apply(self.rule_spaced_list, "spaced_list", [])
            self.considerError(lastError, 'comma_list')
            _locals['head'] = _G_apply_54
            def _G_many_55():
                self._trace('\n        ows', (914, 926), self.input.position)
                _G_apply_56, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                self._trace(" ','", (926, 930), self.input.position)
                _G_exactly_57, lastError = self.exactly(',')
                self.considerError(lastError, None)
                self._trace(' ows', (930, 934), self.input.position)
                _G_apply_58, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                self._trace('\n        spaced_list', (934, 954), self.input.position)
                _G_apply_59, lastError = self._apply(self.rule_spaced_list, "spaced_list", [])
                self.considerError(lastError, None)
                _locals['tail'] = _G_apply_59
                _G_python_61, lastError = eval(self._G_expr_60, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_61, self.currentError)
            _G_many_62, lastError = self.many(_G_many_55)
            self.considerError(lastError, 'comma_list')
            _locals['tails'] = _G_many_62
            _G_python_64, lastError = eval(self._G_expr_63, self.globals, _locals), None
            self.considerError(lastError, 'comma_list')
            return (_G_python_64, self.currentError)


        def rule_spaced_list(self):
            _locals = {'self': self}
            self.locals['spaced_list'] = _locals
            self._trace(' single_expression', (1045, 1063), self.input.position)
            _G_apply_65, lastError = self._apply(self.rule_single_expression, "single_expression", [])
            self.considerError(lastError, 'spaced_list')
            _locals['head'] = _G_apply_65
            def _G_many_66():
                self._trace('\n        ws', (1070, 1081), self.input.position)
                _G_apply_67, lastError = self._apply(self.rule_ws, "ws", [])
                self.considerError(lastError, None)
                self._trace('\n        single_expression', (1081, 1107), self.input.position)
                _G_apply_68, lastError = self._apply(self.rule_single_expression, "single_expression", [])
                self.considerError(lastError, None)
                _locals['tail'] = _G_apply_68
                _G_python_69, lastError = eval(self._G_expr_60, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_69, self.currentError)
            _G_many_70, lastError = self.many(_G_many_66)
            self.considerError(lastError, 'spaced_list')
            _locals['tails'] = _G_many_70
            _G_python_72, lastError = eval(self._G_expr_71, self.globals, _locals), None
            self.considerError(lastError, 'spaced_list')
            return (_G_python_72, self.currentError)


        def rule_single_expression(self):
            _locals = {'self': self}
            self.locals['single_expression'] = _locals
            self._trace(' or_test', (1218, 1226), self.input.position)
            _G_apply_73, lastError = self._apply(self.rule_or_test, "or_test", [])
            self.considerError(lastError, 'single_expression')
            return (_G_apply_73, self.currentError)


        def rule_or_test(self):
            _locals = {'self': self}
            self.locals['or_test'] = _locals
            self._trace(' and_test', (1237, 1246), self.input.position)
            _G_apply_74, lastError = self._apply(self.rule_and_test, "and_test", [])
            self.considerError(lastError, 'or_test')
            _locals['head'] = _G_apply_74
            def _G_many_75():
                self._trace("\n        'o'", (1253, 1265), self.input.position)
                _G_exactly_76, lastError = self.exactly('o')
                self.considerError(lastError, None)
                self._trace(" 'r'", (1265, 1269), self.input.position)
                _G_exactly_77, lastError = self.exactly('r')
                self.considerError(lastError, None)
                self._trace('\n        and_test', (1269, 1286), self.input.position)
                _G_apply_78, lastError = self._apply(self.rule_and_test, "and_test", [])
                self.considerError(lastError, None)
                _locals['tail'] = _G_apply_78
                _G_python_79, lastError = eval(self._G_expr_60, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_79, self.currentError)
            _G_many_80, lastError = self.many(_G_many_75)
            self.considerError(lastError, 'or_test')
            _locals['tails'] = _G_many_80
            _G_python_82, lastError = eval(self._G_expr_81, self.globals, _locals), None
            self.considerError(lastError, 'or_test')
            return (_G_python_82, self.currentError)


        def rule_and_test(self):
            _locals = {'self': self}
            self.locals['and_test'] = _locals
            self._trace(' not_test', (1369, 1378), self.input.position)
            _G_apply_83, lastError = self._apply(self.rule_not_test, "not_test", [])
            self.considerError(lastError, 'and_test')
            _locals['head'] = _G_apply_83
            def _G_many_84():
                self._trace("\n        'a'", (1385, 1397), self.input.position)
                _G_exactly_85, lastError = self.exactly('a')
                self.considerError(lastError, None)
                self._trace(" 'n'", (1397, 1401), self.input.position)
                _G_exactly_86, lastError = self.exactly('n')
                self.considerError(lastError, None)
                self._trace(" 'd'", (1401, 1405), self.input.position)
                _G_exactly_87, lastError = self.exactly('d')
                self.considerError(lastError, None)
                self._trace('\n        not_test', (1405, 1422), self.input.position)
                _G_apply_88, lastError = self._apply(self.rule_not_test, "not_test", [])
                self.considerError(lastError, None)
                _locals['tail'] = _G_apply_88
                _G_python_89, lastError = eval(self._G_expr_60, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_89, self.currentError)
            _G_many_90, lastError = self.many(_G_many_84)
            self.considerError(lastError, 'and_test')
            _locals['tails'] = _G_many_90
            _G_python_92, lastError = eval(self._G_expr_91, self.globals, _locals), None
            self.considerError(lastError, 'and_test')
            return (_G_python_92, self.currentError)


        def rule_not_test(self):
            _locals = {'self': self}
            self.locals['not_test'] = _locals
            def _G_or_93():
                self._trace(' comparison', (1505, 1516), self.input.position)
                _G_apply_94, lastError = self._apply(self.rule_comparison, "comparison", [])
                self.considerError(lastError, None)
                return (_G_apply_94, self.currentError)
            def _G_or_95():
                self._trace(" 'n'", (1520, 1524), self.input.position)
                _G_exactly_96, lastError = self.exactly('n')
                self.considerError(lastError, None)
                self._trace(" 'o'", (1524, 1528), self.input.position)
                _G_exactly_97, lastError = self.exactly('o')
                self.considerError(lastError, None)
                self._trace(" 't'", (1528, 1532), self.input.position)
                _G_exactly_98, lastError = self.exactly('t')
                self.considerError(lastError, None)
                self._trace(' not_test', (1532, 1541), self.input.position)
                _G_apply_99, lastError = self._apply(self.rule_not_test, "not_test", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_99
                _G_python_101, lastError = eval(self._G_expr_100, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_101, self.currentError)
            _G_or_102, lastError = self._or([_G_or_93, _G_or_95])
            self.considerError(lastError, 'not_test')
            return (_G_or_102, self.currentError)


        def rule_comparison(self):
            _locals = {'self': self}
            self.locals['comparison'] = _locals
            self._trace(' add_expr', (1577, 1586), self.input.position)
            _G_apply_103, lastError = self._apply(self.rule_add_expr, "add_expr", [])
            self.considerError(lastError, 'comparison')
            _locals['node'] = _G_apply_103
            def _G_many_104():
                def _G_or_105():
                    self._trace('\n        ows', (1593, 1605), self.input.position)
                    _G_apply_106, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '<'", (1605, 1609), self.input.position)
                    _G_exactly_107, lastError = self.exactly('<')
                    self.considerError(lastError, None)
                    self._trace(' ows', (1609, 1613), self.input.position)
                    _G_apply_108, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (1613, 1622), self.input.position)
                    _G_apply_109, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_109
                    _G_python_111, lastError = eval(self._G_expr_110, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_111
                    return (_G_python_111, self.currentError)
                def _G_or_112():
                    self._trace(' ows', (1687, 1691), self.input.position)
                    _G_apply_113, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '>'", (1691, 1695), self.input.position)
                    _G_exactly_114, lastError = self.exactly('>')
                    self.considerError(lastError, None)
                    self._trace(' ows', (1695, 1699), self.input.position)
                    _G_apply_115, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (1699, 1708), self.input.position)
                    _G_apply_116, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_116
                    _G_python_118, lastError = eval(self._G_expr_117, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_118
                    return (_G_python_118, self.currentError)
                def _G_or_119():
                    self._trace(' ows', (1773, 1777), self.input.position)
                    _G_apply_120, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '<'", (1777, 1781), self.input.position)
                    _G_exactly_121, lastError = self.exactly('<')
                    self.considerError(lastError, None)
                    self._trace(" '='", (1781, 1785), self.input.position)
                    _G_exactly_122, lastError = self.exactly('=')
                    self.considerError(lastError, None)
                    self._trace(' ows', (1785, 1789), self.input.position)
                    _G_apply_123, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (1789, 1798), self.input.position)
                    _G_apply_124, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_124
                    _G_python_126, lastError = eval(self._G_expr_125, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_126
                    return (_G_python_126, self.currentError)
                def _G_or_127():
                    self._trace(' ows', (1863, 1867), self.input.position)
                    _G_apply_128, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '>'", (1867, 1871), self.input.position)
                    _G_exactly_129, lastError = self.exactly('>')
                    self.considerError(lastError, None)
                    self._trace(" '='", (1871, 1875), self.input.position)
                    _G_exactly_130, lastError = self.exactly('=')
                    self.considerError(lastError, None)
                    self._trace(' ows', (1875, 1879), self.input.position)
                    _G_apply_131, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (1879, 1888), self.input.position)
                    _G_apply_132, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_132
                    _G_python_134, lastError = eval(self._G_expr_133, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_134
                    return (_G_python_134, self.currentError)
                def _G_or_135():
                    self._trace(' ows', (1953, 1957), self.input.position)
                    _G_apply_136, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '='", (1957, 1961), self.input.position)
                    _G_exactly_137, lastError = self.exactly('=')
                    self.considerError(lastError, None)
                    self._trace(" '='", (1961, 1965), self.input.position)
                    _G_exactly_138, lastError = self.exactly('=')
                    self.considerError(lastError, None)
                    self._trace(' ows', (1965, 1969), self.input.position)
                    _G_apply_139, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (1969, 1978), self.input.position)
                    _G_apply_140, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_140
                    _G_python_142, lastError = eval(self._G_expr_141, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_142
                    return (_G_python_142, self.currentError)
                def _G_or_143():
                    self._trace(' ows', (2043, 2047), self.input.position)
                    _G_apply_144, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '!'", (2047, 2051), self.input.position)
                    _G_exactly_145, lastError = self.exactly('!')
                    self.considerError(lastError, None)
                    self._trace(" '='", (2051, 2055), self.input.position)
                    _G_exactly_146, lastError = self.exactly('=')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2055, 2059), self.input.position)
                    _G_apply_147, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (2059, 2068), self.input.position)
                    _G_apply_148, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_148
                    _G_python_150, lastError = eval(self._G_expr_149, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_150
                    return (_G_python_150, self.currentError)
                _G_or_151, lastError = self._or([_G_or_105, _G_or_112, _G_or_119, _G_or_127, _G_or_135, _G_or_143])
                self.considerError(lastError, None)
                return (_G_or_151, self.currentError)
            _G_many_152, lastError = self.many(_G_many_104)
            self.considerError(lastError, 'comparison')
            _G_python_154, lastError = eval(self._G_expr_153, self.globals, _locals), None
            self.considerError(lastError, 'comparison')
            return (_G_python_154, self.currentError)


        def rule_add_expr(self):
            _locals = {'self': self}
            self.locals['add_expr'] = _locals
            self._trace(' mult_expr', (2150, 2160), self.input.position)
            _G_apply_155, lastError = self._apply(self.rule_mult_expr, "mult_expr", [])
            self.considerError(lastError, 'add_expr')
            _locals['node'] = _G_apply_155
            def _G_many_156():
                def _G_or_157():
                    self._trace('\n        ows', (2167, 2179), self.input.position)
                    _G_apply_158, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '+'", (2179, 2183), self.input.position)
                    _G_exactly_159, lastError = self.exactly('+')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2183, 2187), self.input.position)
                    _G_apply_160, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' mult_expr', (2187, 2197), self.input.position)
                    _G_apply_161, lastError = self._apply(self.rule_mult_expr, "mult_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_161
                    _G_python_163, lastError = eval(self._G_expr_162, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_163
                    return (_G_python_163, self.currentError)
                def _G_or_164():
                    self._trace(' ows', (2263, 2267), self.input.position)
                    _G_apply_165, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '-'", (2267, 2271), self.input.position)
                    _G_exactly_166, lastError = self.exactly('-')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2271, 2275), self.input.position)
                    _G_apply_167, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' mult_expr', (2275, 2285), self.input.position)
                    _G_apply_168, lastError = self._apply(self.rule_mult_expr, "mult_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_168
                    _G_python_170, lastError = eval(self._G_expr_169, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_170
                    return (_G_python_170, self.currentError)
                _G_or_171, lastError = self._or([_G_or_157, _G_or_164])
                self.considerError(lastError, None)
                return (_G_or_171, self.currentError)
            _G_many_172, lastError = self.many(_G_many_156)
            self.considerError(lastError, 'add_expr')
            _G_python_173, lastError = eval(self._G_expr_153, self.globals, _locals), None
            self.considerError(lastError, 'add_expr')
            return (_G_python_173, self.currentError)


        def rule_mult_expr(self):
            _locals = {'self': self}
            self.locals['mult_expr'] = _locals
            self._trace(' unary_expr', (2369, 2380), self.input.position)
            _G_apply_174, lastError = self._apply(self.rule_unary_expr, "unary_expr", [])
            self.considerError(lastError, 'mult_expr')
            _locals['node'] = _G_apply_174
            def _G_many_175():
                def _G_or_176():
                    self._trace('\n        ows', (2387, 2399), self.input.position)
                    _G_apply_177, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '*'", (2399, 2403), self.input.position)
                    _G_exactly_178, lastError = self.exactly('*')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2403, 2407), self.input.position)
                    _G_apply_179, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' unary_expr', (2407, 2418), self.input.position)
                    _G_apply_180, lastError = self._apply(self.rule_unary_expr, "unary_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_180
                    _G_python_182, lastError = eval(self._G_expr_181, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_182
                    return (_G_python_182, self.currentError)
                def _G_or_183():
                    self._trace(' ows', (2484, 2488), self.input.position)
                    _G_apply_184, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '/'", (2488, 2492), self.input.position)
                    _G_exactly_185, lastError = self.exactly('/')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2492, 2496), self.input.position)
                    _G_apply_186, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' unary_expr', (2496, 2507), self.input.position)
                    _G_apply_187, lastError = self._apply(self.rule_unary_expr, "unary_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_187
                    _G_python_189, lastError = eval(self._G_expr_188, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_189
                    return (_G_python_189, self.currentError)
                _G_or_190, lastError = self._or([_G_or_176, _G_or_183])
                self.considerError(lastError, None)
                return (_G_or_190, self.currentError)
            _G_many_191, lastError = self.many(_G_many_175)
            self.considerError(lastError, 'mult_expr')
            _G_python_192, lastError = eval(self._G_expr_153, self.globals, _locals), None
            self.considerError(lastError, 'mult_expr')
            return (_G_python_192, self.currentError)


        def rule_unary_expr(self):
            _locals = {'self': self}
            self.locals['unary_expr'] = _locals
            def _G_or_193():
                self._trace("\n        '-'", (2598, 2610), self.input.position)
                _G_exactly_194, lastError = self.exactly('-')
                self.considerError(lastError, None)
                self._trace(' unary_expr', (2610, 2621), self.input.position)
                _G_apply_195, lastError = self._apply(self.rule_unary_expr, "unary_expr", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_195
                _G_python_197, lastError = eval(self._G_expr_196, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_197, self.currentError)
            def _G_or_198():
                self._trace(" '+'", (2667, 2671), self.input.position)
                _G_exactly_199, lastError = self.exactly('+')
                self.considerError(lastError, None)
                self._trace(' unary_expr', (2671, 2682), self.input.position)
                _G_apply_200, lastError = self._apply(self.rule_unary_expr, "unary_expr", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_200
                _G_python_202, lastError = eval(self._G_expr_201, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_202, self.currentError)
            def _G_or_203():
                self._trace(' atom', (2728, 2733), self.input.position)
                _G_apply_204, lastError = self._apply(self.rule_atom, "atom", [])
                self.considerError(lastError, None)
                return (_G_apply_204, self.currentError)
            _G_or_205, lastError = self._or([_G_or_193, _G_or_198, _G_or_203])
            self.considerError(lastError, 'unary_expr')
            return (_G_or_205, self.currentError)


        def rule_atom(self):
            _locals = {'self': self}
            self.locals['atom'] = _locals
            def _G_or_206():
                self._trace("\n        # Parenthesized expression\n        '('", (2749, 2796), self.input.position)
                _G_exactly_207, lastError = self.exactly('(')
                self.considerError(lastError, None)
                self._trace(' comma_list', (2796, 2807), self.input.position)
                _G_apply_208, lastError = self._apply(self.rule_comma_list, "comma_list", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_208
                self._trace(" ')'", (2812, 2816), self.input.position)
                _G_exactly_209, lastError = self.exactly(')')
                self.considerError(lastError, None)
                _G_python_211, lastError = eval(self._G_expr_210, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_211, self.currentError)
            def _G_or_212():
                self._trace(" '['", (2927, 2931), self.input.position)
                _G_exactly_213, lastError = self.exactly('[')
                self.considerError(lastError, None)
                self._trace(' comma_list', (2931, 2942), self.input.position)
                _G_apply_214, lastError = self._apply(self.rule_comma_list, "comma_list", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_214
                self._trace(" ']'", (2947, 2951), self.input.position)
                _G_exactly_215, lastError = self.exactly(']')
                self.considerError(lastError, None)
                _G_python_216, lastError = eval(self._G_expr_210, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_216, self.currentError)
            def _G_or_217():
                self._trace(" 'u'", (3005, 3009), self.input.position)
                _G_exactly_218, lastError = self.exactly('u')
                self.considerError(lastError, None)
                self._trace(" 'r'", (3009, 3013), self.input.position)
                _G_exactly_219, lastError = self.exactly('r')
                self.considerError(lastError, None)
                self._trace(" 'l'", (3013, 3017), self.input.position)
                _G_exactly_220, lastError = self.exactly('l')
                self.considerError(lastError, None)
                self._trace(" '('", (3017, 3021), self.input.position)
                _G_exactly_221, lastError = self.exactly('(')
                self.considerError(lastError, None)
                def _G_or_222():
                    self._trace('string', (3023, 3029), self.input.position)
                    _G_apply_223, lastError = self._apply(self.rule_string, "string", [])
                    self.considerError(lastError, None)
                    return (_G_apply_223, self.currentError)
                def _G_or_224():
                    self._trace(' uri', (3031, 3035), self.input.position)
                    _G_apply_225, lastError = self._apply(self.rule_uri, "uri", [])
                    self.considerError(lastError, None)
                    return (_G_apply_225, self.currentError)
                _G_or_226, lastError = self._or([_G_or_222, _G_or_224])
                self.considerError(lastError, None)
                _locals['s'] = _G_or_226
                self._trace(" ')'", (3038, 3042), self.input.position)
                _G_exactly_227, lastError = self.exactly(')')
                self.considerError(lastError, None)
                _G_python_229, lastError = eval(self._G_expr_228, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_229, self.currentError)
            def _G_or_230():
                self._trace(' identifier', (3106, 3117), self.input.position)
                _G_apply_231, lastError = self._apply(self.rule_identifier, "identifier", [])
                self.considerError(lastError, None)
                _locals['name'] = _G_apply_231
                self._trace(" '('", (3122, 3126), self.input.position)
                _G_exactly_232, lastError = self.exactly('(')
                self.considerError(lastError, None)
                self._trace(' argspec', (3126, 3134), self.input.position)
                _G_apply_233, lastError = self._apply(self.rule_argspec, "argspec", [])
                self.considerError(lastError, None)
                _locals['args'] = _G_apply_233
                self._trace(" ')'", (3139, 3143), self.input.position)
                _G_exactly_234, lastError = self.exactly(')')
                self.considerError(lastError, None)
                _G_python_236, lastError = eval(self._G_expr_235, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_236, self.currentError)
            def _G_or_237():
                def _G_consumedby_238():
                    def _G_optional_239():
                        self._trace(" '!'", (3197, 3201), self.input.position)
                        _G_exactly_240, lastError = self.exactly('!')
                        self.considerError(lastError, None)
                        return (_G_exactly_240, self.currentError)
                    def _G_optional_241():
                        return (None, self.input.nullError())
                    _G_or_242, lastError = self._or([_G_optional_239, _G_optional_241])
                    self.considerError(lastError, None)
                    self._trace(' identifier', (3202, 3213), self.input.position)
                    _G_apply_243, lastError = self._apply(self.rule_identifier, "identifier", [])
                    self.considerError(lastError, None)
                    return (_G_apply_243, self.currentError)
                _G_consumedby_244, lastError = self.consumedby(_G_consumedby_238)
                self.considerError(lastError, None)
                _locals['word'] = _G_consumedby_244
                _G_python_246, lastError = eval(self._G_expr_245, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_246, self.currentError)
            def _G_or_247():
                self._trace(' number', (3281, 3288), self.input.position)
                _G_apply_248, lastError = self._apply(self.rule_number, "number", [])
                self.considerError(lastError, None)
                _locals['number'] = _G_apply_248
                def _G_optional_249():
                    def _G_consumedby_250():
                        def _G_or_251():
                            self._trace(" '%'", (3297, 3301), self.input.position)
                            _G_exactly_252, lastError = self.exactly('%')
                            self.considerError(lastError, None)
                            return (_G_exactly_252, self.currentError)
                        def _G_or_253():
                            def _G_many1_254():
                                self._trace(' letter', (3303, 3310), self.input.position)
                                _G_apply_255, lastError = self._apply(self.rule_letter, "letter", [])
                                self.considerError(lastError, None)
                                return (_G_apply_255, self.currentError)
                            _G_many1_256, lastError = self.many(_G_many1_254, _G_many1_254())
                            self.considerError(lastError, None)
                            return (_G_many1_256, self.currentError)
                        _G_or_257, lastError = self._or([_G_or_251, _G_or_253])
                        self.considerError(lastError, None)
                        return (_G_or_257, self.currentError)
                    _G_consumedby_258, lastError = self.consumedby(_G_consumedby_250)
                    self.considerError(lastError, None)
                    return (_G_consumedby_258, self.currentError)
                def _G_optional_259():
                    return (None, self.input.nullError())
                _G_or_260, lastError = self._or([_G_optional_249, _G_optional_259])
                self.considerError(lastError, None)
                _locals['unit'] = _G_or_260
                _G_python_262, lastError = eval(self._G_expr_261, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_262, self.currentError)
            def _G_or_263():
                self._trace(' string', (3397, 3404), self.input.position)
                _G_apply_264, lastError = self._apply(self.rule_string, "string", [])
                self.considerError(lastError, None)
                return (_G_apply_264, self.currentError)
            def _G_or_265():
                def _G_consumedby_266():
                    self._trace(" '#'", (3500, 3504), self.input.position)
                    _G_exactly_267, lastError = self.exactly('#')
                    self.considerError(lastError, None)
                    def _G_or_268():
                        def _G_consumedby_269():
                            def _G_repeat_270():
                                self._trace('hex', (3520, 3523), self.input.position)
                                _G_apply_271, lastError = self._apply(self.rule_hex, "hex", [])
                                self.considerError(lastError, None)
                                return (_G_apply_271, self.currentError)
                            _G_repeat_272, lastError = self.repeat(2, 2, _G_repeat_270)
                            self.considerError(lastError, None)
                            return (_G_repeat_272, self.currentError)
                        _G_consumedby_273, lastError = self.consumedby(_G_consumedby_269)
                        self.considerError(lastError, None)
                        _locals['red'] = _G_consumedby_273
                        def _G_consumedby_274():
                            def _G_repeat_275():
                                self._trace('hex', (3533, 3536), self.input.position)
                                _G_apply_276, lastError = self._apply(self.rule_hex, "hex", [])
                                self.considerError(lastError, None)
                                return (_G_apply_276, self.currentError)
                            _G_repeat_277, lastError = self.repeat(2, 2, _G_repeat_275)
                            self.considerError(lastError, None)
                            return (_G_repeat_277, self.currentError)
                        _G_consumedby_278, lastError = self.consumedby(_G_consumedby_274)
                        self.considerError(lastError, None)
                        _locals['green'] = _G_consumedby_278
                        def _G_consumedby_279():
                            def _G_repeat_280():
                                self._trace('hex', (3548, 3551), self.input.position)
                                _G_apply_281, lastError = self._apply(self.rule_hex, "hex", [])
                                self.considerError(lastError, None)
                                return (_G_apply_281, self.currentError)
                            _G_repeat_282, lastError = self.repeat(2, 2, _G_repeat_280)
                            self.considerError(lastError, None)
                            return (_G_repeat_282, self.currentError)
                        _G_consumedby_283, lastError = self.consumedby(_G_consumedby_279)
                        self.considerError(lastError, None)
                        _locals['blue'] = _G_consumedby_283
                        return (_G_consumedby_283, self.currentError)
                    def _G_or_284():
                        self._trace(' hex', (3689, 3693), self.input.position)
                        _G_apply_285, lastError = self._apply(self.rule_hex, "hex", [])
                        self.considerError(lastError, None)
                        _locals['red'] = _G_apply_285
                        self._trace(' hex', (3697, 3701), self.input.position)
                        _G_apply_286, lastError = self._apply(self.rule_hex, "hex", [])
                        self.considerError(lastError, None)
                        _locals['green'] = _G_apply_286
                        self._trace(' hex', (3707, 3711), self.input.position)
                        _G_apply_287, lastError = self._apply(self.rule_hex, "hex", [])
                        self.considerError(lastError, None)
                        _locals['blue'] = _G_apply_287
                        return (_G_apply_287, self.currentError)
                    _G_or_288, lastError = self._or([_G_or_268, _G_or_284])
                    self.considerError(lastError, None)
                    return (_G_or_288, self.currentError)
                _G_consumedby_289, lastError = self.consumedby(_G_consumedby_266)
                self.considerError(lastError, None)
                _locals['color'] = _G_consumedby_289
                _G_python_291, lastError = eval(self._G_expr_290, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_291, self.currentError)
            def _G_or_292():
                self._trace(' variable', (3919, 3928), self.input.position)
                _G_apply_293, lastError = self._apply(self.rule_variable, "variable", [])
                self.considerError(lastError, None)
                _locals['name'] = _G_apply_293
                _G_python_295, lastError = eval(self._G_expr_294, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_295, self.currentError)
            _G_or_296, lastError = self._or([_G_or_206, _G_or_212, _G_or_217, _G_or_230, _G_or_237, _G_or_247, _G_or_263, _G_or_265, _G_or_292])
            self.considerError(lastError, 'atom')
            return (_G_or_296, self.currentError)


        def rule_uri(self):
            _locals = {'self': self}
            self.locals['uri'] = _locals
            def _G_many_297():
                def _G_or_298():
                    self._trace('\n        escape', (4126, 4141), self.input.position)
                    _G_apply_299, lastError = self._apply(self.rule_escape, "escape", [])
                    self.considerError(lastError, None)
                    return (_G_apply_299, self.currentError)
                def _G_or_300():
                    self._trace(' anything', (4151, 4160), self.input.position)
                    _G_apply_301, lastError = self._apply(self.rule_anything, "anything", [])
                    self.considerError(lastError, None)
                    _locals['ch'] = _G_apply_301
                    def _G_pred_302():
                        _G_python_304, lastError = eval(self._G_expr_303, self.globals, _locals), None
                        self.considerError(lastError, None)
                        return (_G_python_304, self.currentError)
                    _G_pred_305, lastError = self.pred(_G_pred_302)
                    self.considerError(lastError, None)
                    _G_python_307, lastError = eval(self._G_expr_306, self.globals, _locals), None
                    self.considerError(lastError, None)
                    return (_G_python_307, self.currentError)
                _G_or_308, lastError = self._or([_G_or_298, _G_or_300])
                self.considerError(lastError, None)
                return (_G_or_308, self.currentError)
            _G_many_309, lastError = self.many(_G_many_297)
            self.considerError(lastError, 'uri')
            _locals['s'] = _G_many_309
            _G_python_311, lastError = eval(self._G_expr_310, self.globals, _locals), None
            self.considerError(lastError, 'uri')
            return (_G_python_311, self.currentError)


        def rule_string(self):
            _locals = {'self': self}
            self.locals['string'] = _locals
            def _G_or_312():
                self._trace('\n        \'"\'', (4275, 4287), self.input.position)
                _G_exactly_313, lastError = self.exactly('"')
                self.considerError(lastError, None)
                self._trace(' string_contents(\'"\')', (4287, 4308), self.input.position)
                _G_python_314, lastError = ('"'), None
                self.considerError(lastError, None)
                _G_apply_315, lastError = self._apply(self.rule_string_contents, "string_contents", [_G_python_314])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_315
                self._trace(' \'"\'', (4313, 4317), self.input.position)
                _G_exactly_316, lastError = self.exactly('"')
                self.considerError(lastError, None)
                _G_python_317, lastError = eval(self._G_expr_153, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_317, self.currentError)
            def _G_or_318():
                self._trace(" '\\''", (4335, 4340), self.input.position)
                _G_exactly_319, lastError = self.exactly("'")
                self.considerError(lastError, None)
                self._trace(" string_contents('\\'')", (4340, 4362), self.input.position)
                _G_python_320, lastError = ('\''), None
                self.considerError(lastError, None)
                _G_apply_321, lastError = self._apply(self.rule_string_contents, "string_contents", [_G_python_320])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_321
                self._trace(" '\\''", (4367, 4372), self.input.position)
                _G_exactly_322, lastError = self.exactly("'")
                self.considerError(lastError, None)
                _G_python_323, lastError = eval(self._G_expr_153, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_323, self.currentError)
            _G_or_324, lastError = self._or([_G_or_312, _G_or_318])
            self.considerError(lastError, 'string')
            return (_G_or_324, self.currentError)


        def rule_interpolation(self):
            _locals = {'self': self}
            self.locals['interpolation'] = _locals
            self._trace(" '#'", (4403, 4407), self.input.position)
            _G_exactly_325, lastError = self.exactly('#')
            self.considerError(lastError, 'interpolation')
            self._trace(" '{'", (4407, 4411), self.input.position)
            _G_exactly_326, lastError = self.exactly('{')
            self.considerError(lastError, 'interpolation')
            self._trace(' expression', (4411, 4422), self.input.position)
            _G_apply_327, lastError = self._apply(self.rule_expression, "expression", [])
            self.considerError(lastError, 'interpolation')
            _locals['node'] = _G_apply_327
            self._trace(" '}'", (4427, 4431), self.input.position)
            _G_exactly_328, lastError = self.exactly('}')
            self.considerError(lastError, 'interpolation')
            _G_python_329, lastError = eval(self._G_expr_153, self.globals, _locals), None
            self.considerError(lastError, 'interpolation')
            return (_G_python_329, self.currentError)


        def rule_string_contents(self):
            _locals = {'self': self}
            self.locals['string_contents'] = _locals
            _G_apply_330, lastError = self._apply(self.rule_anything, "anything", [])
            self.considerError(lastError, 'string_contents')
            _locals['quote'] = _G_apply_330
            self._trace('\n            string_part(quote)', (4477, 4508), self.input.position)
            _G_python_332, lastError = eval(self._G_expr_331, self.globals, _locals), None
            self.considerError(lastError, 'string_contents')
            _G_apply_333, lastError = self._apply(self.rule_string_part, "string_part", [_G_python_332])
            self.considerError(lastError, 'string_contents')
            _locals['before'] = _G_apply_333
            _G_python_335, lastError = eval(self._G_expr_334, self.globals, _locals), None
            self.considerError(lastError, 'string_contents')
            _locals['retval'] = _G_python_335
            def _G_many_336():
                self._trace('\n                interpolation', (4609, 4639), self.input.position)
                _G_apply_337, lastError = self._apply(self.rule_interpolation, "interpolation", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_337
                self._trace('\n                string_part(quote)', (4644, 4679), self.input.position)
                _G_python_338, lastError = eval(self._G_expr_331, self.globals, _locals), None
                self.considerError(lastError, None)
                _G_apply_339, lastError = self._apply(self.rule_string_part, "string_part", [_G_python_338])
                self.considerError(lastError, None)
                _locals['after'] = _G_apply_339
                _G_python_341, lastError = eval(self._G_expr_340, self.globals, _locals), None
                self.considerError(lastError, None)
                _locals['retval'] = _G_python_341
                return (_G_python_341, self.currentError)
            _G_many_342, lastError = self.many(_G_many_336)
            self.considerError(lastError, 'string_contents')
            _G_python_344, lastError = eval(self._G_expr_343, self.globals, _locals), None
            self.considerError(lastError, 'string_contents')
            return (_G_python_344, self.currentError)


        def rule_string_part(self):
            _locals = {'self': self}
            self.locals['string_part'] = _locals
            _G_apply_345, lastError = self._apply(self.rule_anything, "anything", [])
            self.considerError(lastError, 'string_part')
            _locals['quote'] = _G_apply_345
            def _G_consumedby_346():
                def _G_many_347():
                    def _G_or_348():
                        self._trace("\n        '#'", (4857, 4869), self.input.position)
                        _G_exactly_349, lastError = self.exactly('#')
                        self.considerError(lastError, None)
                        def _G_not_350():
                            self._trace("'{'", (4871, 4874), self.input.position)
                            _G_exactly_351, lastError = self.exactly('{')
                            self.considerError(lastError, None)
                            return (_G_exactly_351, self.currentError)
                        _G_not_352, lastError = self._not(_G_not_350)
                        self.considerError(lastError, None)
                        return (_G_not_352, self.currentError)
                    def _G_or_353():
                        self._trace(' anything', (4884, 4893), self.input.position)
                        _G_apply_354, lastError = self._apply(self.rule_anything, "anything", [])
                        self.considerError(lastError, None)
                        _locals['ch'] = _G_apply_354
                        def _G_pred_355():
                            _G_python_357, lastError = eval(self._G_expr_356, self.globals, _locals), None
                            self.considerError(lastError, None)
                            return (_G_python_357, self.currentError)
                        _G_pred_358, lastError = self.pred(_G_pred_355)
                        self.considerError(lastError, None)
                        return (_G_pred_358, self.currentError)
                    _G_or_359, lastError = self._or([_G_or_348, _G_or_353])
                    self.considerError(lastError, None)
                    return (_G_or_359, self.currentError)
                _G_many_360, lastError = self.many(_G_many_347)
                self.considerError(lastError, None)
                return (_G_many_360, self.currentError)
            _G_consumedby_361, lastError = self.consumedby(_G_consumedby_346)
            self.considerError(lastError, 'string_part')
            return (_G_consumedby_361, self.currentError)


        def rule_argspec(self):
            _locals = {'self': self}
            self.locals['argspec'] = _locals
            def _G_many_362():
                self._trace('\n        argspec_item', (4983, 5004), self.input.position)
                _G_apply_363, lastError = self._apply(self.rule_argspec_item, "argspec_item", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_363
                self._trace('\n        ows', (5009, 5021), self.input.position)
                _G_apply_364, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                self._trace(" ','", (5021, 5025), self.input.position)
                _G_exactly_365, lastError = self.exactly(',')
                self.considerError(lastError, None)
                self._trace(' ows', (5025, 5029), self.input.position)
                _G_apply_366, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                _G_python_367, lastError = eval(self._G_expr_153, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_367, self.currentError)
            _G_many_368, lastError = self.many(_G_many_362)
            self.considerError(lastError, 'argspec')
            _locals['nodes'] = _G_many_368
            def _G_optional_369():
                self._trace(' argspec_item', (5064, 5077), self.input.position)
                _G_apply_370, lastError = self._apply(self.rule_argspec_item, "argspec_item", [])
                self.considerError(lastError, None)
                _locals['tail'] = _G_apply_370
                self._trace(' ows', (5082, 5086), self.input.position)
                _G_apply_371, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                _G_python_373, lastError = eval(self._G_expr_372, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_373, self.currentError)
            def _G_optional_374():
                return (None, self.input.nullError())
            _G_or_375, lastError = self._or([_G_optional_369, _G_optional_374])
            self.considerError(lastError, 'argspec')
            _G_python_377, lastError = eval(self._G_expr_376, self.globals, _locals), None
            self.considerError(lastError, 'argspec')
            return (_G_python_377, self.currentError)


        def rule_argspec_item(self):
            _locals = {'self': self}
            self.locals['argspec_item'] = _locals
            self._trace('\n    ows', (5157, 5165), self.input.position)
            _G_apply_378, lastError = self._apply(self.rule_ows, "ows", [])
            self.considerError(lastError, 'argspec_item')
            def _G_optional_379():
                self._trace(' variable', (5181, 5190), self.input.position)
                _G_apply_380, lastError = self._apply(self.rule_variable, "variable", [])
                self.considerError(lastError, None)
                _locals['name'] = _G_apply_380
                self._trace(' ows', (5195, 5199), self.input.position)
                _G_apply_381, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                self._trace(" ':'", (5199, 5203), self.input.position)
                _G_exactly_382, lastError = self.exactly(':')
                self.considerError(lastError, None)
                self._trace(' ows', (5203, 5207), self.input.position)
                _G_apply_383, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                _G_python_385, lastError = eval(self._G_expr_384, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_385, self.currentError)
            def _G_optional_386():
                return (None, self.input.nullError())
            _G_or_387, lastError = self._or([_G_optional_379, _G_optional_386])
            self.considerError(lastError, 'argspec_item')
            _locals['name'] = _G_or_387
            self._trace('\n        spaced_list', (5223, 5243), self.input.position)
            _G_apply_388, lastError = self._apply(self.rule_spaced_list, "spaced_list", [])
            self.considerError(lastError, 'argspec_item')
            _locals['value'] = _G_apply_388
            _G_python_390, lastError = eval(self._G_expr_389, self.globals, _locals), None
            self.considerError(lastError, 'argspec_item')
            return (_G_python_390, self.currentError)


        _G_expr_334 = compile('Literal(String(before, quotes=quote))', '<string>', 'eval')
        _G_expr_306 = compile('ch', '<string>', 'eval')
        _G_expr_110 = compile('BinaryOp(operator.lt, node, operand)', '<string>', 'eval')
        _G_expr_196 = compile('UnaryOp(operator.neg, node)', '<string>', 'eval')
        _G_expr_290 = compile('Literal(ColorValue(ParserValue(color)))', '<string>', 'eval')
        _G_expr_149 = compile('BinaryOp(operator.ne, node, operand)', '<string>', 'eval')
        _G_expr_100 = compile('NotOp(node)', '<string>', 'eval')
        _G_expr_372 = compile('nodes.append(tail)', '<string>', 'eval')
        _G_expr_303 = compile('ord(ch) > 32 and ch not in \' !"$\\\'()\'', '<string>', 'eval')
        _G_expr_210 = compile('Parentheses(node)', '<string>', 'eval')
        _G_expr_228 = compile("FunctionLiteral('url', s)", '<string>', 'eval')
        _G_expr_245 = compile('Literal(parse_bareword(word))', '<string>', 'eval')
        _G_expr_169 = compile('BinaryOp(operator.sub, node, operand)', '<string>', 'eval')
        _G_expr_60 = compile('tail', '<string>', 'eval')
        _G_expr_91 = compile('AllOp(*[head] + tails) if tails else head', '<string>', 'eval')
        _G_expr_331 = compile('quote', '<string>', 'eval')
        _G_expr_235 = compile('CallOp(name, args)', '<string>', 'eval')
        _G_expr_63 = compile('ListLiteral([head] + tails) if tails else head', '<string>', 'eval')
        _G_expr_294 = compile('Variable(name)', '<string>', 'eval')
        _G_expr_153 = compile('node', '<string>', 'eval')
        _G_expr_201 = compile('UnaryOp(operator.pos, node)', '<string>', 'eval')
        _G_expr_141 = compile('BinaryOp(operator.eq, node, operand)', '<string>', 'eval')
        _G_expr_162 = compile('BinaryOp(operator.add, node, operand)', '<string>', 'eval')
        _G_expr_117 = compile('BinaryOp(operator.gt, node, operand)', '<string>', 'eval')
        _G_expr_261 = compile('Literal(NumberValue(float(number), unit=unit))', '<string>', 'eval')
        _G_expr_188 = compile('BinaryOp(operator.truediv, node, operand)', '<string>', 'eval')
        _G_expr_15 = compile('unichr(int(cp, 16))', '<string>', 'eval')
        _G_expr_125 = compile('BinaryOp(operator.le, node, operand)', '<string>', 'eval')
        _G_expr_71 = compile('ListLiteral([head] + tails, comma=False) if tails else head', '<string>', 'eval')
        _G_expr_181 = compile('BinaryOp(operator.mul, node, operand)', '<string>', 'eval')
        _G_expr_343 = compile('retval', '<string>', 'eval')
        _G_expr_310 = compile("Literal(String(''.join(s), quotes=None))", '<string>', 'eval')
        _G_expr_384 = compile('name', '<string>', 'eval')
        _G_expr_389 = compile('(name, value)', '<string>', 'eval')
        _G_expr_376 = compile('ArgspecLiteral(nodes)', '<string>', 'eval')
        _G_expr_340 = compile('Interpolation(retval, node, Literal(String(after, quotes=quote)), quotes=quote)', '<string>', 'eval')
        _G_expr_81 = compile('AnyOp(*[head] + tails) if tails else head', '<string>', 'eval')
        _G_expr_133 = compile('BinaryOp(operator.ge, node, operand)', '<string>', 'eval')
        _G_expr_356 = compile("ch not in ('#', quote)", '<string>', 'eval')
    if Grammar.globals is not None:
        Grammar.globals = Grammar.globals.copy()
        Grammar.globals.update(ruleGlobals)
    else:
        Grammar.globals = ruleGlobals
    return Grammar