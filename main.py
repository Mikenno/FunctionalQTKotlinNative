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


variableAssignmentOperators = sampled_from(["=", "+=", "-=", "*="])  # Division (/ and %) is temporarily excluded
variableOperators = sampled_from(["+", "-", "*"])  # Division (/ and %) is temporarily excluded


@composite
def chooseVariableName(draw, variables, varType=None):
    assume(len(variables) != 0)
    potentials = []
    for var in variables:
        if var[1] == varType or varType is None:
            potentials.append(var[0])
    return draw(sampled_from(potentials))


@composite
def chooseVariable(draw, variables, varType=None):
    assume(len(variables) != 0)
    potentials = []
    for var in variables:
        if var[1] == varType or varType is None:
            potentials.append(var)
    return draw(sampled_from(potentials))


@composite
def buildValue(draw, variables, type):
    if type == "Long":
        operator = draw(variableOperators)
    elif type == "String":
        operator = "+"
    else:
        return draw(genValue(variables, type))
    return draw(genValue(variables, type)) + " " + operator + " " + draw(genValue(variables, type))


@composite
def buildValueParenthesis(draw, variables, type):
    return "(" + draw(buildValue(variables, type)) + ")"


@composite
def buildPrimitive(draw, type):
    if type == "Long":
        return draw(numbers)

    if type == "String":
        return draw(just("\"" + draw(names) + "\""))


@composite
def genValue(draw, variables, type):
    return str(draw(one_of(
        buildPrimitive(type),
        buildValue(variables, type),
        buildValueParenthesis(variables, type),
        chooseVariableName(variables, type)
    )))


@composite
def genType(draw):
    return draw(sampled_from(["Long", "String"]))


@composite
def genVariableChange(draw, variables):
    if len(variables) == 0:
        return draw(genVariable(variables))

    variable = draw(chooseVariable(variables))
    variableName = variable[0]
    type = variable[1]

    if type == "Long":
        operator = draw(variableAssignmentOperators)
    elif type == "String":
        operator = draw(sampled_from(["=", "+="]))
    else:
        operator = "="
    return (depth * "\t" + variableName + operator + str(
        draw(genValue(variables, type))) + ";\n"), variables


@composite
def genVariable(draw, variables, type=None):
    if type == None:
        type = draw(genType())
    value = draw(genValue(variables, type))
    name = draw(names)
    variableNames = []
    for varName in variables:
        variableNames.append(varName[0])
    assume(name not in variableNames)

    variables.append((name, type))
    return (depth * "\t" + 'var ' + name + ': ' + type + ' = ' + str(value) + ';\n'), variables


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
    inputString = inputString.replace("external", "")
    return inputString.replace("-native", "")


@given(projectsv2())
@settings(deadline=None, suppress_health_check=[HealthCheck.large_base_example], max_examples=20,
          verbosity=Verbosity.debug)
def test_compilertest(s):
    dt = datetime.now()
    name = "out/folder" + (str(dt.microsecond))
    print("run " + str(dt.microsecond))
    (output1) = runner.run(s, "kotlinc-jvm", outputDirectory=name)
    (output2) = runner.run(s, "kotlinc-native", outputDirectory=name + "-native")
    assert nativeRemover(str(output1)) == nativeRemover(str(output2))
