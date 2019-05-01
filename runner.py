import glob
import os
import subprocess

TEMPORARY_CODE_FILE_NAME = "out/code.kt"
TEMPORARY_EXECUTABLE_FILE_NAME = "out/code.jar"


def run(code, compiler="kotlinc") -> (bool, str):
    prepareOutputDirectory()
    checkPrerequisites(code, compiler)
    writeCodeFile(code, TEMPORARY_CODE_FILE_NAME)
    compilerOutput = compileFile(TEMPORARY_CODE_FILE_NAME, TEMPORARY_EXECUTABLE_FILE_NAME, compiler)
    runOutput = runFile(TEMPORARY_EXECUTABLE_FILE_NAME, compiler)
    return (compilerOutput, runOutput)


def runFile(file, compiler):
    if os.path.exists(file):
        executionString = "java -jar " + file
        return subprocess.run(executionString, stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8')
    return None


def compileFile(inputFile, outputFile, compiler):
    executionString = "kotlinc/bin/{} {} -include-runtime -d {}".format(compiler, inputFile, outputFile)

    if os.name == 'nt':
        executionString = executionString.replace("/", "\\")

    return subprocess.run(executionString, stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8')


def checkPrerequisites(code, compiler):
    if not os.path.exists("kotlinc/bin/" + compiler):
        raise Exception("ERROR: Please include standalone kotlin compiler in kotlinc folder, aborting")
    if code == "":
        print("Warning: Code is blank")


def writeCodeFile(code, outputFile):
    f = open(outputFile, "w")
    f.write(code)
    f.close()


def prepareOutputDirectory():
    if not os.path.isdir("out"):
        os.mkdir("out")
    else:
        files = glob.glob('out/*')
        for f in files:
            os.remove(f)
