import runner

code = """fun main(args: Array<String>) {
    println("Hello, World!")
}"""
output = runner.run(code)

print("output1: " + output[1])

output = runner.run(code, "kotlinc-native")

print("output2: " + output[1])