# Document Data Model

## Exercise 2: Resume in MongoDB (The Document Model)

Objective: To model the same resume data from the relational exercise in a document database (MongoDB). This exercise is
designed to provide a direct contrast to the relational model and make the concepts of data locality and schema-on-read
tangible.

## Getting Started

1. **Start MongoDB using Docker Compose:**
   ```bash
   docker compose up -d mongodb
   ```

2. **Set up the Python environment:**
   ```bash
   uv sync
   ```

3. **Run the MongoDB data loader:**
   ```bash
   uv run mongodb.py
   ```

## Key Concepts Demonstrated

1. The Document Model: Instead of tables and rows, MongoDB stores data in collections of documents. Each document is a
   flexible, JSON-like structure (technically BSON) that can have nested objects and arrays.
2. Schema-on-Read: This is the core philosophical difference from PostgreSQL. We did not create a schema.sql file. The
   database does not enforce a rigid structure on write. Instead, the "schema" is defined by the structure of the Python
   dictionary in our application code at the moment of insertion. This flexibility makes it much easier to evolve the
   application over time.
3. Data Locality: This is the most important advantage for this use case. The entire resume—the user's name, all their
   job positions, all their education history, and all their skills—is stored together as a single document in the
   database.
   - The Result: Because the entire resume has high locality, it can be retrieved with a single query. This completely
     eliminates the need for the multiple JOIN operations that were required in the relational model.
4. Reduced Impedance Mismatch: The structure of our Python dictionary, with its nested lists for positions and
   education, maps almost perfectly to the way the data is stored in the MongoDB document. This significantly reduces
   the "impedance mismatch" we experienced with the relational model, leading to simpler, more intuitive application
   code.

### The Exercise in Practice

1. Designing the Document: The first step was to represent the resume as a single JSON object. The positions and
   education sections, which were separate tables in PostgreSQL, became arrays of nested objects inside the main user
   document.

   ```json

   {
     "name": "Gaston Hyde",
     "positions": [
       { "title": "Joinery Consultant", "company": "AT&T" ... }
     ],
     "education": [
       { "university": "University of Louisville", "degree": "Master" ... }
     ],
     "skills": ["CI/CD", "VueJS", "AWS" ...]
   }
   ```

2. Inserting the Data: The Python script used `mimesis` to build this nested dictionary and then inserted the entire
   object into the `resumes` collection with a single command: `resumes_collection.insert_one(resume_doc)`. This is much
   simpler than the multiple `INSERT` statements and foreign key lookups required for the normalized relational schema.
3. Querying Nested Data: We saw that MongoDB's query language is extremely powerful for working with nested data:

- Simple Array Query: ``{"skills": "Python"}` finds any document where "Python" is an element in the skills array.
- AND Condition: `{"skills": {"$all": ["Python", "AWS"]}}` finds documents where the skills array contains both values.
- OR Condition: `{"skills": {"$in": ["Python", "AWS"]}}` finds documents where the skills array contains at least one of
  the values.
- Querying Nested Objects: `"education.major": "Statistics"` uses dot notation to "reach into" the education array and
  find a match.
- Precise Nested Queries: `{"education": {"$elemMatch": {"degree": "PhD", "major": "Statistics"}}}` is used to find a
  single education entry that meets multiple criteria, solving the problem of false positives that can occur with
  simpler queries.

### Summary: Relational vs. Document for the Resume Use Case

| Aspect                | Relational Model (PostgreSQL)                                                | Document Model (MongoDB)                                                    |
| --------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Schema                | Schema-on-Write: Rigid, defined upfront in schema.sql.                       | Schema-on-Read: Flexible, defined by the application code.                  |
| Data Structure        | Normalized: Data is split into 5 tables to reduce duplication.               | Denormalized: Data has high locality; the entire resume is in one document. |
| Writing Data          | Requires multiple INSERT statements and careful handling of foreign keys.    | Requires a single insert_one operation for the entire nested object.        |
| Reading a Full Resume | Requires multiple queries and application-side JOINs to reassemble the data. | A single find_one query retrieves the entire document.                      |

**Conclusion**: For a self-contained document like a resume, the document model is a much more natural fit. It
simplifies the application code for both writes and reads and avoids the complexity of JOINs, perfectly illustrating the
advantages of data locality that are discussed in Chapter 2.

### Caveats

However, there is one more crucial concept that Chapter 2 discusses, which is the big trade-off you have to make when
designing a document model:

#### Handling Relationships: Embedding vs. Referencing

In our resume exercise, we used embedding. We put the positions and education arrays directly inside the user document.
This works perfectly for a resume because that data has high locality—you almost always want to see a person's jobs when
you look at their resume.

But what if the relationship was different?

Imagine our application also needed to show a page for each company, listing its address, industry, and all the users in
our database who have ever worked there.

- If we embed the company name as a simple string (like we did), and Hilton Hotels changes its name, we would have to
  find and update every single user document that contains "Hilton Hotels Corporation." This can be slow and complex.
- This is where referencing comes in. Instead of embedding the company name, we could store a company_id, just like we
  would in a relational database.

```json
{
  "name": "Olimpia Haynes",
  "positions": [
    {
      "title": "Motor Racing",
      "company_id": "ObjectId('some-unique-id-for-hilton')"
      // ...
    }
  ]
  // ...
}
```

Then, you would have a separate companies collection to store the details for each company. To reconstruct the resume,
your application would first fetch the user document, and then make a second query to fetch the details for each
company_id in the positions array.

#### The Big Takeaway: It Depends on Your Queries

Chapter 2 makes it clear that neither approach is always better. The choice between embedding and referencing depends
entirely on how your application needs to access the data.

- **Choose Embedding (Denormalization)** for one-to-many relationships when you primarily access the "many" side through
  the "one" side (like the positions in a resume). This is great for read-heavy applications because it avoids JOINs.

- **Choose Referencing (Normalization)** when the relationship is many-to-many, or when the referenced data is large,
  frequently updated, or accessed on its own.

The document model's greatest strength, though, _is_ locality, and this is the greatest trade-off.
