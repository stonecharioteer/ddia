#!/usr/bin/env python3
"""
Database demonstration CLI tool for DDIA Chapter 2 exercises.
Supports PostgreSQL, MongoDB, and Neo4j operations.
"""

import click
from tqdm import tqdm
from postgres import (
    create_schemas,
    populate_initial_skills,
    load_data,
    add_followers,
    run_sql_file,
)
from mongodb import (
    load_one_resume,
    filter_resumes,
    summary,
    summary_mapreduce,
    purge_data,
)
from neo4j_social import (
    GraphDatabase,
    create_first_user,
    create_social_graph,
    query_followers_of_random_user,
    query_friends_of_friends,
    query_influential_followers,
)


@click.group()
@click.help_option("-h", "--help")
def cli():
    """Database demonstration CLI for PostgreSQL, MongoDB, and Neo4j."""
    pass


@cli.group()
@click.help_option("-h", "--help")
def postgres():
    """PostgreSQL operations.

    \b
    Setup order:
      1. create-schemas     (Create database tables)
      2. populate-data      (Add fake data and followers)

    \b
    Then run any of:
      - count-skills               (Show skill distribution)
      - suggest-follows            (Suggest users to follow via friends-of-friends)
      - list-influential-followers (Find users with influential followers)
    """
    pass


@postgres.command("create-schemas")
@click.help_option("-h", "--help")
def postgres_create_schemas():
    """Create database tables from schema.sql."""
    try:
        create_schemas()
        click.echo("✓ PostgreSQL schemas created successfully")
    except Exception as e:
        click.echo(f"✗ Error creating schemas: {e}", err=True)
        raise click.Abort()


@postgres.command("populate-data")
@click.option("--users", default=10000, help="Number of users to generate")
@click.help_option("-h", "--help")
def postgres_populate_data(users):
    """Populate database with fake resume data and followers."""
    try:
        click.echo("Populating initial skills...")
        populate_initial_skills()

        click.echo(f"Loading data for {users:_} users...")
        load_data(num_users=users)

        click.echo("Adding follower relationships...")
        add_followers()

        click.echo("✓ PostgreSQL data populated successfully")
    except Exception as e:
        click.echo(f"✗ Error populating data: {e}", err=True)
        raise click.Abort()


@postgres.command("count-skills")
@click.help_option("-h", "--help")
def postgres_count_skills():
    """Count how many users have each skill."""
    try:
        click.echo("Counting users per skill...")
        run_sql_file("summary.sql")
        click.echo("✓ Skill count completed")
    except Exception as e:
        click.echo(f"✗ Error counting skills: {e}", err=True)
        raise click.Abort()


@postgres.command("suggest-follows")
@click.option("--user-id", default=1, help="User ID to find follow suggestions for")
@click.help_option("-h", "--help")
def postgres_suggest_follows(user_id):
    """Suggest users to follow based on friends-of-friends analysis."""
    try:
        click.echo(
            f"Finding follow suggestions for user {user_id} (friends-of-friends)..."
        )
        run_sql_file("followers.sql", user_id=user_id)
        click.echo("✓ Follow suggestions completed")
    except Exception as e:
        click.echo(f"✗ Error generating follow suggestions: {e}", err=True)
        raise click.Abort()


@postgres.command("list-influential-followers")
@click.option(
    "--min-followers",
    default=12,
    help="Minimum followers threshold for influential users",
)
@click.help_option("-h", "--help")
def postgres_list_influential_followers(min_followers):
    """List users who have influential followers (followers with many followers)."""
    try:
        click.echo(
            f"Finding users with influential followers (min {min_followers} followers each)..."
        )
        run_sql_file("follower_with_ge_x_followers.sql", min_followers=min_followers)
        click.echo("✓ Influential followers analysis completed")
    except Exception as e:
        click.echo(f"✗ Error running influential followers analysis: {e}", err=True)
        raise click.Abort()


@cli.group()
@click.help_option("-h", "--help")
def mongo():
    """MongoDB operations.

    \b
    Setup order:
      1. populate-data     (Generate and insert fake resumes)

    \b
    Then run any of:
      - query-resumes         (Demonstrate various MongoDB queries)
      - count-skills          (Count skills using aggregation pipeline)
      - count-skills-mapreduce (Count skills using legacy MapReduce)
      - purge-data            (Clear all data from MongoDB collections)
    """
    pass


