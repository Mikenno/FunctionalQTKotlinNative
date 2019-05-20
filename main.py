from hypothesis._strategies import randoms, sampled_from, one_of, recursive, builds

import runner
from datetime import datetime
from hypothesis import settings, given, HealthCheck, assume, Verbosity
from hypothesis.strategies import just, text, characters, composite, integers, random_module
import math
import random
import string
from datetime import datetime

from hypothesis import assume, Verbosity
from hypothesis import settings, given, HealthCheck
from hypothesis.strategies import text, characters, composite, integers, decimals

import runner

NUMBER_TYPES = ["Long", "Int", "Double"]
COMPATIBLE_TYPES = {"String": ["String"] + NUMBER_TYPES,
                    "Long": NUMBER_TYPES,
                    "Int": NUMBER_TYPES,
                    "Double": NUMBER_TYPES}

names = text(characters(max_codepoint=150, whitelist_categories=('Lu', 'Ll')), min_size=3)

long = integers(min_value=-math.pow(2, 63), max_value=(math.pow(2, 63) - 1))
integer = integers(min_value=-math.pow(2, 31), max_value=math.pow(2, 31) - 1)
positiveInteger = integers(min_value=0, max_value=math.pow(2, 63) - 1)
negativeInteger = integers(min_value=-math.pow(2, 63), max_value=0)
double = decimals(allow_infinity=False, allow_nan=False)

functionParametersCount = integers(min_value=0, max_value=10)
fuelGen = integers(min_value=1, max_value=50)

fuel = 0


@composite
def projects(draw):
    name = draw(names)
    code = """fun main(args: Array<String>) {
        println("Hello, World!")
    }
    """
    return code.replace("World", name)


def genCode(draw, variables, functions):
    string_code = ""
    global fuel
    while (fuel > 0):
        newCode, newVariableList, functions = draw(genExp(variables, functions))
        variables = newVariableList
        string_code += newCode
        fuel -= 1
    return string_code, variables, functions


@composite
def genLoop(draw, variables, functions):
    startValue = draw(integer)
    varName = draw(names)

    variableNames = []
    for vars in variables:
        variableNames.append(vars[0])
    assume(varName not in variableNames)
    endValue = draw(integer)

    global fuel
    newFuel = draw(integers(min_value=1, max_value=min([25, fuel])))
    fuel -= newFuel
    finalCode = ""

    localVars = variables.copy()
    localVars += [(varName, "Int", True)]
    localFuncs = functions.copy()

    while fuel > 0:
        code, vars, funcs = genCode(draw, localVars, localFuncs)
        finalCode += code
        localVars = vars
        localFuncs = funcs

    return "for (%s in %s..%s) %s" % (varName, startValue, endValue, "{\n" + finalCode + "\n}"), variables, functions


@composite
def genExp(draw, variables, functions):
    return draw(one_of(
        genVariable(variables=variables, functions=functions),
        genVariableChange(variables=variables, functions=functions),
        genFunction(variables=variables, functions=functions),
        genLoop(variables, functions)
    ))


variableAssignmentOperators = sampled_from(["=", "+=", "-=", "*="])  # Division (/ and %) is temporarily excluded
variableOperators = sampled_from(["+", "-", "*"])  # Division (/ and %) is temporarily excluded
stringAssignmentOperators = sampled_from(["=", "+="])


@composite
def chooseVariableName(draw, variables, varType=None, writeableRequired=True):
    assume(len(variables) != 0)
    potentials = []
    for var in variables:
        if type(varType) in [list, tuple]:
            for values in varType:
                if var[1] == values and (not writeableRequired or var[2] == writeableRequired):
                    potentials.append(var[0])
        else:
            if (var[1] == varType or varType is None) and (not writeableRequired or var[2] == writeableRequired):
                potentials.append(var[0])
    return draw(sampled_from(potentials))


@composite
def chooseVariable(draw, variables, varType=None, writeableRequired=True):
    assume(len(variables) != 0)
    potentials = []
    for var in variables:
        if type(varType) in [list, tuple]:
            for values in varType:
                if var[1] == values and (not writeableRequired or var[2] == writeableRequired):
                    potentials.append(var)
        else:
            if (var[1] == varType or varType is None) and (not writeableRequired or var[2] == writeableRequired):
                potentials.append(var)

    return draw(sampled_from(potentials))


