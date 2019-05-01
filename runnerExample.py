import runner

code = """fun main(args: Array<String>) {
    println("Hello, World!")
}"""
output = runner.run(code)

print(output[1])

output = runner.run(code, "kotlinc-jvm")

print(output[1])