@mongo.command("populate-data")
@click.option("--resumes", default=50, help="Number of resumes to generate")
@click.help_option("-h", "--help")
def mongo_populate_data(resumes):
    """Generate and insert fake resumes."""
    try:
        click.echo(f"Generating and inserting {resumes:_} fake resumes into MongoDB...")

        # Use tqdm for progress bar with counter, ETA, and elapsed time
        # Custom format function for underscore-separated numbers
        def format_num(n):
            return f"{n:_}"

        with tqdm(
            total=resumes,
            desc="Inserting resumes",
            unit="resume",
            bar_format="{l_bar}{bar}| {n:_}/{total:_} [{elapsed}<{remaining}]",
        ) as pbar:
            for i in range(resumes):
                load_one_resume()
                pbar.update(1)

        click.echo("✓ MongoDB data populated successfully")
    except Exception as e:
        click.echo(f"✗ Error populating data: {e}", err=True)
        raise click.Abort()


@mongo.command("query-resumes")
@click.help_option("-h", "--help")
def mongo_query_resumes():
    """Demonstrate various MongoDB queries on resume data."""
    try:
        click.echo("Demonstrating MongoDB query patterns...")
        filter_resumes()
        click.echo("✓ Query demonstration completed")
    except Exception as e:
        click.echo(f"✗ Error running queries: {e}", err=True)
        raise click.Abort()


@mongo.command("count-skills")
@click.help_option("-h", "--help")
def mongo_count_skills():
    """Count how many users have each skill using aggregation pipeline."""
    try:
        click.echo("Counting skills using MongoDB aggregation pipeline...")
        summary()
        click.echo("✓ Skill counting completed")
    except Exception as e:
        click.echo(f"✗ Error counting skills: {e}", err=True)
        raise click.Abort()


@mongo.command("count-skills-mapreduce")
@click.help_option("-h", "--help")
def mongo_count_skills_mapreduce():
    """Count how many users have each skill using legacy MapReduce."""
    try:
        click.echo("Counting skills using legacy MongoDB MapReduce...")
        summary_mapreduce()
        click.echo("✓ MapReduce skill counting completed")
    except Exception as e:
        click.echo(f"✗ Error running MapReduce: {e}", err=True)
        raise click.Abort()


@mongo.command("purge-data")
@click.help_option("-h", "--help")
def mongo_purge_data():
    """Clear all data from MongoDB collections."""
    try:
        click.echo("Purging all data from MongoDB collections...")
        purge_data()
        click.echo("✓ MongoDB data purged successfully")
    except Exception as e:
        click.echo(f"✗ Error purging data: {e}", err=True)
        raise click.Abort()


@cli.group()
@click.help_option("-h", "--help")
def neo4j():
    """Neo4j operations."""
    pass


@neo4j.command("create-user")
@click.option("--name", default="Alice", help="Name of the user to create")
@click.help_option("-h", "--help")
def neo4j_create_user(name):
    """Create a single user node."""
    try:
        with GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "password")
        ) as driver:
            driver.verify_connectivity()
            create_first_user(driver, name)
            click.echo(f"✓ Created Neo4j user: {name}")
    except Exception as e:
        click.echo(f"✗ Error creating user: {e}", err=True)
        raise click.Abort()


@neo4j.command("create-social-graph")
@click.help_option("-h", "--help")
def neo4j_create_social_graph():
    try:
        with GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "password")
        ) as driver:
            driver.verify_connectivity()
            create_social_graph(driver, num_users=10000)
            click.echo("✓ Created Social graph")
    except Exception as e:
        click.echo(f"✗ Error creating user: {e}", err=True)
        raise click.Abort()

@neo4j.command("get-followers-of-random-user")
@click.help_option("-h", "--help")
def neo4j_get_followers_of_random_user():
    try:
        with GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password")) as driver:
            driver.verify_connectivity()
            query_followers_of_random_user(driver)
            click.echo("✓ Queried followers")
    except Exception as e:
        click.echo(f"✗ Error getting followers: {e}", err=True)
        raise click.Abort()


@neo4j.command("get-influential-followers")
@click.help_option("-h", "--help")
def neo4j_get_influential_followers():
    try:
        with GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password")) as driver:
            driver.verify_connectivity()
            query_influential_followers(driver)
            click.echo("✓ Queried influential followers")
    except Exception as e:
        click.echo(f"✗ Error getting followers: {e}", err=True)
        raise click.Abort()


@neo4j.command("get-friends-of-friends")
@click.help_option("-h", "--help")
def neo4j_get_friends_of_friends():
    try:
        with GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password")) as driver:
            driver.verify_connectivity()
            query_friends_of_friends(driver)
            click.echo("✓ Queried influential followers")
    except Exception as e:
        click.echo(f"✗ Error getting followers: {e}", err=True)
        raise click.Abort()
if __name__ == "__main__":
    cli()
