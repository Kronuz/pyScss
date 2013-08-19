import sys
import traceback

class SassError(Exception):
    """Error class that wraps another exception and attempts to bolt on some
    useful context.
    """
    def __init__(self, exc, rule=None, expression=None):
        self.exc = exc
        self.rule = rule
        self.expression = expression
        _, _, self.original_traceback = sys.exc_info()

    def set_rule(self, rule):
        """Set the current rule.

        If this error already has a rule, it's left alone; this is because
        exceptions propagate outwards and so the first rule seen is the
        "innermost".
        """
        if not self.rule:
            self.rule = rule

    def format_prefix(self):
        # TODO pointer, yadda
        # TODO newlines, yadda
        if self.rule:
            return "Error parsing block:\n" + "    " + self.rule.unparsed_contents
        else:
            return "Unknown error"

    def __str__(self):
        prefix = self.format_prefix()

        ret = [prefix, "\n\n"]

        if self.rule:
            ret.extend(("From ", self.rule.file_and_line, "\n\n"))

        ret.append("Traceback:\n")
        ret.extend(traceback.format_tb(self.original_traceback))
        ret.extend((type(self.exc).__name__, ": ", str(self.exc), "\n"))
        return ''.join(ret)

class SassParseError(SassError):
    """Error raised when parsing a Sass expression fails."""

    def format_prefix(self):
        # TODO pointer
        # TODO deal with newlines, etc
        return """Error parsing expression:\n    %s""" % (self.expression,)


class SassEvaluationError(SassError):
    """Error raised when evaluating a parsed expression fails."""

    def format_prefix(self):
        # TODO pointer
        # TODO ast needs to know where each node came from for that to work  :(
        # TODO deal with newlines, etc
        return """Error evaluating expression:\n    %s""" % (self.expression,)
