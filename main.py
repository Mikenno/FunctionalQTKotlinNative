import runner
from datetime import datetime
from hypothesis import settings, given, HealthCheck
from hypothesis.strategies import just, text, characters, composite, integers, random_module
import random
import string
import time

names = text(characters(max_codepoint=150, whitelist_categories=('Lu', 'Ll')), min_size=3)
numbers = integers()

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


def genVariableOperator():
    r = random.randint(1, 10)
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
    elif r == 6:
        return "+"
    elif r == 7:
        return "-"
    elif r == 8:
        return "*"
    elif r == 9:
        return "/"
    elif r == 10:
        return "%"


def genValue(draw, variables):
    r = random.randint(1, 4)
    if r < 4 or len(variables) == 0:
        return draw(numbers)
    else:
        r = random.randint(0, len(variables) - 1)
        return variables[r]


def genVariableChange(draw, variables):
    if len(variables) == 0:
        return genVariable(draw, variables)

    index = random.randint(0, len(variables) - 1)
    variableName = variables[index]
    return (depth * "\t" + variableName + genVariableOperator() + str(genValue(draw, variables)) + ";\n"), variables


def genVariable(draw, variables):
    newName = True
    name = ""
    while newName:
        name = draw(names)
        if name not in variables:
            newName = False
            variables.append(name)
    return (depth * "\t" + 'var ' + name + ' = ' + str(draw(numbers)) + ';\n'), variables


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
def compilertest(s):
    dt = datetime.now()
    name = "out/folder" + (str(dt.microsecond))
    print("run " + str(dt.microsecond))
    output1 = runner.run(s, "kotlinc-jvm", outputDirectory=name)
    output2 = runner.run(s, "kotlinc-native", outputDirectory=name + "-native")
    assert str(output1) == nativeRemover(str(output2))
    #time.sleep(1)

compilertest()
