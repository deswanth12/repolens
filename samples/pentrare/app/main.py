"""Pentrare CLI Entry Point."""
import click
from app.knowledge.ingest import IngestWorkflow
from app.knowledge.retriever import KnowledgeRetriever

@click.group()
def cli():
    """Pentrare Knowledge Engine CLI."""
    pass

@cli.command()
@click.argument("source_dir")
def ingest(source_dir: str):
    workflow = IngestWorkflow()
    workflow.run(source_dir)

@cli.command()
@click.argument("query")
def search(query: str):
    retriever = KnowledgeRetriever()
    results = retriever.query(query)
    print(results)

def main():
    cli()

if __name__ == "__main__":
    main()
