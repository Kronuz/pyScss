def createParserClass(GrammarBase, ruleGlobals):
    if ruleGlobals is None:
        ruleGlobals = {}
    class Grammar(GrammarBase):
        def rule_UNITS(self):
            _locals = {'self': self}
            self.locals['UNITS'] = _locals
            def _G_consumedby_1():
                def _G_or_2():
                    self._trace(" 'p'", (29, 33), self.input.position)
                    _G_exactly_3, lastError = self.exactly('p')
                    self.considerError(lastError, None)
                    self._trace(" 'x'", (33, 37), self.input.position)
                    _G_exactly_4, lastError = self.exactly('x')
                    self.considerError(lastError, None)
                    return (_G_exactly_4, self.currentError)
                def _G_or_5():
                    self._trace(" 'c'", (39, 43), self.input.position)
                    _G_exactly_6, lastError = self.exactly('c')
                    self.considerError(lastError, None)
                    self._trace(" 'm'", (43, 47), self.input.position)
                    _G_exactly_7, lastError = self.exactly('m')
                    self.considerError(lastError, None)
                    return (_G_exactly_7, self.currentError)
                def _G_or_8():
                    self._trace(" 'm'", (49, 53), self.input.position)
                    _G_exactly_9, lastError = self.exactly('m')
                    self.considerError(lastError, None)
                    self._trace(" 'm'", (53, 57), self.input.position)
                    _G_exactly_10, lastError = self.exactly('m')
                    self.considerError(lastError, None)
                    return (_G_exactly_10, self.currentError)
                def _G_or_11():
                    self._trace(" 'h'", (59, 63), self.input.position)
                    _G_exactly_12, lastError = self.exactly('h')
                    self.considerError(lastError, None)
                    self._trace(" 'z'", (63, 67), self.input.position)
                    _G_exactly_13, lastError = self.exactly('z')
                    self.considerError(lastError, None)
                    return (_G_exactly_13, self.currentError)
                def _G_or_14():
                    self._trace(" 'i'", (69, 73), self.input.position)
                    _G_exactly_15, lastError = self.exactly('i')
                    self.considerError(lastError, None)
                    self._trace(" 'n'", (73, 77), self.input.position)
                    _G_exactly_16, lastError = self.exactly('n')
                    self.considerError(lastError, None)
                    return (_G_exactly_16, self.currentError)
                def _G_or_17():
                    self._trace(" '%'", (79, 83), self.input.position)
                    _G_exactly_18, lastError = self.exactly('%')
                    self.considerError(lastError, None)
                    return (_G_exactly_18, self.currentError)
                _G_or_19, lastError = self._or([_G_or_2, _G_or_5, _G_or_8, _G_or_11, _G_or_14, _G_or_17])
                self.considerError(lastError, None)
                return (_G_or_19, self.currentError)
            _G_consumedby_20, lastError = self.consumedby(_G_consumedby_1)
            self.considerError(lastError, 'UNITS')
            return (_G_consumedby_20, self.currentError)


        def rule_escape(self):
            _locals = {'self': self}
            self.locals['escape'] = _locals
            self._trace(" '\\\\'", (506, 511), self.input.position)
            _G_exactly_21, lastError = self.exactly('\\')
            self.considerError(lastError, 'escape')
            def _G_or_22():
                self._trace("\n        '\\n'", (513, 526), self.input.position)
                _G_exactly_23, lastError = self.exactly('\n')
                self.considerError(lastError, None)
                _G_python_24, lastError = (''), None
                self.considerError(lastError, None)
                return (_G_python_24, self.currentError)
            def _G_or_25():
                def _G_consumedby_26():
                    def _G_repeat_27():
                        self._trace('hex', (602, 605), self.input.position)
                        _G_apply_28, lastError = self._apply(self.rule_hex, "hex", [])
                        self.considerError(lastError, None)
                        return (_G_apply_28, self.currentError)
                    _G_repeat_29, lastError = self.repeat(1, 6, _G_repeat_27)
                    self.considerError(lastError, None)
                    return (_G_repeat_29, self.currentError)
                _G_consumedby_30, lastError = self.consumedby(_G_consumedby_26)
                self.considerError(lastError, None)
                _locals['cp'] = _G_consumedby_30
                def _G_optional_31():
                    self._trace(' ws', (614, 617), self.input.position)
                    _G_apply_32, lastError = self._apply(self.rule_ws, "ws", [])
                    self.considerError(lastError, None)
                    return (_G_apply_32, self.currentError)
                def _G_optional_33():
                    return (None, self.input.nullError())
                _G_or_34, lastError = self._or([_G_optional_31, _G_optional_33])
                self.considerError(lastError, None)
                _G_python_36, lastError = eval(self._G_expr_35, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_36, self.currentError)
            def _G_or_37():
                self._trace(' anything', (758, 767), self.input.position)
                _G_apply_38, lastError = self._apply(self.rule_anything, "anything", [])
                self.considerError(lastError, None)
                return (_G_apply_38, self.currentError)
            _G_or_39, lastError = self._or([_G_or_22, _G_or_25, _G_or_37])
            self.considerError(lastError, 'escape')
            return (_G_or_39, self.currentError)


        def rule_identifier(self):
            _locals = {'self': self}
            self.locals['identifier'] = _locals
            def _G_consumedby_40():
                self._trace(' letterish', (800, 810), self.input.position)
                _G_apply_41, lastError = self._apply(self.rule_letterish, "letterish", [])
                self.considerError(lastError, None)
                def _G_many_42():
                    def _G_or_43():
                        self._trace('letterish', (812, 821), self.input.position)
                        _G_apply_44, lastError = self._apply(self.rule_letterish, "letterish", [])
                        self.considerError(lastError, None)
                        return (_G_apply_44, self.currentError)
                    def _G_or_45():
                        self._trace(' digit', (823, 829), self.input.position)
                        _G_apply_46, lastError = self._apply(self.rule_digit, "digit", [])
                        self.considerError(lastError, None)
                        return (_G_apply_46, self.currentError)
                    _G_or_47, lastError = self._or([_G_or_43, _G_or_45])
                    self.considerError(lastError, None)
                    return (_G_or_47, self.currentError)
                _G_many_48, lastError = self.many(_G_many_42)
                self.considerError(lastError, None)
                return (_G_many_48, self.currentError)
            _G_consumedby_49, lastError = self.consumedby(_G_consumedby_40)
            self.considerError(lastError, 'identifier')
            return (_G_consumedby_49, self.currentError)


        def rule_number(self):
            _locals = {'self': self}
            self.locals['number'] = _locals
            def _G_consumedby_50():
                def _G_or_51():
                    def _G_many1_52():
                        self._trace(' digit', (844, 850), self.input.position)
                        _G_apply_53, lastError = self._apply(self.rule_digit, "digit", [])
                        self.considerError(lastError, None)
                        return (_G_apply_53, self.currentError)
                    _G_many1_54, lastError = self.many(_G_many1_52, _G_many1_52())
                    self.considerError(lastError, None)
                    def _G_optional_55():
                        self._trace("'.'", (853, 856), self.input.position)
                        _G_exactly_56, lastError = self.exactly('.')
                        self.considerError(lastError, None)
                        def _G_many_57():
                            self._trace(' digit', (856, 862), self.input.position)
                            _G_apply_58, lastError = self._apply(self.rule_digit, "digit", [])
                            self.considerError(lastError, None)
                            return (_G_apply_58, self.currentError)
                        _G_many_59, lastError = self.many(_G_many_57)
                        self.considerError(lastError, None)
                        return (_G_many_59, self.currentError)
                    def _G_optional_60():
                        return (None, self.input.nullError())
                    _G_or_61, lastError = self._or([_G_optional_55, _G_optional_60])
                    self.considerError(lastError, None)
                    return (_G_or_61, self.currentError)
                def _G_or_62():
                    self._trace(" '.'", (867, 871), self.input.position)
                    _G_exactly_63, lastError = self.exactly('.')
                    self.considerError(lastError, None)
                    def _G_many1_64():
                        self._trace(' digit', (871, 877), self.input.position)
                        _G_apply_65, lastError = self._apply(self.rule_digit, "digit", [])
                        self.considerError(lastError, None)
                        return (_G_apply_65, self.currentError)
                    _G_many1_66, lastError = self.many(_G_many1_64, _G_many1_64())
                    self.considerError(lastError, None)
                    return (_G_many1_66, self.currentError)
                _G_or_67, lastError = self._or([_G_or_51, _G_or_62])
                self.considerError(lastError, None)
                return (_G_or_67, self.currentError)
            _G_consumedby_68, lastError = self.consumedby(_G_consumedby_50)
            self.considerError(lastError, 'number')
            return (_G_consumedby_68, self.currentError)


        def rule_variable(self):
            _locals = {'self': self}
            self.locals['variable'] = _locals
            def _G_consumedby_69():
                self._trace(" '$'", (893, 897), self.input.position)
                _G_exactly_70, lastError = self.exactly('$')
                self.considerError(lastError, None)
                self._trace(' identifier', (897, 908), self.input.position)
                _G_apply_71, lastError = self._apply(self.rule_identifier, "identifier", [])
                self.considerError(lastError, None)
                return (_G_apply_71, self.currentError)
            _G_consumedby_72, lastError = self.consumedby(_G_consumedby_69)
            self.considerError(lastError, 'variable')
            return (_G_consumedby_72, self.currentError)


        def rule_expression(self):
            _locals = {'self': self}
            self.locals['expression'] = _locals
            self._trace(' comma_list', (938, 949), self.input.position)
            _G_apply_73, lastError = self._apply(self.rule_comma_list, "comma_list", [])
            self.considerError(lastError, 'expression')
            return (_G_apply_73, self.currentError)


        def rule_comma_list(self):
            _locals = {'self': self}
            self.locals['comma_list'] = _locals
            self._trace(' spaced_list', (963, 975), self.input.position)
            _G_apply_74, lastError = self._apply(self.rule_spaced_list, "spaced_list", [])
            self.considerError(lastError, 'comma_list')
            _locals['head'] = _G_apply_74
            def _G_many_75():
                self._trace('\n        ows', (982, 994), self.input.position)
                _G_apply_76, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                self._trace(" ','", (994, 998), self.input.position)
                _G_exactly_77, lastError = self.exactly(',')
                self.considerError(lastError, None)
                self._trace(' ows', (998, 1002), self.input.position)
                _G_apply_78, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                self._trace('\n        spaced_list', (1002, 1022), self.input.position)
                _G_apply_79, lastError = self._apply(self.rule_spaced_list, "spaced_list", [])
                self.considerError(lastError, None)
                _locals['tail'] = _G_apply_79
                _G_python_81, lastError = eval(self._G_expr_80, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_81, self.currentError)
            _G_many_82, lastError = self.many(_G_many_75)
            self.considerError(lastError, 'comma_list')
            _locals['tails'] = _G_many_82
            _G_python_84, lastError = eval(self._G_expr_83, self.globals, _locals), None
            self.considerError(lastError, 'comma_list')
            return (_G_python_84, self.currentError)


        def rule_spaced_list(self):
            _locals = {'self': self}
            self.locals['spaced_list'] = _locals
            self._trace(' single_expression', (1113, 1131), self.input.position)
            _G_apply_85, lastError = self._apply(self.rule_single_expression, "single_expression", [])
            self.considerError(lastError, 'spaced_list')
            _locals['head'] = _G_apply_85
            def _G_many_86():
                self._trace('\n        ws', (1138, 1149), self.input.position)
                _G_apply_87, lastError = self._apply(self.rule_ws, "ws", [])
                self.considerError(lastError, None)
                self._trace('\n        single_expression', (1149, 1175), self.input.position)
                _G_apply_88, lastError = self._apply(self.rule_single_expression, "single_expression", [])
                self.considerError(lastError, None)
                _locals['tail'] = _G_apply_88
                _G_python_89, lastError = eval(self._G_expr_80, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_89, self.currentError)
            _G_many_90, lastError = self.many(_G_many_86)
            self.considerError(lastError, 'spaced_list')
            _locals['tails'] = _G_many_90
            _G_python_92, lastError = eval(self._G_expr_91, self.globals, _locals), None
            self.considerError(lastError, 'spaced_list')
            return (_G_python_92, self.currentError)


        def rule_single_expression(self):
            _locals = {'self': self}
            self.locals['single_expression'] = _locals
            self._trace(' or_test', (1286, 1294), self.input.position)
            _G_apply_93, lastError = self._apply(self.rule_or_test, "or_test", [])
            self.considerError(lastError, 'single_expression')
            return (_G_apply_93, self.currentError)


        def rule_or_test(self):
            _locals = {'self': self}
            self.locals['or_test'] = _locals
            self._trace(' and_test', (1305, 1314), self.input.position)
            _G_apply_94, lastError = self._apply(self.rule_and_test, "and_test", [])
            self.considerError(lastError, 'or_test')
            _locals['head'] = _G_apply_94
            def _G_many_95():
                self._trace("\n        'o'", (1321, 1333), self.input.position)
                _G_exactly_96, lastError = self.exactly('o')
                self.considerError(lastError, None)
                self._trace(" 'r'", (1333, 1337), self.input.position)
                _G_exactly_97, lastError = self.exactly('r')
                self.considerError(lastError, None)
                self._trace('\n        and_test', (1337, 1354), self.input.position)
                _G_apply_98, lastError = self._apply(self.rule_and_test, "and_test", [])
                self.considerError(lastError, None)
                _locals['tail'] = _G_apply_98
                _G_python_99, lastError = eval(self._G_expr_80, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_99, self.currentError)
            _G_many_100, lastError = self.many(_G_many_95)
            self.considerError(lastError, 'or_test')
            _locals['tails'] = _G_many_100
            _G_python_102, lastError = eval(self._G_expr_101, self.globals, _locals), None
            self.considerError(lastError, 'or_test')
            return (_G_python_102, self.currentError)


        def rule_and_test(self):
            _locals = {'self': self}
            self.locals['and_test'] = _locals
            self._trace(' not_test', (1437, 1446), self.input.position)
            _G_apply_103, lastError = self._apply(self.rule_not_test, "not_test", [])
            self.considerError(lastError, 'and_test')
            _locals['head'] = _G_apply_103
            def _G_many_104():
                self._trace("\n        'a'", (1453, 1465), self.input.position)
                _G_exactly_105, lastError = self.exactly('a')
                self.considerError(lastError, None)
                self._trace(" 'n'", (1465, 1469), self.input.position)
                _G_exactly_106, lastError = self.exactly('n')
                self.considerError(lastError, None)
                self._trace(" 'd'", (1469, 1473), self.input.position)
                _G_exactly_107, lastError = self.exactly('d')
                self.considerError(lastError, None)
                self._trace('\n        not_test', (1473, 1490), self.input.position)
                _G_apply_108, lastError = self._apply(self.rule_not_test, "not_test", [])
                self.considerError(lastError, None)
                _locals['tail'] = _G_apply_108
                _G_python_109, lastError = eval(self._G_expr_80, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_109, self.currentError)
            _G_many_110, lastError = self.many(_G_many_104)
            self.considerError(lastError, 'and_test')
            _locals['tails'] = _G_many_110
            _G_python_112, lastError = eval(self._G_expr_111, self.globals, _locals), None
            self.considerError(lastError, 'and_test')
            return (_G_python_112, self.currentError)


        def rule_not_test(self):
            _locals = {'self': self}
            self.locals['not_test'] = _locals
            def _G_or_113():
                self._trace(' comparison', (1573, 1584), self.input.position)
                _G_apply_114, lastError = self._apply(self.rule_comparison, "comparison", [])
                self.considerError(lastError, None)
                return (_G_apply_114, self.currentError)
            def _G_or_115():
                self._trace(" 'n'", (1588, 1592), self.input.position)
                _G_exactly_116, lastError = self.exactly('n')
                self.considerError(lastError, None)
                self._trace(" 'o'", (1592, 1596), self.input.position)
                _G_exactly_117, lastError = self.exactly('o')
                self.considerError(lastError, None)
                self._trace(" 't'", (1596, 1600), self.input.position)
                _G_exactly_118, lastError = self.exactly('t')
                self.considerError(lastError, None)
                self._trace(' not_test', (1600, 1609), self.input.position)
                _G_apply_119, lastError = self._apply(self.rule_not_test, "not_test", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_119
                _G_python_121, lastError = eval(self._G_expr_120, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_121, self.currentError)
            _G_or_122, lastError = self._or([_G_or_113, _G_or_115])
            self.considerError(lastError, 'not_test')
            return (_G_or_122, self.currentError)


        def rule_comparison(self):
            _locals = {'self': self}
            self.locals['comparison'] = _locals
            self._trace(' add_expr', (1645, 1654), self.input.position)
            _G_apply_123, lastError = self._apply(self.rule_add_expr, "add_expr", [])
            self.considerError(lastError, 'comparison')
            _locals['node'] = _G_apply_123
            def _G_many_124():
                def _G_or_125():
                    self._trace('\n        ows', (1661, 1673), self.input.position)
                    _G_apply_126, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '<'", (1673, 1677), self.input.position)
                    _G_exactly_127, lastError = self.exactly('<')
                    self.considerError(lastError, None)
                    self._trace(' ows', (1677, 1681), self.input.position)
                    _G_apply_128, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (1681, 1690), self.input.position)
                    _G_apply_129, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_129
                    _G_python_131, lastError = eval(self._G_expr_130, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_131
                    return (_G_python_131, self.currentError)
                def _G_or_132():
                    self._trace(' ows', (1755, 1759), self.input.position)
                    _G_apply_133, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '>'", (1759, 1763), self.input.position)
                    _G_exactly_134, lastError = self.exactly('>')
                    self.considerError(lastError, None)
                    self._trace(' ows', (1763, 1767), self.input.position)
                    _G_apply_135, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (1767, 1776), self.input.position)
                    _G_apply_136, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_136
                    _G_python_138, lastError = eval(self._G_expr_137, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_138
                    return (_G_python_138, self.currentError)
                def _G_or_139():
                    self._trace(' ows', (1841, 1845), self.input.position)
                    _G_apply_140, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '<'", (1845, 1849), self.input.position)
                    _G_exactly_141, lastError = self.exactly('<')
                    self.considerError(lastError, None)
                    self._trace(" '='", (1849, 1853), self.input.position)
                    _G_exactly_142, lastError = self.exactly('=')
                    self.considerError(lastError, None)
                    self._trace(' ows', (1853, 1857), self.input.position)
                    _G_apply_143, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (1857, 1866), self.input.position)
                    _G_apply_144, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_144
                    _G_python_146, lastError = eval(self._G_expr_145, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_146
                    return (_G_python_146, self.currentError)
                def _G_or_147():
                    self._trace(' ows', (1931, 1935), self.input.position)
                    _G_apply_148, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '>'", (1935, 1939), self.input.position)
                    _G_exactly_149, lastError = self.exactly('>')
                    self.considerError(lastError, None)
                    self._trace(" '='", (1939, 1943), self.input.position)
                    _G_exactly_150, lastError = self.exactly('=')
                    self.considerError(lastError, None)
                    self._trace(' ows', (1943, 1947), self.input.position)
                    _G_apply_151, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (1947, 1956), self.input.position)
                    _G_apply_152, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_152
                    _G_python_154, lastError = eval(self._G_expr_153, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_154
                    return (_G_python_154, self.currentError)
                def _G_or_155():
                    self._trace(' ows', (2021, 2025), self.input.position)
                    _G_apply_156, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '='", (2025, 2029), self.input.position)
                    _G_exactly_157, lastError = self.exactly('=')
                    self.considerError(lastError, None)
                    self._trace(" '='", (2029, 2033), self.input.position)
                    _G_exactly_158, lastError = self.exactly('=')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2033, 2037), self.input.position)
                    _G_apply_159, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (2037, 2046), self.input.position)
                    _G_apply_160, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_160
                    _G_python_162, lastError = eval(self._G_expr_161, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_162
                    return (_G_python_162, self.currentError)
                def _G_or_163():
                    self._trace(' ows', (2111, 2115), self.input.position)
                    _G_apply_164, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '!'", (2115, 2119), self.input.position)
                    _G_exactly_165, lastError = self.exactly('!')
                    self.considerError(lastError, None)
                    self._trace(" '='", (2119, 2123), self.input.position)
                    _G_exactly_166, lastError = self.exactly('=')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2123, 2127), self.input.position)
                    _G_apply_167, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' add_expr', (2127, 2136), self.input.position)
                    _G_apply_168, lastError = self._apply(self.rule_add_expr, "add_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_168
                    _G_python_170, lastError = eval(self._G_expr_169, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_170
                    return (_G_python_170, self.currentError)
                _G_or_171, lastError = self._or([_G_or_125, _G_or_132, _G_or_139, _G_or_147, _G_or_155, _G_or_163])
                self.considerError(lastError, None)
                return (_G_or_171, self.currentError)
            _G_many_172, lastError = self.many(_G_many_124)
            self.considerError(lastError, 'comparison')
            _G_python_174, lastError = eval(self._G_expr_173, self.globals, _locals), None
            self.considerError(lastError, 'comparison')
            return (_G_python_174, self.currentError)


        def rule_add_expr(self):
            _locals = {'self': self}
            self.locals['add_expr'] = _locals
            self._trace(' mult_expr', (2218, 2228), self.input.position)
            _G_apply_175, lastError = self._apply(self.rule_mult_expr, "mult_expr", [])
            self.considerError(lastError, 'add_expr')
            _locals['node'] = _G_apply_175
            def _G_many_176():
                def _G_or_177():
                    self._trace('\n        ows', (2235, 2247), self.input.position)
                    _G_apply_178, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '+'", (2247, 2251), self.input.position)
                    _G_exactly_179, lastError = self.exactly('+')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2251, 2255), self.input.position)
                    _G_apply_180, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' mult_expr', (2255, 2265), self.input.position)
                    _G_apply_181, lastError = self._apply(self.rule_mult_expr, "mult_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_181
                    _G_python_183, lastError = eval(self._G_expr_182, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_183
                    return (_G_python_183, self.currentError)
                def _G_or_184():
                    self._trace(' ows', (2331, 2335), self.input.position)
                    _G_apply_185, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '-'", (2335, 2339), self.input.position)
                    _G_exactly_186, lastError = self.exactly('-')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2339, 2343), self.input.position)
                    _G_apply_187, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' mult_expr', (2343, 2353), self.input.position)
                    _G_apply_188, lastError = self._apply(self.rule_mult_expr, "mult_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_188
                    _G_python_190, lastError = eval(self._G_expr_189, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_190
                    return (_G_python_190, self.currentError)
                _G_or_191, lastError = self._or([_G_or_177, _G_or_184])
                self.considerError(lastError, None)
                return (_G_or_191, self.currentError)
            _G_many_192, lastError = self.many(_G_many_176)
            self.considerError(lastError, 'add_expr')
            _G_python_193, lastError = eval(self._G_expr_173, self.globals, _locals), None
            self.considerError(lastError, 'add_expr')
            return (_G_python_193, self.currentError)


        def rule_mult_expr(self):
            _locals = {'self': self}
            self.locals['mult_expr'] = _locals
            self._trace(' unary_expr', (2437, 2448), self.input.position)
            _G_apply_194, lastError = self._apply(self.rule_unary_expr, "unary_expr", [])
            self.considerError(lastError, 'mult_expr')
            _locals['node'] = _G_apply_194
            def _G_many_195():
                def _G_or_196():
                    self._trace('\n        ows', (2455, 2467), self.input.position)
                    _G_apply_197, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '*'", (2467, 2471), self.input.position)
                    _G_exactly_198, lastError = self.exactly('*')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2471, 2475), self.input.position)
                    _G_apply_199, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' unary_expr', (2475, 2486), self.input.position)
                    _G_apply_200, lastError = self._apply(self.rule_unary_expr, "unary_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_200
                    _G_python_202, lastError = eval(self._G_expr_201, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_202
                    return (_G_python_202, self.currentError)
                def _G_or_203():
                    self._trace(' ows', (2552, 2556), self.input.position)
                    _G_apply_204, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(" '/'", (2556, 2560), self.input.position)
                    _G_exactly_205, lastError = self.exactly('/')
                    self.considerError(lastError, None)
                    self._trace(' ows', (2560, 2564), self.input.position)
                    _G_apply_206, lastError = self._apply(self.rule_ows, "ows", [])
                    self.considerError(lastError, None)
                    self._trace(' unary_expr', (2564, 2575), self.input.position)
                    _G_apply_207, lastError = self._apply(self.rule_unary_expr, "unary_expr", [])
                    self.considerError(lastError, None)
                    _locals['operand'] = _G_apply_207
                    _G_python_209, lastError = eval(self._G_expr_208, self.globals, _locals), None
                    self.considerError(lastError, None)
                    _locals['node'] = _G_python_209
                    return (_G_python_209, self.currentError)
                _G_or_210, lastError = self._or([_G_or_196, _G_or_203])
                self.considerError(lastError, None)
                return (_G_or_210, self.currentError)
            _G_many_211, lastError = self.many(_G_many_195)
            self.considerError(lastError, 'mult_expr')
            _G_python_212, lastError = eval(self._G_expr_173, self.globals, _locals), None
            self.considerError(lastError, 'mult_expr')
            return (_G_python_212, self.currentError)


        def rule_unary_expr(self):
            _locals = {'self': self}
            self.locals['unary_expr'] = _locals
            def _G_or_213():
                self._trace("\n        '-'", (2662, 2674), self.input.position)
                _G_exactly_214, lastError = self.exactly('-')
                self.considerError(lastError, None)
                self._trace(' unary_expr', (2674, 2685), self.input.position)
                _G_apply_215, lastError = self._apply(self.rule_unary_expr, "unary_expr", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_215
                _G_python_217, lastError = eval(self._G_expr_216, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_217, self.currentError)
            def _G_or_218():
                self._trace(" '+'", (2731, 2735), self.input.position)
                _G_exactly_219, lastError = self.exactly('+')
                self.considerError(lastError, None)
                self._trace(' unary_expr', (2735, 2746), self.input.position)
                _G_apply_220, lastError = self._apply(self.rule_unary_expr, "unary_expr", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_220
                _G_python_222, lastError = eval(self._G_expr_221, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_222, self.currentError)
            def _G_or_223():
                self._trace(' atom', (2792, 2797), self.input.position)
                _G_apply_224, lastError = self._apply(self.rule_atom, "atom", [])
                self.considerError(lastError, None)
                return (_G_apply_224, self.currentError)
            _G_or_225, lastError = self._or([_G_or_213, _G_or_218, _G_or_223])
            self.considerError(lastError, 'unary_expr')
            return (_G_or_225, self.currentError)


        def rule_atom(self):
            _locals = {'self': self}
            self.locals['atom'] = _locals
            def _G_or_226():
                self._trace("\n        # Parenthesized expression\n        '('", (2813, 2860), self.input.position)
                _G_exactly_227, lastError = self.exactly('(')
                self.considerError(lastError, None)
                self._trace(' comma_list', (2860, 2871), self.input.position)
                _G_apply_228, lastError = self._apply(self.rule_comma_list, "comma_list", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_228
                self._trace(" ')'", (2876, 2880), self.input.position)
                _G_exactly_229, lastError = self.exactly(')')
                self.considerError(lastError, None)
                _G_python_230, lastError = eval(self._G_expr_173, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_230, self.currentError)
            def _G_or_231():
                self._trace(" '['", (2978, 2982), self.input.position)
                _G_exactly_232, lastError = self.exactly('[')
                self.considerError(lastError, None)
                self._trace(' comma_list', (2982, 2993), self.input.position)
                _G_apply_233, lastError = self._apply(self.rule_comma_list, "comma_list", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_233
                self._trace(" ']'", (2998, 3002), self.input.position)
                _G_exactly_234, lastError = self.exactly(']')
                self.considerError(lastError, None)
                _G_python_235, lastError = eval(self._G_expr_173, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_235, self.currentError)
            def _G_or_236():
                self._trace(" 'u'", (3043, 3047), self.input.position)
                _G_exactly_237, lastError = self.exactly('u')
                self.considerError(lastError, None)
                self._trace(" 'r'", (3047, 3051), self.input.position)
                _G_exactly_238, lastError = self.exactly('r')
                self.considerError(lastError, None)
                self._trace(" 'l'", (3051, 3055), self.input.position)
                _G_exactly_239, lastError = self.exactly('l')
                self.considerError(lastError, None)
                self._trace(" '('", (3055, 3059), self.input.position)
                _G_exactly_240, lastError = self.exactly('(')
                self.considerError(lastError, None)
                def _G_or_241():
                    self._trace('string', (3061, 3067), self.input.position)
                    _G_apply_242, lastError = self._apply(self.rule_string, "string", [])
                    self.considerError(lastError, None)
                    return (_G_apply_242, self.currentError)
                def _G_or_243():
                    self._trace(' uri', (3069, 3073), self.input.position)
                    _G_apply_244, lastError = self._apply(self.rule_uri, "uri", [])
                    self.considerError(lastError, None)
                    return (_G_apply_244, self.currentError)
                _G_or_245, lastError = self._or([_G_or_241, _G_or_243])
                self.considerError(lastError, None)
                _locals['s'] = _G_or_245
                self._trace(" ')'", (3076, 3080), self.input.position)
                _G_exactly_246, lastError = self.exactly(')')
                self.considerError(lastError, None)
                _G_python_248, lastError = eval(self._G_expr_247, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_248, self.currentError)
            def _G_or_249():
                self._trace(' identifier', (3144, 3155), self.input.position)
                _G_apply_250, lastError = self._apply(self.rule_identifier, "identifier", [])
                self.considerError(lastError, None)
                _locals['name'] = _G_apply_250
                self._trace(" '('", (3160, 3164), self.input.position)
                _G_exactly_251, lastError = self.exactly('(')
                self.considerError(lastError, None)
                self._trace(' argspec', (3164, 3172), self.input.position)
                _G_apply_252, lastError = self._apply(self.rule_argspec, "argspec", [])
                self.considerError(lastError, None)
                _locals['args'] = _G_apply_252
                self._trace(" ')'", (3177, 3181), self.input.position)
                _G_exactly_253, lastError = self.exactly(')')
                self.considerError(lastError, None)
                _G_python_255, lastError = eval(self._G_expr_254, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_255, self.currentError)
            def _G_or_256():
                def _G_consumedby_257():
                    def _G_optional_258():
                        self._trace(" '!'", (3235, 3239), self.input.position)
                        _G_exactly_259, lastError = self.exactly('!')
                        self.considerError(lastError, None)
                        return (_G_exactly_259, self.currentError)
                    def _G_optional_260():
                        return (None, self.input.nullError())
                    _G_or_261, lastError = self._or([_G_optional_258, _G_optional_260])
                    self.considerError(lastError, None)
                    self._trace(' identifier', (3240, 3251), self.input.position)
                    _G_apply_262, lastError = self._apply(self.rule_identifier, "identifier", [])
                    self.considerError(lastError, None)
                    return (_G_apply_262, self.currentError)
                _G_consumedby_263, lastError = self.consumedby(_G_consumedby_257)
                self.considerError(lastError, None)
                _locals['word'] = _G_consumedby_263
                _G_python_265, lastError = eval(self._G_expr_264, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_265, self.currentError)
            def _G_or_266():
                self._trace(' number', (3319, 3326), self.input.position)
                _G_apply_267, lastError = self._apply(self.rule_number, "number", [])
                self.considerError(lastError, None)
                _locals['number'] = _G_apply_267
                def _G_optional_268():
                    def _G_consumedby_269():
                        def _G_or_270():
                            self._trace(" '%'", (3335, 3339), self.input.position)
                            _G_exactly_271, lastError = self.exactly('%')
                            self.considerError(lastError, None)
                            return (_G_exactly_271, self.currentError)
                        def _G_or_272():
                            def _G_many1_273():
                                self._trace(' letter', (3341, 3348), self.input.position)
                                _G_apply_274, lastError = self._apply(self.rule_letter, "letter", [])
                                self.considerError(lastError, None)
                                return (_G_apply_274, self.currentError)
                            _G_many1_275, lastError = self.many(_G_many1_273, _G_many1_273())
                            self.considerError(lastError, None)
                            return (_G_many1_275, self.currentError)
                        _G_or_276, lastError = self._or([_G_or_270, _G_or_272])
                        self.considerError(lastError, None)
                        return (_G_or_276, self.currentError)
                    _G_consumedby_277, lastError = self.consumedby(_G_consumedby_269)
                    self.considerError(lastError, None)
                    return (_G_consumedby_277, self.currentError)
                def _G_optional_278():
                    return (None, self.input.nullError())
                _G_or_279, lastError = self._or([_G_optional_268, _G_optional_278])
                self.considerError(lastError, None)
                _locals['unit'] = _G_or_279
                _G_python_281, lastError = eval(self._G_expr_280, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_281, self.currentError)
            def _G_or_282():
                self._trace(' string', (3435, 3442), self.input.position)
                _G_apply_283, lastError = self._apply(self.rule_string, "string", [])
                self.considerError(lastError, None)
                return (_G_apply_283, self.currentError)
            def _G_or_284():
                def _G_consumedby_285():
                    self._trace(" '#'", (3538, 3542), self.input.position)
                    _G_exactly_286, lastError = self.exactly('#')
                    self.considerError(lastError, None)
                    def _G_or_287():
                        def _G_consumedby_288():
                            def _G_repeat_289():
                                self._trace('hex', (3558, 3561), self.input.position)
                                _G_apply_290, lastError = self._apply(self.rule_hex, "hex", [])
                                self.considerError(lastError, None)
                                return (_G_apply_290, self.currentError)
                            _G_repeat_291, lastError = self.repeat(2, 2, _G_repeat_289)
                            self.considerError(lastError, None)
                            return (_G_repeat_291, self.currentError)
                        _G_consumedby_292, lastError = self.consumedby(_G_consumedby_288)
                        self.considerError(lastError, None)
                        _locals['red'] = _G_consumedby_292
                        def _G_consumedby_293():
                            def _G_repeat_294():
                                self._trace('hex', (3571, 3574), self.input.position)
                                _G_apply_295, lastError = self._apply(self.rule_hex, "hex", [])
                                self.considerError(lastError, None)
                                return (_G_apply_295, self.currentError)
                            _G_repeat_296, lastError = self.repeat(2, 2, _G_repeat_294)
                            self.considerError(lastError, None)
                            return (_G_repeat_296, self.currentError)
                        _G_consumedby_297, lastError = self.consumedby(_G_consumedby_293)
                        self.considerError(lastError, None)
                        _locals['green'] = _G_consumedby_297
                        def _G_consumedby_298():
                            def _G_repeat_299():
                                self._trace('hex', (3586, 3589), self.input.position)
                                _G_apply_300, lastError = self._apply(self.rule_hex, "hex", [])
                                self.considerError(lastError, None)
                                return (_G_apply_300, self.currentError)
                            _G_repeat_301, lastError = self.repeat(2, 2, _G_repeat_299)
                            self.considerError(lastError, None)
                            return (_G_repeat_301, self.currentError)
                        _G_consumedby_302, lastError = self.consumedby(_G_consumedby_298)
                        self.considerError(lastError, None)
                        _locals['blue'] = _G_consumedby_302
                        return (_G_consumedby_302, self.currentError)
                    def _G_or_303():
                        self._trace(' hex', (3727, 3731), self.input.position)
                        _G_apply_304, lastError = self._apply(self.rule_hex, "hex", [])
                        self.considerError(lastError, None)
                        _locals['red'] = _G_apply_304
                        self._trace(' hex', (3735, 3739), self.input.position)
                        _G_apply_305, lastError = self._apply(self.rule_hex, "hex", [])
                        self.considerError(lastError, None)
                        _locals['green'] = _G_apply_305
                        self._trace(' hex', (3745, 3749), self.input.position)
                        _G_apply_306, lastError = self._apply(self.rule_hex, "hex", [])
                        self.considerError(lastError, None)
                        _locals['blue'] = _G_apply_306
                        return (_G_apply_306, self.currentError)
                    _G_or_307, lastError = self._or([_G_or_287, _G_or_303])
                    self.considerError(lastError, None)
                    return (_G_or_307, self.currentError)
                _G_consumedby_308, lastError = self.consumedby(_G_consumedby_285)
                self.considerError(lastError, None)
                _locals['color'] = _G_consumedby_308
                _G_python_310, lastError = eval(self._G_expr_309, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_310, self.currentError)
            def _G_or_311():
                self._trace(' variable', (3957, 3966), self.input.position)
                _G_apply_312, lastError = self._apply(self.rule_variable, "variable", [])
                self.considerError(lastError, None)
                _locals['name'] = _G_apply_312
                _G_python_314, lastError = eval(self._G_expr_313, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_314, self.currentError)
            _G_or_315, lastError = self._or([_G_or_226, _G_or_231, _G_or_236, _G_or_249, _G_or_256, _G_or_266, _G_or_282, _G_or_284, _G_or_311])
            self.considerError(lastError, 'atom')
            return (_G_or_315, self.currentError)


        def rule_uri(self):
            _locals = {'self': self}
            self.locals['uri'] = _locals
            def _G_many_316():
                def _G_or_317():
                    self._trace('\n        escape', (4164, 4179), self.input.position)
                    _G_apply_318, lastError = self._apply(self.rule_escape, "escape", [])
                    self.considerError(lastError, None)
                    return (_G_apply_318, self.currentError)
                def _G_or_319():
                    self._trace(' anything', (4189, 4198), self.input.position)
                    _G_apply_320, lastError = self._apply(self.rule_anything, "anything", [])
                    self.considerError(lastError, None)
                    _locals['ch'] = _G_apply_320
                    def _G_pred_321():
                        _G_python_323, lastError = eval(self._G_expr_322, self.globals, _locals), None
                        self.considerError(lastError, None)
                        return (_G_python_323, self.currentError)
                    _G_pred_324, lastError = self.pred(_G_pred_321)
                    self.considerError(lastError, None)
                    _G_python_326, lastError = eval(self._G_expr_325, self.globals, _locals), None
                    self.considerError(lastError, None)
                    return (_G_python_326, self.currentError)
                _G_or_327, lastError = self._or([_G_or_317, _G_or_319])
                self.considerError(lastError, None)
                return (_G_or_327, self.currentError)
            _G_many_328, lastError = self.many(_G_many_316)
            self.considerError(lastError, 'uri')
            _locals['s'] = _G_many_328
            _G_python_330, lastError = eval(self._G_expr_329, self.globals, _locals), None
            self.considerError(lastError, 'uri')
            return (_G_python_330, self.currentError)


        def rule_string(self):
            _locals = {'self': self}
            self.locals['string'] = _locals
            def _G_or_331():
                self._trace('\n        \'"\'', (4313, 4325), self.input.position)
                _G_exactly_332, lastError = self.exactly('"')
                self.considerError(lastError, None)
                self._trace(' string_contents(\'"\')', (4325, 4346), self.input.position)
                _G_python_333, lastError = ('"'), None
                self.considerError(lastError, None)
                _G_apply_334, lastError = self._apply(self.rule_string_contents, "string_contents", [_G_python_333])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_334
                self._trace(' \'"\'', (4351, 4355), self.input.position)
                _G_exactly_335, lastError = self.exactly('"')
                self.considerError(lastError, None)
                _G_python_336, lastError = eval(self._G_expr_173, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_336, self.currentError)
            def _G_or_337():
                self._trace(" '\\''", (4373, 4378), self.input.position)
                _G_exactly_338, lastError = self.exactly("'")
                self.considerError(lastError, None)
                self._trace(" string_contents('\\'')", (4378, 4400), self.input.position)
                _G_python_339, lastError = ('\''), None
                self.considerError(lastError, None)
                _G_apply_340, lastError = self._apply(self.rule_string_contents, "string_contents", [_G_python_339])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_340
                self._trace(" '\\''", (4405, 4410), self.input.position)
                _G_exactly_341, lastError = self.exactly("'")
                self.considerError(lastError, None)
                _G_python_342, lastError = eval(self._G_expr_173, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_342, self.currentError)
            _G_or_343, lastError = self._or([_G_or_331, _G_or_337])
            self.considerError(lastError, 'string')
            return (_G_or_343, self.currentError)


        def rule_interpolation(self):
            _locals = {'self': self}
            self.locals['interpolation'] = _locals
            self._trace(" '#'", (4441, 4445), self.input.position)
            _G_exactly_344, lastError = self.exactly('#')
            self.considerError(lastError, 'interpolation')
            self._trace(" '{'", (4445, 4449), self.input.position)
            _G_exactly_345, lastError = self.exactly('{')
            self.considerError(lastError, 'interpolation')
            self._trace(' expression', (4449, 4460), self.input.position)
            _G_apply_346, lastError = self._apply(self.rule_expression, "expression", [])
            self.considerError(lastError, 'interpolation')
            _locals['node'] = _G_apply_346
            self._trace(" '}'", (4465, 4469), self.input.position)
            _G_exactly_347, lastError = self.exactly('}')
            self.considerError(lastError, 'interpolation')
            _G_python_348, lastError = eval(self._G_expr_173, self.globals, _locals), None
            self.considerError(lastError, 'interpolation')
            return (_G_python_348, self.currentError)


        def rule_string_contents(self):
            _locals = {'self': self}
            self.locals['string_contents'] = _locals
            _G_apply_349, lastError = self._apply(self.rule_anything, "anything", [])
            self.considerError(lastError, 'string_contents')
            _locals['quote'] = _G_apply_349
            self._trace('\n            string_part(quote)', (4515, 4546), self.input.position)
            _G_python_351, lastError = eval(self._G_expr_350, self.globals, _locals), None
            self.considerError(lastError, 'string_contents')
            _G_apply_352, lastError = self._apply(self.rule_string_part, "string_part", [_G_python_351])
            self.considerError(lastError, 'string_contents')
            _locals['before'] = _G_apply_352
            _G_python_354, lastError = eval(self._G_expr_353, self.globals, _locals), None
            self.considerError(lastError, 'string_contents')
            _locals['retval'] = _G_python_354
            def _G_many_355():
                self._trace('\n                interpolation', (4647, 4677), self.input.position)
                _G_apply_356, lastError = self._apply(self.rule_interpolation, "interpolation", [])
                self.considerError(lastError, None)
                _locals['node'] = _G_apply_356
                self._trace('\n                string_part(quote)', (4682, 4717), self.input.position)
                _G_python_357, lastError = eval(self._G_expr_350, self.globals, _locals), None
                self.considerError(lastError, None)
                _G_apply_358, lastError = self._apply(self.rule_string_part, "string_part", [_G_python_357])
                self.considerError(lastError, None)
                _locals['after'] = _G_apply_358
                _G_python_360, lastError = eval(self._G_expr_359, self.globals, _locals), None
                self.considerError(lastError, None)
                _locals['retval'] = _G_python_360
                return (_G_python_360, self.currentError)
            _G_many_361, lastError = self.many(_G_many_355)
            self.considerError(lastError, 'string_contents')
            _G_python_363, lastError = eval(self._G_expr_362, self.globals, _locals), None
            self.considerError(lastError, 'string_contents')
            return (_G_python_363, self.currentError)


        def rule_string_part(self):
            _locals = {'self': self}
            self.locals['string_part'] = _locals
            _G_apply_364, lastError = self._apply(self.rule_anything, "anything", [])
            self.considerError(lastError, 'string_part')
            _locals['quote'] = _G_apply_364
            def _G_consumedby_365():
                def _G_many_366():
                    def _G_or_367():
                        self._trace("\n        '#'", (4895, 4907), self.input.position)
                        _G_exactly_368, lastError = self.exactly('#')
                        self.considerError(lastError, None)
                        def _G_not_369():
                            self._trace("'{'", (4909, 4912), self.input.position)
                            _G_exactly_370, lastError = self.exactly('{')
                            self.considerError(lastError, None)
                            return (_G_exactly_370, self.currentError)
                        _G_not_371, lastError = self._not(_G_not_369)
                        self.considerError(lastError, None)
                        return (_G_not_371, self.currentError)
                    def _G_or_372():
                        self._trace(' anything', (4922, 4931), self.input.position)
                        _G_apply_373, lastError = self._apply(self.rule_anything, "anything", [])
                        self.considerError(lastError, None)
                        _locals['ch'] = _G_apply_373
                        def _G_pred_374():
                            _G_python_376, lastError = eval(self._G_expr_375, self.globals, _locals), None
                            self.considerError(lastError, None)
                            return (_G_python_376, self.currentError)
                        _G_pred_377, lastError = self.pred(_G_pred_374)
                        self.considerError(lastError, None)
                        return (_G_pred_377, self.currentError)
                    _G_or_378, lastError = self._or([_G_or_367, _G_or_372])
                    self.considerError(lastError, None)
                    return (_G_or_378, self.currentError)
                _G_many_379, lastError = self.many(_G_many_366)
                self.considerError(lastError, None)
                return (_G_many_379, self.currentError)
            _G_consumedby_380, lastError = self.consumedby(_G_consumedby_365)
            self.considerError(lastError, 'string_part')
            return (_G_consumedby_380, self.currentError)


        def rule_argspec(self):
            _locals = {'self': self}
            self.locals['argspec'] = _locals
            self._trace(' argspec_item', (5019, 5032), self.input.position)
            _G_apply_381, lastError = self._apply(self.rule_argspec_item, "argspec_item", [])
            self.considerError(lastError, 'argspec')
            _locals['head'] = _G_apply_381
            def _G_many_382():
                self._trace('\n        ows', (5039, 5051), self.input.position)
                _G_apply_383, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                self._trace(" ','", (5051, 5055), self.input.position)
                _G_exactly_384, lastError = self.exactly(',')
                self.considerError(lastError, None)
                self._trace(' ows', (5055, 5059), self.input.position)
                _G_apply_385, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                self._trace('\n        argspec_item', (5059, 5080), self.input.position)
                _G_apply_386, lastError = self._apply(self.rule_argspec_item, "argspec_item", [])
                self.considerError(lastError, None)
                _locals['tail'] = _G_apply_386
                _G_python_387, lastError = eval(self._G_expr_80, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_387, self.currentError)
            _G_many_388, lastError = self.many(_G_many_382)
            self.considerError(lastError, 'argspec')
            _locals['tails'] = _G_many_388
            _G_python_390, lastError = eval(self._G_expr_389, self.globals, _locals), None
            self.considerError(lastError, 'argspec')
            return (_G_python_390, self.currentError)


        def rule_argspec_item(self):
            _locals = {'self': self}
            self.locals['argspec_item'] = _locals
            def _G_optional_391():
                self._trace(' variable', (5169, 5178), self.input.position)
                _G_apply_392, lastError = self._apply(self.rule_variable, "variable", [])
                self.considerError(lastError, None)
                _locals['name'] = _G_apply_392
                self._trace(' ows', (5183, 5187), self.input.position)
                _G_apply_393, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                self._trace(" ':'", (5187, 5191), self.input.position)
                _G_exactly_394, lastError = self.exactly(':')
                self.considerError(lastError, None)
                self._trace(' ows', (5191, 5195), self.input.position)
                _G_apply_395, lastError = self._apply(self.rule_ows, "ows", [])
                self.considerError(lastError, None)
                _G_python_397, lastError = eval(self._G_expr_396, self.globals, _locals), None
                self.considerError(lastError, None)
                return (_G_python_397, self.currentError)
            def _G_optional_398():
                return (None, self.input.nullError())
            _G_or_399, lastError = self._or([_G_optional_391, _G_optional_398])
            self.considerError(lastError, 'argspec_item')
            _locals['name'] = _G_or_399
            self._trace('\n        spaced_list', (5211, 5231), self.input.position)
            _G_apply_400, lastError = self._apply(self.rule_spaced_list, "spaced_list", [])
            self.considerError(lastError, 'argspec_item')
            _locals['value'] = _G_apply_400
            _G_python_402, lastError = eval(self._G_expr_401, self.globals, _locals), None
            self.considerError(lastError, 'argspec_item')
            return (_G_python_402, self.currentError)


        _G_expr_353 = compile('Literal(String(before, quotes=quote))', '<string>', 'eval')
        _G_expr_325 = compile('ch', '<string>', 'eval')
        _G_expr_130 = compile('BinaryOp(operator.lt, node, operand)', '<string>', 'eval')
        _G_expr_216 = compile('UnaryOp(operator.neg, node)', '<string>', 'eval')
        _G_expr_309 = compile('Literal(ColorValue(ParserValue(color)))', '<string>', 'eval')
        _G_expr_169 = compile('BinaryOp(operator.ne, node, operand)', '<string>', 'eval')
        _G_expr_120 = compile('NotOp(node)', '<string>', 'eval')
        _G_expr_322 = compile('ord(ch) > 32 and ch not in \' !"$\\\'()\'', '<string>', 'eval')
        _G_expr_247 = compile("FunctionLiteral('url', s)", '<string>', 'eval')
        _G_expr_264 = compile('Literal(parse_bareword(word))', '<string>', 'eval')
        _G_expr_189 = compile('BinaryOp(operator.sub, node, operand)', '<string>', 'eval')
        _G_expr_80 = compile('tail', '<string>', 'eval')
        _G_expr_111 = compile('AllOp(*[head] + tails) if tails else head', '<string>', 'eval')
        _G_expr_280 = compile('Literal(NumberValue(float(number), type=unit))', '<string>', 'eval')
        _G_expr_350 = compile('quote', '<string>', 'eval')
        _G_expr_254 = compile('CallOp(name, args)', '<string>', 'eval')
        _G_expr_83 = compile('ListLiteral([head] + tails) if tails else head', '<string>', 'eval')
        _G_expr_313 = compile('Variable(name)', '<string>', 'eval')
        _G_expr_173 = compile('node', '<string>', 'eval')
        _G_expr_221 = compile('UnaryOp(operator.pos, node)', '<string>', 'eval')
        _G_expr_161 = compile('BinaryOp(operator.eq, node, operand)', '<string>', 'eval')
        _G_expr_182 = compile('BinaryOp(operator.add, node, operand)', '<string>', 'eval')
        _G_expr_137 = compile('BinaryOp(operator.gt, node, operand)', '<string>', 'eval')
        _G_expr_389 = compile('ArgspecLiteral([head] + tails)', '<string>', 'eval')
        _G_expr_208 = compile('BinaryOp(operator.div, node, operand)', '<string>', 'eval')
        _G_expr_35 = compile('unichr(int(cp, 16))', '<string>', 'eval')
        _G_expr_145 = compile('BinaryOp(operator.le, node, operand)', '<string>', 'eval')
        _G_expr_91 = compile('ListLiteral([head] + tails, comma=False) if tails else head', '<string>', 'eval')
        _G_expr_201 = compile('BinaryOp(operator.mul, node, operand)', '<string>', 'eval')
        _G_expr_362 = compile('retval', '<string>', 'eval')
        _G_expr_329 = compile("Literal(String(''.join(s), quotes=None))", '<string>', 'eval')
        _G_expr_396 = compile('name', '<string>', 'eval')
        _G_expr_401 = compile('(name, value)', '<string>', 'eval')
        _G_expr_359 = compile('Interpolation(retval, node, Literal(String(after, quotes=quote)), quotes=quote)', '<string>', 'eval')
        _G_expr_101 = compile('AnyOp(*[head] + tails) if tails else head', '<string>', 'eval')
        _G_expr_153 = compile('BinaryOp(operator.ge, node, operand)', '<string>', 'eval')
        _G_expr_375 = compile("ch not in ('#', quote)", '<string>', 'eval')
    if Grammar.globals is not None:
        Grammar.globals = Grammar.globals.copy()
        Grammar.globals.update(ruleGlobals)
    else:
        Grammar.globals = ruleGlobals
    return Grammar