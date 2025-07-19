
# Juggler BackEnd

## Overview
Juggler BackEnd is a modular backend built with **FastAPI** for scheduling and resource allocation. It features async operations, JWT authentication, MongoDB integration, and a scalable, maintainable architecture.

## Features
- **User Management**
  - Sign up, login
  - JWT-based authentication (access tokens with user ID and expiration)
  - Admins can promote/demote users and delete accounts
  - No password hashing yet (planned)
- **Order Management**
  - Users create/update orders
  - Orders require admin approval
  - Only creators or admins can update orders
  - Conflict detection prevents scheduling overlaps
  - Filter orders by time and approval status
- **Resource Management**
  - Resource models are statically defined by developers
  - Each model inherits from a base resource
  - Schemas are dynamically exposed to the frontend for auto-generated forms
- **Authentication & Authorization**
  - JWT tokens issued at login (sub=user ID, exp=expiration)
  - Dependency-based access control (admin-only/user-specific routes)
  - No refresh tokens yet (planned)
- **Architecture & Codebase**
  - Modular, scalable codebase
  - Lifespan management with AppFactory
  - Async MongoDB via Motor
  - Pydantic models for validation
  - Logging via YAML config and rotating log files

## Project Structure
```
JugglerBE/
├── main.py
├── configs/
├── logs/
├── src/
│   ├── api/              # FastAPI routes, dependencies, middleware
│   ├── base/             # Configuration and logger setup
│   ├── db/               # MongoDB management
│   ├── handlers/         # Business logic for users, orders, resources
│   ├── models/           # Pydantic models
│   └── exceptions/       # Custom exceptions
```

## Getting Started
1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure environment**:
   - Edit YAML files in `configs/app/` for your environment (`base.yaml`, `dev.yaml`, `prod.yaml`).
   - Optionally create a `.env` file for secrets.
3. **Configure logging**:
   - Edit `configs/logging/logger.yaml` as needed.
4. **Run the application**:
   ```bash
   uvicorn main:app --reload
   ```

## Configuration
- **App Config**: Located in `configs/app/`. Supports multiple environments.
- **Logging**: Configured via `configs/logging/logger.yaml`.
- **MongoDB**: Connection details in config files and `.env`.

## API Overview
- `/api/v1/users/`: login, signup, admin actions
- `/api/v1/orders/`: create/update/get user-specific orders
- `/api/v1/resources/`: expose schemas for resource models

## Exception Handling
Custom exceptions for:
- User login/registration errors
- Resource duplication
- Order conflicts, not found, permission issues

## Logging
Logs are written to the `logs/` directory. Logging is configured via YAML and supports file rotation and formatting. Middleware logs requests and errors.

## Extending
- Add new resource types by creating new model classes and updating config
- Add new business logic by extending handler classes
- Add new exception types in the `exceptions/` directory


## License
MIT License

## Author
Michael Uzilevsky