@composite
def buildValue(draw, variables, type):
    if type in NUMBER_TYPES:
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
        return draw(long)

    if type == "Int":
        return draw(integer)

    if type == "Double":
        return draw(just(str(draw(double)) + "d"))

    if type == "String":
        return draw(just("\"" + draw(names) + "\""))


@composite
def genValue(draw, variables, type):
    return str(draw(one_of(
        buildPrimitive(type),
        buildValue(variables, type),
        buildValueParenthesis(variables, type),
        chooseVariableName(variables, type, writeableRequired=False)
    )))


@composite
def genType(draw):
    return draw(sampled_from(NUMBER_TYPES + ["String"]))


@composite
def genVariableChange(draw, variables, functions):
    if len(variables) == 0:
        return draw(genVariable(variables, functions))

    variable = draw(chooseVariable(variables))
    variableName = variable[0]
    type = variable[1]

    if type in NUMBER_TYPES:
        operator = draw(variableAssignmentOperators)
    elif type == "String":
        operator = draw(stringAssignmentOperators)
    else:
        operator = "="
    return (variableName + operator + str(
        draw(genValue(variables, type))) + ";\n"), variables, functions


@composite
def genVariable(draw, variables, functions, type=None):
    if type == None:
        type = draw(genType())
    value = draw(genValue(variables, type))
    name = draw(names)
    variableNames = []
    for varName in variables:
        variableNames.append(varName[0])
    assume(name not in variableNames)

    variables.append((name, type, False))
    return ('var ' + name + ': ' + type + ' = ' + str(value) + ';\n'), variables, functions


@composite
def genFunction(draw, variables, functions):
    name = draw(names)
    functionNames = []
    for varName in functions:
        functionNames.append(varName[0])
    assume(name not in functionNames)
    type = draw(genType())
    parameters, parametercode = draw(genParameters())
    code = """fun """ + name + """(""" + parametercode + """ ) :""" + type + """? {
input
output
}"""

    gen, parameters, extraFuncs = genCode(draw, parameters, functions)
    parameters += variables.copy()
    returnvariable = draw(chooseVariableName(parameters, type))
    if (returnvariable is None):
        returncode = """return null"""
    else:
        returncode = """return """ + returnvariable
    functions.append((name, type))
    return code.replace("input", gen).replace("output", returncode), variables, functions


@composite
def genParameters(draw):
    amount = draw(functionParametersCount)
    s = ""
    paramterlist = []
    paramternamelist = []
    for x in range(amount):
        name = draw(names)
        type = draw(genType())
        assume(name not in paramternamelist)
        paramternamelist.append(name)
        paramterlist.append((name, type, True))
        if x == amount - 1:
            s += name + " :" + type
        else:
            s += name + " :" + type + ", "
    return paramterlist, s


@composite
def projectsv2(draw):
    global fuel
    fuel = draw(fuelGen)
    functions = []
    variables = []
    gen, variables, functions = genCode(draw, variables, functions)
    code = """fun main(args: Array<String>) {
input
}
    """
    return code.replace("input", gen)


def nativeRemover(inputString):
    inputString = inputString.replace("inline", "")
    inputString = inputString.replace("@TypedIntrinsic ", "")
    inputString = inputString.replace("external", "")
    return inputString.replace("-native", "")


@given(projectsv2())
@settings(deadline=None, suppress_health_check=HealthCheck.all(), max_examples=20,
          verbosity=Verbosity.debug)
def test_compilertest(s):
    milisec = TimestampMillisec64()
    name = "out/folder" + (str(milisec))
    print("run " + str(milisec))
    (output1) = runner.run(s, "kotlinc-jvm", outputDirectory=name)
    (output2) = runner.run(s, "kotlinc-native", outputDirectory=name + "-native")
    assert nativeRemover(str(output1)) == nativeRemover(str(output2))


def TimestampMillisec64():
    return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000)


@settings(deadline=None, suppress_health_check=HealthCheck.all(), max_examples=5,
          verbosity=Verbosity.debug)
@given(names)
def test_simple_out(input):
    code = """fun main(args: Array<String>) {
println("{input}")
}""".replace("{input}", input)

    name = "out/folder" + (str(TimestampMillisec64()))
    output1 = runner.run(code, "kotlinc-jvm", outputDirectory=name)
    output2 = runner.run(code, "kotlinc-native", outputDirectory=name + "-native")

    assert output1[1] == input
    assert output2[1] == input
