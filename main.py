import math
import random
import string
from datetime import datetime

from hypothesis import settings, given, HealthCheck
from hypothesis.strategies import text, characters, composite, integers

import runner

names = text(characters(max_codepoint=150, whitelist_categories=('Lu', 'Ll')), min_size=3)
numbers = integers(min_value=-math.pow(2, 63), max_value=(math.pow(2, 63)-1))

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
        newCode, newVariableList = genExp(draw, variables)
        variables = newVariableList
        string_code += newCode
        fuel -= 1
    return string_code


def genExp(draw, variables):
    r = random.randint(1, 2)
    if r == 1:
        generatedCode, variableList = genVariable(draw, variables)
        return generatedCode, variableList
    elif r == 2:
        return genVariableChange(draw, variables)


def genVariableAssignmentOperator():
    r = random.randint(1, 5)
    if r == 1:
        return "="
    elif r == 2:
        return "+="
    elif r == 3:
        return "-="
    elif r == 4:
        return "/="
    elif r == 5:
        return "*="

def genVariableOperator():
    r = random.randint(1, 5)
    if r == 1:
        return "+"
    elif r == 2:
        return "-"
    elif r == 3:
        return "*"
    elif r == 4:
        return "/"
    elif r == 5:
        return "%"


def genValue(draw, variables):
    r = random.randint(1, 8)
    if r < 4 or len(variables) == 0:
        return draw(numbers)
    elif r < 6:
        return str(genValue(draw, variables)) + " " + genVariableOperator() + " " + str(genValue(draw, variables))
    elif r < 7:
        return "(" + str(genValue(draw, variables)) + " " + genVariableOperator() + " " + str(genValue(draw, variables)) + ")"
    else:
        r = random.randint(0, len(variables) - 1)
        return variables[r]


def genVariableChange(draw, variables):
    if len(variables) == 0:
        return genVariable(draw, variables)

    index = random.randint(0, len(variables) - 1)
    variableName = variables[index]
    return (depth * "\t" + variableName + genVariableAssignmentOperator() + str(genValue(draw, variables)) + ";\n"), variables


def genVariable(draw, variables):
    newName = True
    value = genValue(draw, variables)
    name = ""
    while newName:
        name = draw(names)
        if name not in variables:
            newName = False
            variables.append(name)
    return (depth * "\t" + 'var ' + name + ' = ' + str(value) + ';\n'), variables

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


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
@settings(deadline=None, suppress_health_check=[HealthCheck.large_base_example], max_examples=20)
def test_compilertest(s):
    dt = datetime.now()
    name = "out/folder" + (str(dt.microsecond))
    print("run " + str(dt.microsecond))
    output1 = runner.run(s, "kotlinc-jvm", outputDirectory=name)
    output2 = runner.run(s, "kotlinc-native", outputDirectory=name + "-native")
    assert str(output1) == nativeRemover(str(output2))
