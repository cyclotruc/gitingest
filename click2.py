import click2

@click2.command()
@click2.option('--count', default=1, help='Number of greetings.')
@click2.option('--name', prompt='Your name',
              help='The person to greet.')
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for x in range(count):
        click2.echo(f"Hello {name}!")

if __name__ == '__main__':
    hello()