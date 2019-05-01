import os

code = """fun main(args: Array<String>) {
    println("Hello, World!")
}
"""


f = open("test.kt", "w")
f.write(code)
f.close()

os.system("kotlinc/bin/kotlinc test.kt -include-runtime -d test.jar")
output = os.system("java -jar test.jar")

print(output)