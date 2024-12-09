import os
import click
from ingest import ingest_from_query

@click.group()
def cli():
    pass

@click.command()
@click.option("--local_path", prompt="Root directory", help="Parent directory for repository.")
@click.option("--sub_path", prompt="Sub-path beneath root directory", help="The sub-directory of the local repository.")
@click.option("--branch", prompt="Branch to ingest from.  Defaults to 'main'.", default="main", help="The branch to use.")
@click.option("--user_name", prompt="User name attributed to the codebase", help="The user name of the repository owner.")
@click.option("--repo_name", prompt="Logical name of the repository", help="The logical name of the repository.")
@click.option("--slug", prompt="URL-friendly repository slug", help="A slug for the repo.")
@click.option("--output", prompt="The output directory to put artifacts into, defaults to 'output'.", 
              default="output",
              help="The directory containing the output artifacts.")
def ingest(local_path, sub_path, branch, user_name, repo_name, output, slug):
    """Ingest a repository to create LLM-friendly ingestible data."""
    qry = {
        "branch": branch,
        "local_path": local_path,
        "output": output,
        "repo_name": repo_name,
        "slug": slug,
        "subpath": f"/{sub_path}",
        "user_name": user_name,
    }
    rslt = ingest_from_query(qry)
    # result is a tuple of three parts
    # 1. The summary string
    sum_fname = f"{qry['repo_name']}_summary.txt"
    # 2. The tree structure
    tree_fname = f"{qry['repo_name']}_tree.txt"
    # 3. The file content
    content_fname = f"{qry['repo_name']}_content.txt"
    if not os.path.exists(output):
        os.makedirs(output)
    with open(f"{qry['output']}/{sum_fname}", "w") as f:
        f.write(rslt[0])
    click.echo(f"Summary written to {qry['output']}/{sum_fname}")
    with open(f"{qry['output']}/{tree_fname}", "w") as f:
        f.write(rslt[1])
    click.echo(f"Tree written to {qry['output']}/{tree_fname}")
    with open(f"{qry['output']}/{content_fname}", "w") as f:
        f.write(rslt[2])
    click.echo(f"Content written to {qry['output']}/{content_fname}")


cli.add_command(ingest)
if __name__ == '__main__':
    cli()
