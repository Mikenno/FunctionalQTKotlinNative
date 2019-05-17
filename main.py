from hypothesis._strategies import randoms, sampled_from, one_of, recursive, builds

import runner
from datetime import datetime
from hypothesis import settings, given, HealthCheck, assume, Verbosity
from hypothesis.strategies import just, text, characters, composite, integers, random_module
import math
import random
import string
from datetime import datetime

from hypothesis import settings, given, HealthCheck
from hypothesis.strategies import text, characters, composite, integers

import runner

names = text(characters(max_codepoint=150, whitelist_categories=('Lu', 'Ll')), min_size=3)
numbers = integers(min_value=-math.pow(2, 63), max_value=(math.pow(2, 63) - 1))

depth = 1


@composite
def projects(draw):
    name = draw(names)
    code = """fun main(args: Array<String>) {
        println("Hello, World!")
    }
    """
    return code.replace("World", name)


def genCode(draw):
    fuel = 25
    string_code = ""
    variables = []
    while (fuel > 0):
        newCode, newVariableList = draw(genExp(variables))
        variables = newVariableList
        string_code += newCode
        fuel -= 1
    return string_code


@composite
def genExp(draw, variables):
    return draw(one_of(
        genVariable(variables),
        genVariableChange(variables)
    ))


variableAssignmentOperators = sampled_from(["=", "+=", "-=", "*=", "/="])
variableOperators = sampled_from(["+", "-", "*", "/", "%"])


@composite
def chooseVariable(draw, variables):
    assume(len(variables) != 0)
    return draw(sampled_from(variables))


@composite
def buildValue(draw, variables):
    return draw(genValue(variables)) + " " + draw(variableOperators) + " " + draw(genValue(variables))


@composite
def buildValueParenthesis(draw, variables):
    return "(" + draw(buildValue(variables)) + ")"


@composite
def genValue(draw, variables):
    return str(draw(one_of(
        numbers,
        buildValue(variables),
        buildValueParenthesis(variables),
        chooseVariable(variables)
    )))


@composite
def genVariableChange(draw, variables):
    if len(variables) == 0:
        return draw(genVariable(variables))

    variableName = draw(chooseVariable(variables))
    return (depth * "\t" + variableName + draw(variableAssignmentOperators) + str(
        draw(genValue(variables))) + ";\n"), variables


@composite
def genVariable(draw, variables):
    newName = True
    value = draw(genValue(variables))
    name = ""
    while newName:
        name = draw(names)
        if name not in variables:
            newName = False
            variables.append(name)
    return (depth * "\t" + 'var ' + name + ' = ' + str(value) + ';\n'), variables

@composite
def projectsv2(draw):
    gen = genCode(draw)
    code = """fun main(args: Array<String>) {
input}
    """
    return code.replace("input", gen)


def nativeRemover(inputString):
    inputString = inputString.replace("inline", "")
    inputString = inputString.replace("@TypedIntrinsic ", "")
    return inputString.replace("-native", "")


@given(projectsv2())
@settings(deadline=None, suppress_health_check=[HealthCheck.large_base_example], max_examples=5, verbosity=Verbosity.debug)
def test_compilertest(s):
    dt = datetime.now()
    name = "out/folder" + (str(dt.microsecond))
    print("run " + str(dt.microsecond))
    output1 = runner.run(s, "kotlinc-jvm", outputDirectory=name)
    output2 = runner.run(s, "kotlinc-native", outputDirectory=name + "-native")
    assert str(output1) == nativeRemover(str(output2))
