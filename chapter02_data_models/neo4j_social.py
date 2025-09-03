from neo4j import GraphDatabase

URI = "bolt://localhost:7687" 
AUTH = ("neo4j", "password")

def create_first_user(driver):
    """Creates a single user node in the database"""
    with driver.session() as session:
        # A session.write_transaction() automatically handles commits and rollbacks.
        # This is the standard way to execute write queries.
        result = session.write_transaction(create_user_node, "Alice")
        print(f"Created user: {result}")

def create_user_node(tx, name):
    """This function is executed by the transaction.
    It creates a single :User node with a name property.
    """
    query = "CREATE (a:USER {name: $name}) RETURN a.name AS name"
    result = tx.run(query, name=name)
    return result.single()[0]


def main():
    # the driver object is thread-safe and manages your connection pool
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connection successful")
        create_first_user(driver)


if __name__ == "__main__":
    main()
