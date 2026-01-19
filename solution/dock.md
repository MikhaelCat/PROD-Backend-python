# Документация проекта

## Содержание
1. [Обзор проекта](#обзор-проекта)
2. [Архитектура](#архитектура)
3. [Структура каталогов](#структура-каталогов)
4. [Технологии](#технологии)
5. [Установка и настройка](#установка-и-настройка)
6. [Конфигурация](#конфигурация)
7. [Документация API](#документация-api)
8. [Схема базы данных](#схема-базы-данных)
9. [Аутентификация](#аутентификация)
10. [Тестирование](#тестирование)
11. [Развертывание](#развертывание)
12. [CI/CD](#cicd)

## Обзор проекта
Этот проект представляет собой веб-приложение, разработанное с использованием современных технологий. Проект состоит из нескольких компонентов, включая фронтенд, бэкенд и базу данных.

## Архитектура
Проект использует микросервисную архитектуру с разделением на:
- Фронтенд (React/Vue/Angular)
- Бэкенд (Node.js/Express или другой серверный фреймворк)
- База данных (PostgreSQL, MongoDB или другая СУБД)
- Контейнеризация (Docker)
- Оркестрация (Docker Compose/Kubernetes)

## Структура каталогов
```
solution/
├── frontend/          # Исходный код фронтенда
├── backend/           # Исходный код бэкенда
├── database/          # Скрипты миграции и схемы базы данных
├── docker/            # Конфигурационные файлы Docker
├── tests/             # Тесты приложения
├── docs/              # Дополнительная документация
├── config/            # Файлы конфигурации
└── scripts/           # Вспомогательные скрипты
```

## Технологии
- **Языки программирования**: JavaScript/TypeScript, Python, Java и др.
- **Фронтенд**: React, Vue.js, Angular или другие фреймворки
- **Бэкенд**: Node.js, Express, Django, Spring Boot и др.
- **Базы данных**: PostgreSQL, MySQL, MongoDB, Redis
- **Контейнеризация**: Docker
- **Оркестрация**: Docker Compose, Kubernetes
- **CI/CD**: GitLab CI, GitHub Actions
- **Версионность**: Git

## Установка и настройка
### Предварительные требования
- Docker (v20.10.0 или выше)
- Docker Compose (v2.0.0 или выше)
- Node.js (если используется для бэкенда)
- Git

### Шаги установки
1. Клонируйте репозиторий:
```bash
git clone <URL_РЕПОЗИТОРИЯ>
cd solution
```

2. Установите зависимости:
```bash
# Для фронтенда
cd frontend && npm install

# Для бэкенда
cd backend && npm install || cd backend && pip install -r requirements.txt
```

3. Запустите проект с помощью Docker:
```bash
docker-compose up --build
```

## Конфигурация
### Переменные окружения
Файл `.env` содержит все необходимые переменные окружения:

#### Для бэкенда:
```
NODE_ENV=production
PORT=3000
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp_db
DB_USER=db_user
DB_PASSWORD=secret_password
JWT_SECRET=jwt_secret_key
```

#### Для фронтенда:
```
REACT_APP_API_URL=http://localhost:3000
REACT_APP_ENVIRONMENT=development
```

## Документация API
### Базовый URL
`http://localhost:3000/api/v1`

### Аутентификация
Для доступа к защищенным маршрутам требуется токен JWT, передаваемый в заголовке:
```
Authorization: Bearer <токен>
```

### Маршруты API

#### Пользователи
- `GET /api/v1/users` - получить список пользователей
- `POST /api/v1/users` - создать нового пользователя
- `GET /api/v1/users/:id` - получить информацию о пользователе
- `PUT /api/v1/users/:id` - обновить информацию о пользователе
- `DELETE /api/v1/users/:id` - удалить пользователя

#### Аутентификация
- `POST /api/v1/auth/login` - вход пользователя
- `POST /api/v1/auth/register` - регистрация пользователя
- `POST /api/v1/auth/logout` - выход пользователя

## Схема базы данных
### Таблица пользователей
```
users
├── id (UUID, PRIMARY KEY)
├── username (VARCHAR(50), UNIQUE, NOT NULL)
├── email (VARCHAR(100), UNIQUE, NOT NULL)
├── password_hash (VARCHAR(255), NOT NULL)
├── first_name (VARCHAR(50))
├── last_name (VARCHAR(50))
├── created_at (TIMESTAMP, DEFAULT NOW())
└── updated_at (TIMESTAMP, DEFAULT NOW())
```

### Таблица сессий
```
sessions
├── id (UUID, PRIMARY KEY)
├── user_id (UUID, FOREIGN KEY -> users.id)
├── token (VARCHAR(255), NOT NULL)
├── expires_at (TIMESTAMP, NOT NULL)
└── created_at (TIMESTAMP, DEFAULT NOW())
```

## Аутентификация
Проект использует JWT-аутентификацию:
- При регистрации/входе пользователь получает токен
- Токен должен быть включен в заголовок Authorization для защищенных маршрутов
- Токены имеют срок действия и могут быть обновлены

## Тестирование
### Unit тесты
Для запуска unit тестов:
```bash
npm run test:unit
```

### Интеграционные тесты
Для запуска интеграционных тестов:
```bash
npm run test:integration
```

### E2E тесты
Для запуска end-to-end тестов:
```bash
npm run test:e2e
```

## Развертывание
### Локальное развертывание
```bash
docker-compose up --build
```

### Настройка продакшена
1. Измените переменные окружения в файле `.env.production`
2. Запустите сборку:
```bash
docker-compose -f docker-compose.prod.yaml up --build
```

### Разворачивание на сервере
1. Подключитесь к серверу
2. Клонируйте репозиторий
3. Обновите конфигурационные файлы
4. Запустите приложение

## CI/CD
Проект использует GitLab CI/CD для автоматизации процессов:
- Автоматические тесты при каждом пуше
- Автоматическая сборка образов Docker
- Автоматическое развертывание на staging/production
- Контроль качества кода

### Pipeline stages:
- `build` - сборка приложения
- `test` - выполнение тестов
- `security` - проверка безопасности
- `deploy` - развертывание