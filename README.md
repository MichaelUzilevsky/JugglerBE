# Juggler BackEnd

## Overview
Juggler BackEnd is a modular Python backend designed to manage users, resources, and orders for complex scheduling and resource allocation systems. It features a clean architecture, async operations, MongoDB integration, and robust configuration and logging support.

## Features
- **User Management**: Sign up, login, update, delete, and admin role assignment.
- **Resource Management**: CRUD operations for various resource types, dynamic resource class loading, and duplicate name protection.
- **Order Management**: Create, update, approve, reject, and query orders with conflict detection and time-range filtering.
- **MongoDB Integration**: Async database operations using Motor and Pydantic models.
- **Configurable**: Environment-based configuration loading and support for .env files.
- **Structured Logging**: YAML-based logging configuration with file output.
- **Exception Handling**: Custom exceptions for users, resources, and orders.

## Project Structure
```
JugglerBE/
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── configs/                 # App and logging configs
├── logs/                    # Log files
├── src/
│   ├── base/                # Config and logger loaders
│   ├── db/                  # Database and CRUD logic
│   ├── exceptions/          # Custom exception classes
│   ├── handlers/            # Business logic for users, resources, orders
│   ├── models/              # Data models for users, resources, orders
│   └── utils/               # Utility functions
```

## Getting Started
1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure environment**:
   - Edit `configs/app/base.yaml` and environment-specific YAMLs.
   - Optionally create a `.env` file for secrets.
3. **Configure logging**:
   - Edit `configs/logging/logger.yaml` as needed.
4. **Run the application**:
   ```bash
   python main.py
   ```

## Configuration
- **App Config**: Located in `configs/app/`. Supports multiple environments (`base.yaml`, `dev.yaml`, `prod.yaml`).
- **Logging**: Configured via `configs/logging/logger.yaml`.
- **MongoDB**: Connection details in config files and `.env`.

## Key Modules
- `src/base/config_loader.py`: Loads and merges configuration files.
- `src/base/logger_loader.py`: Sets up logging from YAML config.
- `src/db/mongodb/mongo_crud.py`: Generic async CRUD operations for MongoDB collections.
- `src/handlers/users_handler.py`: User-related business logic.
- `src/handlers/resources_handler.py`: Resource-related business logic.
- `src/handlers/orders_handler.py`: Order-related business logic and conflict detection.
- `src/utils/system_resources.py`: Dynamic resource class loading from config.

## Exception Handling
Custom exceptions are defined for:
- User login and registration errors
- Resource duplication
- Order conflicts, not found, and permission issues

## Logging
Logs are written to the `logs/` directory. Logging is configured via YAML and supports file rotation and formatting.

## Extending
- Add new resource types by creating new model classes and updating config.
- Add new business logic by extending handler classes.
- Add new exception types in the `exceptions/` directory.

## License
MIT License

## Author
Michael Uzilevsky

