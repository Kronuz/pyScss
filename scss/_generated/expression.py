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
                self._trace(' letterish', (734, 744), self.input.position)
                _G_apply_21, lastError = self._apply(self.rule_letterish, "letterish", [])
                self.considerError(lastError, None)
                def _G_many_22():
                    def _G_or_23():
                        self._trace('letterish', (746, 755), self.input.position)
                        _G_apply_24, lastError = self._apply(self.rule_letterish, "letterish", [])
                        self.considerError(lastError, None)
                        return (_G_apply_24, self.currentError)
                    def _G_or_25():
                        self._trace(' digit', (757, 763), self.input.position)
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
                        self._trace(' digit', (778, 784), self.input.position)
                        _G_apply_33, lastError = self._apply(self.rule_digit, "digit", [])
                        self.considerError(lastError, None)
                        return (_G_apply_33, self.currentError)
                    _G_many1_34, lastError = self.many(_G_many1_32, _G_many1_32())
                    self.considerError(lastError, None)
                    def _G_optional_35():
                        self._trace("'.'", (787, 790), self.input.position)
                        _G_exactly_36, lastError = self.exactly('.')
                        self.considerError(lastError, None)
                        def _G_many_37():
                            self._trace(' digit', (790, 796), self.input.position)
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
                    self._trace(" '.'", (801, 805), self.input.position)
                    _G_exactly_43, lastError = self.exactly('.')
                    self.considerError(lastError, None)
                    def _G_many1_44():
                        self._trace(' digit', (805, 811), self.input.position)
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
                self._trace(" '$'", (827, 831), self.input.position)
                _G_exactly_50, lastError = self.exactly('$')
                self.considerError(lastError, None)
                self._trace(' identifier', (831, 842), self.input.position)
                _G_apply_51, lastError = self._apply(self.rule_identifier, "identifier", [])
                self.considerError(lastError, None)
                return (_G_apply_51, self.currentError)
            _G_consumedby_52, lastError = self.consumedby(_G_consumedby_49)
            self.considerError(lastError, 'variable')
            return (_G_consumedby_52, self.currentError)


        def rule_expression(self):
            _locals = {'self': self}
            self.locals['expression'] = _locals
            self._trace(' comma_list', (874, 885), self.input.position)
            _G_apply_53, lastError = self._apply(self.rule_comma_list, "comma_list", [])
            self.considerError(lastError, 'expression')
            return (_G_apply_53, self.currentError)


        def rule_comma_list(self):
            _locals = {'self': self}
            self.locals['comma_list'] = _locals
            self._trace(' spaced_list', (899, 911), self.input.position)
            _G_apply_54, lastError = self._apply(self.rule_spaced_list, "spaced_list", [])
            self.considerError(lastError, 'comma_list')
            _locals['head'] = _G_apply_54
            def _G_many_55():
                self._trace('\n        ows', (918, 930), self.input.position)
                _G_apply_56, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                self._trace(" ','", (930, 934), self.input.position)
                _G_exactly_57, lastError = self.exactly(',')
                self.considerError(lastError, None)
                self._trace(' ows', (934, 938), self.input.position)
                _G_apply_58, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                self._trace('\n        spaced_list', (938, 958), self.input.position)
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
            self._trace(' single_expression', (1049, 1067), self.input.position)
            _G_apply_65, lastError = self._apply(self.rule_single_expression, "single_expression", [])
            self.considerError(lastError, 'spaced_list')
            _locals['head'] = _G_apply_65
            def _G_many_66():
                self._trace('\n        ows', (1074, 1086), self.input.position)
                _G_apply_67, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                self._trace('\n        single_expression', (1086, 1112), self.input.position)
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
            self._trace(' or_test', (1223, 1231), self.input.position)
            _G_apply_73, lastError = self._apply(self.rule_or_test, "or_test", [])
            self.considerError(lastError, 'single_expression')
            return (_G_apply_73, self.currentError)


        def rule_or_test(self):
            _locals = {'self': self}
            self.locals['or_test'] = _locals
            self._trace(' and_test', (1242, 1251), self.input.position)
            _G_apply_74, lastError = self._apply(self.rule_and_test, "and_test", [])
            self.considerError(lastError, 'or_test')
            _locals['head'] = _G_apply_74
            def _G_many_75():
                self._trace("\n        'o'", (1258, 1270), self.input.position)
                _G_exactly_76, lastError = self.exactly('o')
                self.considerError(lastError, None)
                self._trace(" 'r'", (1270, 1274), self.input.position)
                _G_exactly_77, lastError = self.exactly('r')
                self.considerError(lastError, None)
                self._trace('\n        and_test', (1274, 1291), self.input.position)
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
            self._trace(' not_test', (1374, 1383), self.input.position)
            _G_apply_83, lastError = self._apply(self.rule_not_test, "not_test", [])
            self.considerError(lastError, 'and_test')
            _locals['head'] = _G_apply_83
            def _G_many_84():
                self._trace("\n        'a'", (1390, 1402), self.input.position)
                _G_exactly_85, lastError = self.exactly('a')
                self.considerError(lastError, None)
                self._trace(" 'n'", (1402, 1406), self.input.position)
                _G_exactly_86, lastError = self.exactly('n')
                self.considerError(lastError, None)
                self._trace(" 'd'", (1406, 1410), self.input.position)
                _G_exactly_87, lastError = self.exactly('d')
                self.considerError(lastError, None)
                self._trace('\n        not_test', (1410, 1427), self.input.position)
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
                self._trace(' comparison', (1510, 1521), self.input.position)
                _G_apply_94, lastError = self._apply(self.rule_comparison, "comparison", [])
                self.considerError(lastError, None)
                return (_G_apply_94, self.currentError)
            def _G_or_95():
                self._trace(" 'n'", (1525, 1529), self.input.position)
                _G_exactly_96, lastError = self.exactly('n')
                self.considerError(lastError, None)
                self._trace(" 'o'", (1529, 1533), self.input.position)
                _G_exactly_97, lastError = self.exactly('o')
                self.considerError(lastError, None)
                self._trace(" 't'", (1533, 1537), self.input.position)
                _G_exactly_98, lastError = self.exactly('t')
                self.considerError(lastError, None)
                self._trace(' not_test', (1537, 1546), self.input.position)
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
            self._trace(' add_expr', (1582, 1591), self.input.position)
            _G_apply_103, lastError = self._apply(self.rule_add_expr, "add_expr", [])
            self.considerError(lastError, 'comparison')
            _locals['node'] = _G_apply_103
            def _G_many_104():
                def _G_or_105():
                    self._trace('\n        ows', (1598, 1610), self.input.position)
                    _G_apply_106, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '<'", (1610, 1614), self.input.position)
                    _G_exactly_107, lastError = self.exactly('<')
                    self.considerError(lastError, None)
                    self._trace(' ows', (1614, 1618), self.input.position)
                    _G_apply_108, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (1618, 1627), self.input.position)
                    _G_apply_109, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_109
                    _G_python_111, lastError = eval(self._G_expr_110, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_111
                    return (_G_python_111, self.currentError)
                def _G_or_112():
                    self._trace(' ows', (1692, 1696), self.input.position)
                    _G_apply_113, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '>'", (1696, 1700), self.input.position)
                    _G_exactly_114, lastError = self.exactly('>')
                    self.considerError(lastError, None)
                    self._trace(' ows', (1700, 1704), self.input.position)
                    _G_apply_115, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (1704, 1713), self.input.position)
                    _G_apply_116, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_116
                    _G_python_118, lastError = eval(self._G_expr_117, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_118
                    return (_G_python_118, self.currentError)
                def _G_or_119():
                    self._trace(' ows', (1778, 1782), self.input.position)
                    _G_apply_120, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '<'", (1782, 1786), self.input.position)
                    _G_exactly_121, lastError = self.exactly('<')
                    self.considerError(lastError, None)
                    self._trace(" '='", (1786, 1790), self.input.position)
                    _G_exactly_122, lastError = self.exactly('=')
                    self.considerError(lastError, None)
                    self._trace(' ows', (1790, 1794), self.input.position)
                    _G_apply_123, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (1794, 1803), self.input.position)
                    _G_apply_124, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_124
                    _G_python_126, lastError = eval(self._G_expr_125, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_126
                    return (_G_python_126, self.currentError)
                def _G_or_127():
                    self._trace(' ows', (1868, 1872), self.input.position)
                    _G_apply_128, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '>'", (1872, 1876), self.input.position)
                    _G_exactly_129, lastError = self.exactly('>')
                    self.considerError(lastError, None)
                    self._trace(" '='", (1876, 1880), self.input.position)
                    _G_exactly_130, lastError = self.exactly('=')
                    self.considerError(lastError, None)
                    self._trace(' ows', (1880, 1884), self.input.position)
                    _G_apply_131, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (1884, 1893), self.input.position)
                    _G_apply_132, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_132
                    _G_python_134, lastError = eval(self._G_expr_133, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_134
                    return (_G_python_134, self.currentError)
                def _G_or_135():
                    self._trace(' ows', (1958, 1962), self.input.position)
                    _G_apply_136, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '='", (1962, 1966), self.input.position)
                    _G_exactly_137, lastError = self.exactly('=')
                    self.considerError(lastError, None)
                    self._trace(" '='", (1966, 1970), self.input.position)
                    _G_exactly_138, lastError = self.exactly('=')
                    self.considerError(lastError, None)
                    self._trace(' ows', (1970, 1974), self.input.position)
                    _G_apply_139, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (1974, 1983), self.input.position)
                    _G_apply_140, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_140
                    _G_python_142, lastError = eval(self._G_expr_141, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_142
                    return (_G_python_142, self.currentError)
                def _G_or_143():
                    self._trace(' ows', (2048, 2052), self.input.position)
                    _G_apply_144, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '!'", (2052, 2056), self.input.position)
                    _G_exactly_145, lastError = self.exactly('!')
                    self.considerError(lastError, None)
                    self._trace(" '='", (2056, 2060), self.input.position)
                    _G_exactly_146, lastError = self.exactly('=')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2060, 2064), self.input.position)
                    _G_apply_147, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (2064, 2073), self.input.position)
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
            self._trace(' mult_expr', (2155, 2165), self.input.position)
            _G_apply_155, lastError = self._apply(self.rule_mult_expr, "mult_expr", [])
            self.considerError(lastError, 'add_expr')
            _locals['node'] = _G_apply_155
            def _G_many_156():
                def _G_or_157():
                    self._trace('\n        ows', (2172, 2184), self.input.position)
                    _G_apply_158, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '+'", (2184, 2188), self.input.position)
                    _G_exactly_159, lastError = self.exactly('+')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2188, 2192), self.input.position)
                    _G_apply_160, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' mult_expr', (2192, 2202), self.input.position)
                    _G_apply_161, lastError = self._apply(self.rule_mult_expr, "mult_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_161
                    _G_python_163, lastError = eval(self._G_expr_162, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_163
                    return (_G_python_163, self.currentError)
                def _G_or_164():
                    self._trace(' ows', (2268, 2272), self.input.position)
                    _G_apply_165, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '-'", (2272, 2276), self.input.position)
                    _G_exactly_166, lastError = self.exactly('-')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2276, 2280), self.input.position)
                    _G_apply_167, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' mult_expr', (2280, 2290), self.input.position)
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
            self._trace(' unary_expr', (2374, 2385), self.input.position)
            _G_apply_174, lastError = self._apply(self.rule_unary_expr, "unary_expr", [])
            self.considerError(lastError, 'mult_expr')
            _locals['node'] = _G_apply_174
            def _G_many_175():
                def _G_or_176():
                    self._trace('\n        ows', (2392, 2404), self.input.position)
                    _G_apply_177, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '*'", (2404, 2408), self.input.position)
                    _G_exactly_178, lastError = self.exactly('*')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2408, 2412), self.input.position)
                    _G_apply_179, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' unary_expr', (2412, 2423), self.input.position)
                    _G_apply_180, lastError = self._apply(self.rule_unary_expr, "unary_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_180
                    _G_python_182, lastError = eval(self._G_expr_181, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_182
                    return (_G_python_182, self.currentError)
                def _G_or_183():
                    self._trace(' ows', (2489, 2493), self.input.position)
                    _G_apply_184, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '/'", (2493, 2497), self.input.position)
                    _G_exactly_185, lastError = self.exactly('/')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2497, 2501), self.input.position)
                    _G_apply_186, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' unary_expr', (2501, 2512), self.input.position)
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
                self._trace("\n        '-'", (2603, 2615), self.input.position)
                _G_exactly_194, lastError = self.exactly('-')
                self.considerError(lastError, None)
                self._trace(' unary_expr', (2615, 2626), self.input.position)
                _G_apply_195, lastError = self._apply(self.rule_unary_expr, "unary_expr", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_195
                _G_python_197, lastError = eval(self._G_expr_196, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_197, self.currentError)
            def _G_or_198():
                self._trace(" '+'", (2672, 2676), self.input.position)
                _G_exactly_199, lastError = self.exactly('+')
                self.considerError(lastError, None)
                self._trace(' unary_expr', (2676, 2687), self.input.position)
                _G_apply_200, lastError = self._apply(self.rule_unary_expr, "unary_expr", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_200
                _G_python_202, lastError = eval(self._G_expr_201, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_202, self.currentError)
            def _G_or_203():
                self._trace(' atom', (2733, 2738), self.input.position)
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
                self._trace("\n        # Parenthesized expression\n        '('", (2754, 2801), self.input.position)
                _G_exactly_207, lastError = self.exactly('(')
                self.considerError(lastError, None)
                self._trace(' comma_list', (2801, 2812), self.input.position)
                _G_apply_208, lastError = self._apply(self.rule_comma_list, "comma_list", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_208
                self._trace(" ')'", (2817, 2821), self.input.position)
                _G_exactly_209, lastError = self.exactly(')')
                self.considerError(lastError, None)
                _G_python_211, lastError = eval(self._G_expr_210, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_211, self.currentError)
            def _G_or_212():
                self._trace(" '['", (2932, 2936), self.input.position)
                _G_exactly_213, lastError = self.exactly('[')
                self.considerError(lastError, None)
                self._trace(' comma_list', (2936, 2947), self.input.position)
                _G_apply_214, lastError = self._apply(self.rule_comma_list, "comma_list", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_214
                self._trace(" ']'", (2952, 2956), self.input.position)
                _G_exactly_215, lastError = self.exactly(']')
                self.considerError(lastError, None)
                _G_python_216, lastError = eval(self._G_expr_210, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_216, self.currentError)
            def _G_or_217():
                self._trace(" 'u'", (3010, 3014), self.input.position)
                _G_exactly_218, lastError = self.exactly('u')
                self.considerError(lastError, None)
                self._trace(" 'r'", (3014, 3018), self.input.position)
                _G_exactly_219, lastError = self.exactly('r')
                self.considerError(lastError, None)
                self._trace(" 'l'", (3018, 3022), self.input.position)
                _G_exactly_220, lastError = self.exactly('l')
                self.considerError(lastError, None)
                self._trace(" '('", (3022, 3026), self.input.position)
                _G_exactly_221, lastError = self.exactly('(')
                self.considerError(lastError, None)
                self._trace(' inside_url', (3026, 3037), self.input.position)
                _G_apply_222, lastError = self._apply(self.rule_inside_url, "inside_url", [])
                self.considerError(lastError, None)
                _locals['s'] = _G_apply_222
                self._trace(" ')'", (3039, 3043), self.input.position)
                _G_exactly_223, lastError = self.exactly(')')
                self.considerError(lastError, None)
                _G_python_225, lastError = eval(self._G_expr_224, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_225, self.currentError)
            def _G_or_226():
                self._trace(' identifier', (3107, 3118), self.input.position)
                _G_apply_227, lastError = self._apply(self.rule_identifier, "identifier", [])
                self.considerError(lastError, None)
                _locals['name'] = _G_apply_227
                self._trace(" '('", (3123, 3127), self.input.position)
                _G_exactly_228, lastError = self.exactly('(')
                self.considerError(lastError, None)
                self._trace(' argspec', (3127, 3135), self.input.position)
                _G_apply_229, lastError = self._apply(self.rule_argspec, "argspec", [])
                self.considerError(lastError, None)
                _locals['args'] = _G_apply_229
                self._trace(" ')'", (3140, 3144), self.input.position)
                _G_exactly_230, lastError = self.exactly(')')
                self.considerError(lastError, None)
                _G_python_232, lastError = eval(self._G_expr_231, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_232, self.currentError)
            def _G_or_233():
                def _G_consumedby_234():
                    def _G_optional_235():
                        self._trace(" '!'", (3198, 3202), self.input.position)
                        _G_exactly_236, lastError = self.exactly('!')
                        self.considerError(lastError, None)
                        return (_G_exactly_236, self.currentError)
                    def _G_optional_237():
                        return (None, self.input.nullError())
                    _G_or_238, lastError = self._or([_G_optional_235, _G_optional_237])
                    self.considerError(lastError, None)
                    self._trace(' identifier', (3203, 3214), self.input.position)
                    _G_apply_239, lastError = self._apply(self.rule_identifier, "identifier", [])
                    self.considerError(lastError, None)
                    return (_G_apply_239, self.currentError)
                _G_consumedby_240, lastError = self.consumedby(_G_consumedby_234)
                self.considerError(lastError, None)
                _locals['word'] = _G_consumedby_240
                _G_python_242, lastError = eval(self._G_expr_241, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_242, self.currentError)
            def _G_or_243():
                self._trace(' number', (3282, 3289), self.input.position)
                _G_apply_244, lastError = self._apply(self.rule_number, "number", [])
                self.considerError(lastError, None)
                _locals['number'] = _G_apply_244
                def _G_optional_245():
                    def _G_consumedby_246():
                        def _G_or_247():
                            self._trace(" '%'", (3298, 3302), self.input.position)
                            _G_exactly_248, lastError = self.exactly('%')
                            self.considerError(lastError, None)
                            return (_G_exactly_248, self.currentError)
                        def _G_or_249():
                            def _G_many1_250():
                                self._trace(' letter', (3304, 3311), self.input.position)
                                _G_apply_251, lastError = self._apply(self.rule_letter, "letter", [])
                                self.considerError(lastError, None)
                                return (_G_apply_251, self.currentError)
                            _G_many1_252, lastError = self.many(_G_many1_250, _G_many1_250())
                            self.considerError(lastError, None)
                            return (_G_many1_252, self.currentError)
                        _G_or_253, lastError = self._or([_G_or_247, _G_or_249])
                        self.considerError(lastError, None)
                        return (_G_or_253, self.currentError)
                    _G_consumedby_254, lastError = self.consumedby(_G_consumedby_246)
                    self.considerError(lastError, None)
                    return (_G_consumedby_254, self.currentError)
                def _G_optional_255():
                    return (None, self.input.nullError())
                _G_or_256, lastError = self._or([_G_optional_245, _G_optional_255])
                self.considerError(lastError, None)
                _locals['unit'] = _G_or_256
                _G_python_258, lastError = eval(self._G_expr_257, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_258, self.currentError)
            def _G_or_259():
                self._trace(' string', (3393, 3400), self.input.position)
                _G_apply_260, lastError = self._apply(self.rule_string, "string", [])
                self.considerError(lastError, None)
                return (_G_apply_260, self.currentError)
            def _G_or_261():
                self._trace(" '#'", (3499, 3503), self.input.position)
                _G_exactly_262, lastError = self.exactly('#')
                self.considerError(lastError, None)
                def _G_or_263():
                    def _G_consumedby_264():
                        def _G_repeat_265():
                            self._trace('hex', (3519, 3522), self.input.position)
                            _G_apply_266, lastError = self._apply(self.rule_hex, "hex", [])
                            self.considerError(lastError, None)
                            return (_G_apply_266, self.currentError)
                        _G_repeat_267, lastError = self.repeat(2, 2, _G_repeat_265)
                        self.considerError(lastError, None)
                        return (_G_repeat_267, self.currentError)
                    _G_consumedby_268, lastError = self.consumedby(_G_consumedby_264)
                    self.considerError(lastError, None)
                    _locals['red'] = _G_consumedby_268
                    def _G_consumedby_269():
                        def _G_repeat_270():
                            self._trace('hex', (3532, 3535), self.input.position)
                            _G_apply_271, lastError = self._apply(self.rule_hex, "hex", [])
                            self.considerError(lastError, None)
                            return (_G_apply_271, self.currentError)
                        _G_repeat_272, lastError = self.repeat(2, 2, _G_repeat_270)
                        self.considerError(lastError, None)
                        return (_G_repeat_272, self.currentError)
                    _G_consumedby_273, lastError = self.consumedby(_G_consumedby_269)
                    self.considerError(lastError, None)
                    _locals['green'] = _G_consumedby_273
                    def _G_consumedby_274():
                        def _G_repeat_275():
                            self._trace('hex', (3547, 3550), self.input.position)
                            _G_apply_276, lastError = self._apply(self.rule_hex, "hex", [])
                            self.considerError(lastError, None)
                            return (_G_apply_276, self.currentError)
                        _G_repeat_277, lastError = self.repeat(2, 2, _G_repeat_275)
                        self.considerError(lastError, None)
                        return (_G_repeat_277, self.currentError)
                    _G_consumedby_278, lastError = self.consumedby(_G_consumedby_274)
                    self.considerError(lastError, None)
                    _locals['blue'] = _G_consumedby_278
                    def _G_optional_279():
                        def _G_consumedby_280():
                            def _G_repeat_281():
                                self._trace('hex', (3573, 3576), self.input.position)
                                _G_apply_282, lastError = self._apply(self.rule_hex, "hex", [])
                                self.considerError(lastError, None)
                                return (_G_apply_282, self.currentError)
                            _G_repeat_283, lastError = self.repeat(2, 2, _G_repeat_281)
                            self.considerError(lastError, None)
                            return (_G_repeat_283, self.currentError)
                        _G_consumedby_284, lastError = self.consumedby(_G_consumedby_280)
                        self.considerError(lastError, None)
                        return (_G_consumedby_284, self.currentError)
                    def _G_optional_285():
                        return (None, self.input.nullError())
                    _G_or_286, lastError = self._or([_G_optional_279, _G_optional_285])
                    self.considerError(lastError, None)
                    _locals['alpha'] = _G_or_286
                    _G_python_288, lastError = eval(self._G_expr_287, self.globals, _locals), None
                    self.considerError(lastError, None)
                    return (_G_python_288, self.currentError)
                def _G_or_289():
                    self._trace(' hex', (3901, 3905), self.input.position)
                    _G_apply_290, lastError = self._apply(self.rule_hex, "hex", [])
                    self.considerError(lastError, None)
                    _locals['red'] = _G_apply_290
                    self._trace(' hex', (3909, 3913), self.input.position)
                    _G_apply_291, lastError = self._apply(self.rule_hex, "hex", [])
                    self.considerError(lastError, None)
                    _locals['green'] = _G_apply_291
                    self._trace(' hex', (3919, 3923), self.input.position)
                    _G_apply_292, lastError = self._apply(self.rule_hex, "hex", [])
                    self.considerError(lastError, None)
                    _locals['blue'] = _G_apply_292
                    def _G_optional_293():
                        self._trace(' hex', (3928, 3932), self.input.position)
                        _G_apply_294, lastError = self._apply(self.rule_hex, "hex", [])
                        self.considerError(lastError, None)
                        return (_G_apply_294, self.currentError)
                    def _G_optional_295():
                        return (None, self.input.nullError())
                    _G_or_296, lastError = self._or([_G_optional_293, _G_optional_295])
                    self.considerError(lastError, None)
                    _locals['alpha'] = _G_or_296
                    _G_python_298, lastError = eval(self._G_expr_297, self.globals, _locals), None
                    self.considerError(lastError, None)
                    return (_G_python_298, self.currentError)
                _G_or_299, lastError = self._or([_G_or_263, _G_or_289])
                self.considerError(lastError, None)
                return (_G_or_299, self.currentError)
            def _G_or_300():
                self._trace(' variable', (4274, 4283), self.input.position)
                _G_apply_301, lastError = self._apply(self.rule_variable, "variable", [])
                self.considerError(lastError, None)
                _locals['name'] = _G_apply_301
                _G_python_303, lastError = eval(self._G_expr_302, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_303, self.currentError)
            _G_or_304, lastError = self._or([_G_or_206, _G_or_212, _G_or_217, _G_or_226, _G_or_233, _G_or_243, _G_or_259, _G_or_261, _G_or_300])
            self.considerError(lastError, 'atom')
            return (_G_or_304, self.currentError)


        def rule_inside_url(self):
            _locals = {'self': self}
            self.locals['inside_url'] = _locals
            def _G_many_305():
                def _G_or_306():
                    self._trace('\n        interpolation', (4488, 4510), self.input.position)
                    _G_apply_307, lastError = self._apply(self.rule_interpolation, "interpolation", [])
                    self.considerError(lastError, None)
                    _locals['node'] = _G_apply_307
                    _G_python_308, lastError = eval(self._G_expr_153, self.globals, _locals), None
                    self.considerError(lastError, None)
                    return (_G_python_308, self.currentError)
                def _G_or_309():
                    self._trace(' variable', (4533, 4542), self.input.position)
                    _G_apply_310, lastError = self._apply(self.rule_variable, "variable", [])
                    self.considerError(lastError, None)
                    _locals['name'] = _G_apply_310
                    _G_python_311, lastError = eval(self._G_expr_302, self.globals, _locals), None
                    self.considerError(lastError, None)
                    return (_G_python_311, self.currentError)
                def _G_or_312():
                    def _G_many1_313():
                        def _G_or_314():
                            self._trace('\n            escape', (4577, 4596), self.input.position)
                            _G_apply_315, lastError = self._apply(self.rule_escape, "escape", [])
                            self.considerError(lastError, None)
                            return (_G_apply_315, self.currentError)
                        def _G_or_316():
                            self._trace(" '#'", (4610, 4614), self.input.position)
                            _G_exactly_317, lastError = self.exactly('#')
                            self.considerError(lastError, None)
                            def _G_not_318():
                                self._trace("'{'", (4616, 4619), self.input.position)
                                _G_exactly_319, lastError = self.exactly('{')
                                self.considerError(lastError, None)
                                return (_G_exactly_319, self.currentError)
                            _G_not_320, lastError = self._not(_G_not_318)
                            self.considerError(lastError, None)
                            return (_G_not_320, self.currentError)
                        def _G_or_321():
                            self._trace(' anything', (4633, 4642), self.input.position)
                            _G_apply_322, lastError = self._apply(self.rule_anything, "anything", [])
                            self.considerError(lastError, None)
                            _locals['ch'] = _G_apply_322
                            def _G_pred_323():
                                _G_python_325, lastError = eval(self._G_expr_324, self.globals, _locals), None
                                self.considerError(lastError, None)
                                return (_G_python_325, self.currentError)
                            _G_pred_326, lastError = self.pred(_G_pred_323)
                            self.considerError(lastError, None)
                            _G_python_328, lastError = eval(self._G_expr_327, self.globals, _locals), None
                            self.considerError(lastError, None)
                            return (_G_python_328, self.currentError)
                        _G_or_329, lastError = self._or([_G_or_314, _G_or_316, _G_or_321])
                        self.considerError(lastError, None)
                        return (_G_or_329, self.currentError)
                    _G_many1_330, lastError = self.many(_G_many1_313, _G_many1_313())
                    self.considerError(lastError, None)
                    _locals['s'] = _G_many1_330
                    _G_python_332, lastError = eval(self._G_expr_331, self.globals, _locals), None
                    self.considerError(lastError, None)
                    return (_G_python_332, self.currentError)
                def _G_or_333():
                    self._trace(" string_part(')')", (4760, 4777), self.input.position)
                    _G_python_334, lastError = (')'), None
                    self.considerError(lastError, None)
                    _G_apply_335, lastError = self._apply(self.rule_string_part, "string_part", [_G_python_334])
                    self.considerError(lastError, None)
                    _locals['s'] = _G_apply_335
                    _G_python_337, lastError = eval(self._G_expr_336, self.globals, _locals), None
                    self.considerError(lastError, None)
                    return (_G_python_337, self.currentError)
                _G_or_338, lastError = self._or([_G_or_306, _G_or_309, _G_or_312, _G_or_333])
                self.considerError(lastError, None)
                return (_G_or_338, self.currentError)
            _G_many_339, lastError = self.many(_G_many_305)
            self.considerError(lastError, 'inside_url')
            _locals['nodes'] = _G_many_339
            _G_python_341, lastError = eval(self._G_expr_340, self.globals, _locals), None
            self.considerError(lastError, 'inside_url')
            return (_G_python_341, self.currentError)


        def rule_string(self):
            _locals = {'self': self}
            self.locals['string'] = _locals
            def _G_or_342():
                self._trace('\n        \'"\'', (4880, 4892), self.input.position)
                _G_exactly_343, lastError = self.exactly('"')
                self.considerError(lastError, None)
                self._trace(' string_contents(\'"\' \'"\')', (4892, 4917), self.input.position)
                _G_python_344, lastError = ('"'), None
                self.considerError(lastError, None)
                _G_python_345, lastError = ('"'), None
                self.considerError(lastError, None)
                _G_apply_346, lastError = self._apply(self.rule_string_contents, "string_contents", [_G_python_344, _G_python_345])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_346
                self._trace(' \'"\'', (4922, 4926), self.input.position)
                _G_exactly_347, lastError = self.exactly('"')
                self.considerError(lastError, None)
                _G_python_348, lastError = eval(self._G_expr_153, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_348, self.currentError)
            def _G_or_349():
                self._trace(" '\\''", (4944, 4949), self.input.position)
                _G_exactly_350, lastError = self.exactly("'")
                self.considerError(lastError, None)
                self._trace(" string_contents('\\'' '\\'')", (4949, 4976), self.input.position)
                _G_python_351, lastError = ('\''), None
                self.considerError(lastError, None)
                _G_python_352, lastError = ('\''), None
                self.considerError(lastError, None)
                _G_apply_353, lastError = self._apply(self.rule_string_contents, "string_contents", [_G_python_351, _G_python_352])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_353
                self._trace(" '\\''", (4981, 4986), self.input.position)
                _G_exactly_354, lastError = self.exactly("'")
                self.considerError(lastError, None)
                _G_python_355, lastError = eval(self._G_expr_153, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_355, self.currentError)
            _G_or_356, lastError = self._or([_G_or_342, _G_or_349])
            self.considerError(lastError, 'string')
            return (_G_or_356, self.currentError)


        def rule_interpolation(self):
            _locals = {'self': self}
            self.locals['interpolation'] = _locals
            self._trace(" '#'", (5017, 5021), self.input.position)
            _G_exactly_357, lastError = self.exactly('#')
            self.considerError(lastError, 'interpolation')
            self._trace(" '{'", (5021, 5025), self.input.position)
            _G_exactly_358, lastError = self.exactly('{')
            self.considerError(lastError, 'interpolation')
            self._trace(' expression', (5025, 5036), self.input.position)
            _G_apply_359, lastError = self._apply(self.rule_expression, "expression", [])
            self.considerError(lastError, 'interpolation')
            _locals['node'] = _G_apply_359
            self._trace(" '}'", (5041, 5045), self.input.position)
            _G_exactly_360, lastError = self.exactly('}')
            self.considerError(lastError, 'interpolation')
            _G_python_361, lastError = eval(self._G_expr_153, self.globals, _locals), None
            self.considerError(lastError, 'interpolation')
            return (_G_python_361, self.currentError)


        def rule_string_contents(self):
            _locals = {'self': self}
            self.locals['string_contents'] = _locals
            _G_apply_362, lastError = self._apply(self.rule_anything, "anything", [])
            self.considerError(lastError, 'string_contents')
            _locals['end'] = _G_apply_362
            _G_apply_363, lastError = self._apply(self.rule_anything, "anything", [])
            self.considerError(lastError, 'string_contents')
            _locals['quotes'] = _G_apply_363
            def _G_many_364():
                def _G_or_365():
                    self._trace('\n        interpolation', (5091, 5113), self.input.position)
                    _G_apply_366, lastError = self._apply(self.rule_interpolation, "interpolation", [])
                    self.considerError(lastError, None)
                    _locals['node'] = _G_apply_366
                    _G_python_367, lastError = eval(self._G_expr_153, self.globals, _locals), None
                    self.considerError(lastError, None)
                    return (_G_python_367, self.currentError)
                def _G_or_368():
                    self._trace(' string_part(end)', (5136, 5153), self.input.position)
                    _G_python_370, lastError = eval(self._G_expr_369, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _G_apply_371, lastError = self._apply(self.rule_string_part, "string_part", [_G_python_370])
                    self.considerError(lastError, None)
                    _locals['s'] = _G_apply_371
                    _G_python_373, lastError = eval(self._G_expr_372, self.globals, _locals), None
                    self.considerError(lastError, None)
                    return (_G_python_373, self.currentError)
                _G_or_374, lastError = self._or([_G_or_365, _G_or_368])
                self.considerError(lastError, None)
                return (_G_or_374, self.currentError)
            _G_many_375, lastError = self.many(_G_many_364)
            self.considerError(lastError, 'string_contents')
            _locals['nodes'] = _G_many_375
            _G_python_377, lastError = eval(self._G_expr_376, self.globals, _locals), None
            self.considerError(lastError, 'string_contents')
            return (_G_python_377, self.currentError)


        def rule_string_part(self):
            _locals = {'self': self}
            self.locals['string_part'] = _locals
            _G_apply_378, lastError = self._apply(self.rule_anything, "anything", [])
            self.considerError(lastError, 'string_part')
            _locals['end'] = _G_apply_378
            def _G_consumedby_379():
                def _G_many1_380():
                    def _G_or_381():
                        self._trace("\n        '#'", (5271, 5283), self.input.position)
                        _G_exactly_382, lastError = self.exactly('#')
                        self.considerError(lastError, None)
                        def _G_not_383():
                            self._trace("'{'", (5285, 5288), self.input.position)
                            _G_exactly_384, lastError = self.exactly('{')
                            self.considerError(lastError, None)
                            return (_G_exactly_384, self.currentError)
                        _G_not_385, lastError = self._not(_G_not_383)
                        self.considerError(lastError, None)
                        return (_G_not_385, self.currentError)
                    def _G_or_386():
                        self._trace(' anything', (5298, 5307), self.input.position)
                        _G_apply_387, lastError = self._apply(self.rule_anything, "anything", [])
                        self.considerError(lastError, None)
                        _locals['ch'] = _G_apply_387
                        def _G_pred_388():
                            _G_python_390, lastError = eval(self._G_expr_389, self.globals, _locals), None
                            self.considerError(lastError, None)
                            return (_G_python_390, self.currentError)
                        _G_pred_391, lastError = self.pred(_G_pred_388)
                        self.considerError(lastError, None)
                        return (_G_pred_391, self.currentError)
                    _G_or_392, lastError = self._or([_G_or_381, _G_or_386])
                    self.considerError(lastError, None)
                    return (_G_or_392, self.currentError)
                _G_many1_393, lastError = self.many(_G_many1_380, _G_many1_380())
                self.considerError(lastError, None)
                return (_G_many1_393, self.currentError)
            _G_consumedby_394, lastError = self.consumedby(_G_consumedby_379)
            self.considerError(lastError, 'string_part')
            return (_G_consumedby_394, self.currentError)


        def rule_argspec(self):
            _locals = {'self': self}
            self.locals['argspec'] = _locals
            def _G_many_395():
                self._trace('\n        argspec_item', (5395, 5416), self.input.position)
                _G_apply_396, lastError = self._apply(self.rule_argspec_item, "argspec_item", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_396
                self._trace('\n        ows', (5421, 5433), self.input.position)
                _G_apply_397, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                self._trace(" ','", (5433, 5437), self.input.position)
                _G_exactly_398, lastError = self.exactly(',')
                self.considerError(lastError, None)
                self._trace(' ows', (5437, 5441), self.input.position)
                _G_apply_399, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                _G_python_400, lastError = eval(self._G_expr_153, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_400, self.currentError)
            _G_many_401, lastError = self.many(_G_many_395)
            self.considerError(lastError, 'argspec')
            _locals['nodes'] = _G_many_401
            def _G_optional_402():
                self._trace(' argspec_item', (5476, 5489), self.input.position)
                _G_apply_403, lastError = self._apply(self.rule_argspec_item, "argspec_item", [])
                self.considerError(lastError, None)
                _locals['tail'] = _G_apply_403
                self._trace(' ows', (5494, 5498), self.input.position)
                _G_apply_404, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                _G_python_406, lastError = eval(self._G_expr_405, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_406, self.currentError)
            def _G_optional_407():
                return (None, self.input.nullError())
            _G_or_408, lastError = self._or([_G_optional_402, _G_optional_407])
            self.considerError(lastError, 'argspec')
            _G_python_410, lastError = eval(self._G_expr_409, self.globals, _locals), None
            self.considerError(lastError, 'argspec')
            return (_G_python_410, self.currentError)


        def rule_argspec_item(self):
            _locals = {'self': self}
            self.locals['argspec_item'] = _locals
            self._trace('\n    ows', (5569, 5577), self.input.position)
            _G_apply_411, lastError = self._apply(self.rule_ows, "ows", [])
            self.considerError(lastError, 'argspec_item')
            def _G_optional_412():
                self._trace(' variable', (5593, 5602), self.input.position)
                _G_apply_413, lastError = self._apply(self.rule_variable, "variable", [])
                self.considerError(lastError, None)
                _locals['name'] = _G_apply_413
                self._trace(' ows', (5607, 5611), self.input.position)
                _G_apply_414, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                self._trace(" ':'", (5611, 5615), self.input.position)
                _G_exactly_415, lastError = self.exactly(':')
                self.considerError(lastError, None)
                self._trace(' ows', (5615, 5619), self.input.position)
                _G_apply_416, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                _G_python_418, lastError = eval(self._G_expr_417, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_418, self.currentError)
            def _G_optional_419():
                return (None, self.input.nullError())
            _G_or_420, lastError = self._or([_G_optional_412, _G_optional_419])
            self.considerError(lastError, 'argspec_item')
            _locals['name'] = _G_or_420
            self._trace('\n        spaced_list', (5635, 5655), self.input.position)
            _G_apply_421, lastError = self._apply(self.rule_spaced_list, "spaced_list", [])
            self.considerError(lastError, 'argspec_item')
            _locals['value'] = _G_apply_421
            _G_python_423, lastError = eval(self._G_expr_422, self.globals, _locals), None
            self.considerError(lastError, 'argspec_item')
            return (_G_python_423, self.currentError)


        _G_expr_327 = compile('ch', '<string>', 'eval')
        _G_expr_110 = compile('BinaryOp(operator.lt, node, operand)', '<string>', 'eval')
        _G_expr_196 = compile('UnaryOp(operator.neg, node)', '<string>', 'eval')
        _G_expr_336 = compile('Literal(String(s, quotes=None))', '<string>', 'eval')
        _G_expr_149 = compile('BinaryOp(operator.ne, node, operand)', '<string>', 'eval')
        _G_expr_100 = compile('NotOp(node)', '<string>', 'eval')
        _G_expr_405 = compile('nodes.append(tail)', '<string>', 'eval')
        _G_expr_210 = compile('Parentheses(node)', '<string>', 'eval')
        _G_expr_224 = compile("FunctionLiteral('url', s)", '<string>', 'eval')
        _G_expr_241 = compile('Literal(parse_bareword(word))', '<string>', 'eval')
        _G_expr_389 = compile("ch not in ('#', end)", '<string>', 'eval')
        _G_expr_169 = compile('BinaryOp(operator.sub, node, operand)', '<string>', 'eval')
        _G_expr_60 = compile('tail', '<string>', 'eval')
        _G_expr_91 = compile('AllOp(*[head] + tails) if tails else head', '<string>', 'eval')
        _G_expr_231 = compile('CallOp(name, args)', '<string>', 'eval')
        _G_expr_63 = compile('ListLiteral([head] + tails) if tails else head', '<string>', 'eval')
        _G_expr_302 = compile('Variable(name)', '<string>', 'eval')
        _G_expr_297 = compile('Literal(Color.from_rgb(\n                    int(red, 16) / 15.,\n                    int(green, 16) / 15.,\n                    int(blue, 16) / 15.,\n                    int(alpha or "f", 16) / 15.,\n                    original_literal="#" + red + green + blue + (alpha or \'\')))', '<string>', 'eval')
        _G_expr_153 = compile('node', '<string>', 'eval')
        _G_expr_422 = compile('(name, value)', '<string>', 'eval')
        _G_expr_201 = compile('UnaryOp(operator.pos, node)', '<string>', 'eval')
        _G_expr_141 = compile('BinaryOp(operator.eq, node, operand)', '<string>', 'eval')
        _G_expr_162 = compile('BinaryOp(operator.add, node, operand)', '<string>', 'eval')
        _G_expr_117 = compile('BinaryOp(operator.gt, node, operand)', '<string>', 'eval')
        _G_expr_369 = compile('end', '<string>', 'eval')
        _G_expr_324 = compile('ord(ch) > 32 and ch not in \' !"#$\\\'()\'', '<string>', 'eval')
        _G_expr_188 = compile('BinaryOp(operator.truediv, node, operand)', '<string>', 'eval')
        _G_expr_15 = compile('unichr(int(cp, 16))', '<string>', 'eval')
        _G_expr_125 = compile('BinaryOp(operator.le, node, operand)', '<string>', 'eval')
        _G_expr_71 = compile('ListLiteral([head] + tails, comma=False) if tails else head', '<string>', 'eval')
        _G_expr_287 = compile('Literal(Color.from_rgb(\n                    int(red, 16) / 255.,\n                    int(green, 16) / 255.,\n                    int(blue, 16) / 255.,\n                    int(alpha or "ff", 16) / 255.,\n                    original_literal="#" + red + green + blue + (alpha or \'\')))', '<string>', 'eval')
        _G_expr_181 = compile('BinaryOp(operator.mul, node, operand)', '<string>', 'eval')
        _G_expr_331 = compile("Literal(String(''.join(s), quotes=None))", '<string>', 'eval')
        _G_expr_257 = compile('Literal(Number(float(number), unit=unit))', '<string>', 'eval')
        _G_expr_409 = compile('ArgspecLiteral(nodes)', '<string>', 'eval')
        _G_expr_417 = compile('name', '<string>', 'eval')
        _G_expr_81 = compile('AnyOp(*[head] + tails) if tails else head', '<string>', 'eval')
        _G_expr_376 = compile('Interpolation(nodes, quotes=quotes)', '<string>', 'eval')
        _G_expr_372 = compile('Literal(String(s, quotes=quotes))', '<string>', 'eval')
        _G_expr_340 = compile('Interpolation(nodes, quotes=None)', '<string>', 'eval')
        _G_expr_133 = compile('BinaryOp(operator.ge, node, operand)', '<string>', 'eval')
    if Grammar.globals is not None:
        Grammar.globals = Grammar.globals.copy()
        Grammar.globals.update(ruleGlobals)
    else:
        Grammar.globals = ruleGlobals
    return Grammar