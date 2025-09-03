from neo4j import GraphDatabase

URI = "bolt://localhost:7687" 
AUTH = ("neo4j", "password")

def create_first_user(driver, name="Alice"):
    """Creates a single user node in the database"""
    with driver.session() as session:
        # A session.write_transaction() automatically handles commits and rollbacks.
        # This is the standard way to execute write queries.
        result = session.write_transaction(create_user_node, name)
        print(f"Created user: {result}")
        return result

def create_user_node(tx, name):
    """This function is executed by the transaction.
    It creates a single :User node with a name property.
    """
    query = "CREATE (a:USER {name: $name}) RETURN a.name AS name"
    result = tx.run(query, name=name)
    return result.single()[0]

def create_social_graph(driver):
    """Creates a small social network in the database."""
    with driver.session() as session:
        # First, cleanup the database to ensure we start fresh
        session.write_transaction(lambda tx: tx.run("MATCH (n) DETACH DELETE n"))
        print("Cleaned up old data.")
        # This single transaction will create all users and their relationships
        result = session.write_transaction(_create_users_and_relationships)
        print("Created the following relationships:")
        for record in result:
            print(f"- {record['userA']} FOLLOWS {record['userB']}")

def _create_users_and_relationships(tx):
    """This function is executed within a single transaction.
    It creates all the user nodes and the FOLLOWS relationships between them."""
    # Cypher query to create users and relationships in one go.
    query = """
    // Create all the user nodes first.
    CREATE (alice:User {name: 'Alice'}),
           (bob:User {name: 'Bob'}),
           (charlie:User {name: 'Charlie'}),
           (diana:User {name: 'Diana'}),
           (elaine:User {name: 'Elaine'})

    // Use WITH to pass the created nodes to the next part of the query
    WITH alice, bob, charlie, diana, elaine

    // Create the relationships
    CREATE (alice)-[:FOLLOWS]->(bob),
           (alice)-[:FOLLOWS]->(charlie), 
           (bob)-[:FOLLOWS]->(diana),
           (charlie)-[:FOLLOWS]->(diana), 
           (charlie)-[:FOLLOWS]->(elaine)

    // Add another WITH to separate the final write from the read
    WITH alice, bob, charlie, diana, elaine

    // Return the created relationships for verification
    MATCH (a:User)-[r:FOLLOWS]->(b:User)
    RETURN a.name AS userA, b.name AS userB
    """
    result = tx.run(query)
    return result.data()


if __name__ == "__main__":
    # the driver object is thread-safe and manages your connection pool
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connection successful")
        create_first_user(driver)
        create_social_graph(driver)
