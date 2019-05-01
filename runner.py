import glob
import os
import subprocess

TEMPORARY_CODE_FILE_NAME = "out/code.kt"
TEMPORARY_EXECUTABLE_FILE_NAME = "out/code"


def run(code, compiler="kotlinc") -> (bool, str):
    prepareOutputDirectory()
    checkPrerequisites(code, compiler)
    writeCodeFile(code, TEMPORARY_CODE_FILE_NAME)
    compilerOutput = compileFile(TEMPORARY_CODE_FILE_NAME, TEMPORARY_EXECUTABLE_FILE_NAME, compiler)
    runOutput = runFile(TEMPORARY_EXECUTABLE_FILE_NAME, compiler)
    return (compilerOutput, runOutput)


def runFile(file, compiler):
    if compiler == "kotlinc-jvm" or compiler == "kotlinc":
        file = file + ".jar"
    elif isWindows():
        file = file + ".exe"
    else:
        file = file + ".kexe"

    if os.path.exists(file):
        if compiler == "kotlinc-jvm" or compiler == "kotlinc":
            executionString = "java -jar " + file
        else:
            if isWindows():
                executionString = "./" + file
            else:
                executionString = "./" + file
        return subprocess.run(executionString, stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8')
    return None


def isWindows():
    return os.name == "nt"


def compileFile(inputFile, outputFile, compiler):
    if compiler == "kotlinc-jvm" or compiler == "kotlinc":
        outputFile = outputFile + ".jar"
        executionString = "kotlinc/bin/{} {} -include-runtime -d {}".format(compiler, inputFile, outputFile)

        if os.name == 'nt':
            executionString = executionString.replace("/", "\\")

        return subprocess.run(executionString, stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8')
    elif compiler == "kotlinc-native":
        if isWindows():
            outputFile = outputFile.replace("/", "\\") + ".exe"
            inputFile = inputFile.replace("/", "\\")

            executionString = "kotlinc-windows\\bin\\{} -o {output} {input}".format(compiler, input=inputFile,
                                                                                    output=outputFile)
            return subprocess.run(executionString, stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8')
        else:
            outputFile = outputFile + ".kexe"
            executionString = "kotlinc-linux/bin/{} -o {output} {input}".format(compiler, input=inputFile,
                                                                                output=outputFile)
            return subprocess.run(executionString, stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8')


def checkPrerequisites(code, compiler):
    if compiler == "kotlinc-native":
        if os.name == "nt":
            if not os.path.exists("kotlinc-windows/bin/" + compiler):
                raise Exception(
                    "ERROR: Please include standalone native kotlin compiler in kotlinc-windows folder, aborting")
        else:
            if not os.path.exists("kotlinc-linux/bin/" + compiler):
                raise Exception(
                    "ERROR: Please include standalone native kotlin compiler in kotlinc-linux folder, aborting")
    else:
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
