# Документация проекта

## Directory Structure
```
solution/
├── Dockerfile          # Container configuration
├── main.py             # Main application entry point
├── requirements.txt    # Python dependencies
├── api/                # API endpoints and controllers
├── auth/               # Authentication module
├── database/           # Database connection and migrations
├── dsl/                
├── models/             # Data models
└── tests/              # tests
```
## Technologies Used
- **Python**: Primary programming language
- **Docker**: Containerization platform
- **FastAPI** (likely): Web framework for API development
- **SQLAlchemy** (likely): ORM for database operations
- **Pydantic**: Data validation and serialization
- **GitLab CI**: Continuous integration pipeline

### Сторонние ресурсы
Для дебага использовался qwen , он помогал разобраться в чем ошибки и где что я не дописал, а также помогал чинить тесты.