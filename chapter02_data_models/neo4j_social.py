import uuid
import random
from neo4j import GraphDatabase
from mimesis import Person
from mimesis.locales import Locale

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


def ensure_uniqueness_constraint(driver):
    """Ensure a uniqueness constraint is set on the User nodes."""
    with driver.session() as session:
        # update the constraint to be on the `uuid` property
        query = "CREATE CONSTRAINT user_uuid_unique IF NOT EXISTS FOR (u:User) REQUIRE u.uuid IS UNIQUE"
        session.run(query)
        print("Uniqueness constraint on :User(uuid) is present.")


def create_social_graph(driver, num_users=100):
    """Creates a social network with a given number of users."""
    with driver.session() as session:
        # Delete existing data
        session.write_transaction(lambda tx: tx.run("MATCH (n) DETACH DELETE n"))
        print("Cleaned up old data.")
        person = Person(Locale.EN)
        users_to_create = []
        user_names = set()
        while len(user_names) < num_users:
            user_names.add(person.full_name())

        # 1. Generate a name and a unique UUID for each user.
        for name in user_names:
            users_to_create.append({"name": name, "uuid": str(uuid.uuid4())})
        # 2. Generate random relationships using the new UUIDs
        relationships_to_create = []
        user_uuids = [u["uuid"] for u in users_to_create]
        for follower_uuid in user_uuids:
            num_to_follow = random.randint(1, 20)
            potential_users = [uid for uid in user_uuids if uid != follower_uuid]
            users_to_follow = random.sample(
                potential_users, min(num_to_follow, len(potential_users))
            )
            for user_uuid in users_to_follow:
                relationships_to_create.append((follower_uuid, user_uuid))
        session.write_transaction(
            _bulk_create_users_and_relationships,
            users_to_create,
            relationships_to_create,
        )
        print(
            "Bulk-created {} users and {} relationships.".format(
                len(users_to_create), len(relationships_to_create)
            )
        )


def _bulk_create_users_and_relationships(tx, users, relationships):
    """This function uses UNWIND for efficient, batched graph creation."""
    # create user nodes with both name and uuid properties
    create_users_query = """
    UNWIND $users AS user_data
    CREATE (u:User {name: user_data.name, uuid: user_data.uuid})
    """

    tx.run(create_users_query, users=users)
    # Match users by their unique UUID to create relationships
    create_relationships_query = """
    UNWIND $relationships AS rel
    MATCH (u1:User {uuid: rel[0]})
    MATCH (u2:User {uuid: rel[1]})
    CREATE (u1)-[:FOLLOWS]->(u2)
    """
    tx.run(create_relationships_query, relationships=relationships)


def query_followers_of_random_user(driver):
    """Fetchs and prints the followers of a randomly selected user."""
    with driver.session() as session:
        # First, get a list of all user UUIDs to choose from
        result = session.read_transaction(
            lambda tx: tx.run("MATCH (u:User) RETURN u.uuid AS uuid").data()
        )
        if not result:
            print("No users in the database to query.")
            return

        all_uuids = [record["uuid"] for record in result]
        random_user_uuid = random.choice(all_uuids)

        # Now, find the followers for that randomly selected user.
        followers_result = session.read_transaction(_get_followers, random_user_uuid)
        if followers_result:
            user_name = followers_result[0]["user_name"]
            follower_names = sorted(
                [record["follower_name"] for record in followers_result]
            )
            print(f"Followers for user: {user_name}")
            for name in follower_names:
                print(f"- {name}")
        else:
            # Handle the case where the user has no followers
            user_info = session.read_transactions(
                lambda tx: tx.run(
                    "MATCH (u.User {uuid: $uuid}) RETURN u.name AS name",
                    uuid=random_user_uuid,
                ).data()
            )
            if user_info:
                user_name = user_info[0]["name"]
                print(f"User {user_name} has no followers")


def _get_followers(tx, user_uuid):
    """Transaction function to get followers of a specific user."""
    query = """
    MATCH (follower:User)-[:FOLLOWS]->(user:User {uuid: $uuid})
    RETURN user.name AS user_name, follower.name as follower_name
    """
    result = tx.run(query, uuid=user_uuid)
    return result.data()

def query_influential_followers(driver):
    """Finds users based on the influence of their followers"""
    print("Users with the most influential followers (>=8 followers themselves)")
    with driver.session() as session:
        results = session.read_transaction(_get_influential_followers)
        for record in results:
            username = record["userName"]
            influential_follower_count  = record["influentialFollowerCount"]
            print(f"- {username}: {influential_follower_count}")

def _get_influential_followers(tx):
    """Transaction function to get counts of influential followers"""
    minimum_followers = 7
    query = """
    // Find all relationships where a follower follows a user
    MATCH (follower:User)-[:FOLLOWS]->(u:User)

    // Filter to only include followers who have the minimum number of followers themselves
    WHERE size( (follower)<-[:FOLLOWS]-()) >= $minFollowers

    // Use WITH to perform the aggregation first
    WITH u, count(follower) AS influentialFollowerCount

    // Use a final WHERE to filter the results fo the aggregation
    WHERE influentialFollowerCount >= $minFollowers

    // Group by the original user and count the influential followers
    RETURN u.name AS userName, influentialFollowerCount
    ORDER BY influentialFollowerCount DESC
    """
    result = tx.run(query, minFollowers=minimum_followers)
    return result.data()

def query_friends_of_friends(driver):
    """Finds and prints the `friends of friends` for a random user"""
    with driver.session() as session:
        result = session.read_transaction(lambda tx: tx.run("MATCH (u:User) RETURN u.uuid AS uuid, u.name AS name").data())
        if not result:
            return
        random_user = random.choice(result)
        random_user_uuid = random_user["uuid"]
        random_user_name = random_user["name"]
        fof_result = session.read_transaction(_get_friends_of_friends, random_user_uuid)

        print(f"Friends of friends for user: {random_user_name}")
        if fof_result:
            fof_names = sorted([record["friendOfFriendName"] for record in fof_result])
            for name in fof_names:
                print(f"- {name}")
        else:
            print("No friend of friends found for this user.")

def _get_friends_of_friends(tx, user_uuid):
    """Transaction function to get friends of friends."""
    query = """
    MATCH (u:User {uuid: $uuid})-[:FOLLOWS]->(friend:User)-[:FOLLOWS]->(fof:User)
    WHERE u <> fof AND NOT (u)-[:FOLLOWS]->(fof)
    RETURN DISTINCT fof.name AS friendOfFriendName
    """
    result = tx.run(query, uuid=user_uuid)
    return result.data()

if __name__ == "__main__":
    # the driver object is thread-safe and manages your connection pool
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connection successful")
        create_first_user(driver)
        create_social_graph(driver)
