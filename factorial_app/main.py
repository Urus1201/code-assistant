import click

def factorial(n: int) -> int:
    if n <= 1:
        return 1
    return n * factorial(n-1)

@click.command()
@click.argument('number', type=int)
def main(number):
    """
    Calculate factorial of a given integer.
    """
    result = factorial(number)
    click.echo(f"Factorial of {number} is {result}")

if __name__ == '__main__':
    main()
