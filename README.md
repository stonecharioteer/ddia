# Designing Data-Intensive Applications: Practical Learning Journey

This repository contains hands-on exercises and practical implementations based on Martin Kleppmann's **"Designing
Data-Intensive Applications"**. Rather than just reading through the concepts, each chapter includes working code
examples that demonstrate the fundamental principles of modern data systems.

## Why This Approach?

DDIA covers complex distributed systems concepts that can be abstract when encountered only through text. These
exercises bridge the gap between theory and practice by:

- **Building real systems** that exhibit the behaviors described in the book
- **Experiencing trade-offs firsthand** rather than just reading about them
- **Understanding performance characteristics** through measurement and testing
- **Comparing different approaches** with concrete implementations

## Chapters

- **[Chapter 01: Performance and Percentiles](./chapter01_perf_test/README.md)**: Learn why averages lie and percentiles matter through practical load testing with FastAPI and statistical analysis.

- **[Chapter 02: Data Models](./chapter02_data_models/README.md)**: Experience the object-relational impedance mismatch and understand when document, relational, and graph data models shine by implementing the same application in PostgreSQL, MongoDB, and Neo4j.

## Technology Stack

This learning journey uses a diverse set of technologies to mirror real-world data system architectures:

- **Languages**: Python, Go
- **Databases**: PostgreSQL, MongoDB, Neo4j
- **Message Systems**: Kafka (planned)
- **Big Data**: Hadoop, Spark (planned)
- **Orchestration**: Docker, k3d, Temporal (planned)
- **Development**: uv, mise, justfile

## Getting Started

Each chapter directory contains its own README with specific setup instructions. Generally:

1. **Prerequisites**: Docker, Python 3.13+, Go (via mise)
2. **Environment Setup**: `uv sync` in relevant directories
3. **Services**: `docker compose up -d <service>` as needed
4. **Execution**: Follow chapter-specific instructions

## Learning Outcomes

By working through these exercises, you'll gain:

- **Practical experience** with the systems described in DDIA
- **Intuition** for when different data models and architectures are appropriate
- **Hands-on knowledge** of performance measurement and system characterization
- **Understanding** of real-world trade-offs in distributed systems design

## Progress Tracking

See [CHANGELOG.md](CHANGELOG.md) for detailed progress updates and implementation notes.

---

_This is a learning project aimed at deepening understanding of data-intensive systems through practical implementation.
The goal is hands-on experience with the concepts that make modern distributed systems work._
