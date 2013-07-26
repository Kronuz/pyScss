from ometa.builder import writePython
from ometa.grammar import OMeta
import parsley

with open('scss/expression.parsley') as f:
    grammar_source = f.read()

parser = OMeta(grammar_source)
tree = parser.parseGrammar('Grammar')
generated = writePython(tree, grammar_source)

with open('scss/_generated/expression.py', 'w') as f:
    f.write(generated)
