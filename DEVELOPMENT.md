# Development
The next phase of the SysBio project calls for a transition of this code from a demonstration to a minimal but functional and production-ready "beta" version of the SysBio search API service. This section discusses broad areas of development that should be considered in pursuit of this goal.

## Year 2 high-level development needs

### Packaging
- Modernize Python packaging (e.g. use `pyproject.toml` instead of requirements.txt)
- Centralize configuration instead of reading environment variables directly

### Performance & Scaling
- Identify current and future scale of data size (given existing AMPs, trends we expect to see for future datasets, and future-proofing)
- Identify user interaction patterns that are relevant to scaling concerns 
	- e.g. "we think a user is likely to try to grab all data that they can access; how should we handle it if that results in a huge payload?"
- How does the top-level `sysbio-service` handle performance issues from its downstream AMP services?

### Persistence hardening
- The system currently uses SQLite files to store session data. 
- Recommendation: Migrate to something like Postgres instead. Develop a deployment and backup strategy (probably a managed Cloud SQL deployment makes the most sense to achieve both of those goals). 
- Develop a strategy for performing schema migrations (e.g. use Liquibase, Alembic, ...)

### Authentication interface
- `auth-service` is tightly coupled to `sysbio-service` through a shared, symmetric `JWT_SECRET`.
- Decouple `sysbio-service` from `auth-service` by implementing a "no-auth" mode with an optional, injectable authentication dependency, which we'll develop with Technome.
- Work with Technome to develop an injectable interface that they can develop against. Figure out details of the final authentication setup with them to get this part of `sysbio-service` closer to the end vision.
- We shouldn't necessarily throw away `auth-service`. It may be useful for end-to-end testing. But it will probably need to be refactored.

### Security
- Identify attack vectors and develop mitigation strategies (e.g. SQL injection --> use query templates or other means)
- Consult with Verily security eng for advice.

### Automated testing & downstream service contracts
- We have unit tests, but they are out of date and need to be refactored and incorporated into CI/CD
- We should establish a plan for testing the contract between `sysbio-service` and downstream AMP services. 
	- Automated contract testing frameworks like Pact are *potentially* a good fit here, but the tradeoffs should be considered carefully. It could be a huge distraction.
- Regardless of contract testing strategy, we should formalize our versioning strategy and expose it to API consumers through a /version endpoint.

### Deployment, CI/CD, developer experience
- Develop a packaging and deployment plan, both for developer use and deployment into our environments.
- Develop an environment strategy: how many environments do we have, what are they for, and how do new versions progress through them?
- Set up formatters and linters, write a contributor's guide, etc.
