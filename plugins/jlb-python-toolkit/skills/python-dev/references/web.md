# Référence : Web Apps & APIs Python

## FastAPI — Structure recommandée

```
my_api/
├── pyproject.toml
├── .env
├── src/
│   └── my_api/
│       ├── __init__.py
│       ├── main.py          # app FastAPI, inclusion des routers
│       ├── config.py        # Settings pydantic-settings
│       ├── dependencies.py  # Dépendances FastAPI (get_db, get_current_user)
│       ├── models/          # SQLAlchemy models (ORM)
│       ├── schemas/         # Pydantic schemas (requêtes/réponses)
│       ├── routers/         # Un fichier par domaine (users.py, items.py)
│       └── services/        # Logique métier, indépendante du web
└── tests/
```

### main.py — Squelette FastAPI

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import users, items


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage : init connexions, warm-up cache
    yield
    # Arrêt : fermer connexions, flush buffers


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(items.router, prefix="/api/v1/items", tags=["items"])
```

### Router FastAPI — Pattern CRUD

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_db, get_current_user
from ..schemas.user import UserCreate, UserResponse
from ..services.user_service import UserService

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    service: UserService = Depends(),
) -> UserResponse:
    """Créer un nouvel utilisateur."""
    try:
        return service.create(payload)
    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),  # auth requise
) -> UserResponse:
    user = service.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### Gestion des erreurs globale

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    logger.warning("Domain error: %s", exc)
    return JSONResponse(
        status_code=400,
        content={"error": exc.error_code, "message": str(exc)},
    )
```

---

## Flask — Structure recommandée

```
my_flask_app/
├── pyproject.toml
├── .env
├── src/
│   └── my_flask_app/
│       ├── __init__.py      # create_app() factory
│       ├── config.py
│       ├── extensions.py    # db, login_manager, etc.
│       ├── models/
│       ├── blueprints/      # Un blueprint par domaine
│       └── services/
└── tests/
```

### Application Factory Pattern (Flask)

```python
# __init__.py
from flask import Flask
from .extensions import db, login_manager
from .blueprints.users import users_bp
from .config import Config


def create_app(config: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(users_bp, url_prefix="/api/users")

    return app
```

**Toujours utiliser l'Application Factory** — jamais `app = Flask(__name__)` au module level, qui empêche les tests.

---

## Django — Conventions clés

```
my_django_project/
├── manage.py
├── config/           # settings, urls, wsgi/asgi
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   └── urls.py
└── apps/
    └── users/        # Une app par domaine
        ├── models.py
        ├── views.py
        ├── serializers.py  # si DRF
        ├── urls.py
        └── tests/
```

### Django REST Framework — ViewSet

```python
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related("profile").all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filtrer selon l'utilisateur connecté
        return super().get_queryset().filter(org=self.request.user.org)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.deactivate()
        return Response({"status": "deactivated"})
```

---

## Authentification — JWT avec FastAPI

```python
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

---

## SQLAlchemy 2.x — Patterns modernes

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

# ✅ Requête moderne (SQLAlchemy 2.x)
def get_active_users(session: Session) -> list[User]:
    stmt = select(User).where(User.is_active == True).order_by(User.created_at.desc())
    return list(session.scalars(stmt))

# ❌ Ancienne syntaxe (SQLAlchemy 1.x, à éviter)
users = session.query(User).filter(User.is_active == True).all()
```

**Session management :**

```python
# Dependency FastAPI
def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
```

---

## Liens officiels

- FastAPI : https://fastapi.tiangolo.com/
- Flask : https://flask.palletsprojects.com/
- Django : https://docs.djangoproject.com/
- SQLAlchemy 2.x : https://docs.sqlalchemy.org/en/20/
- Pydantic : https://docs.pydantic.dev/
- pydantic-settings : https://docs.pydantic.dev/latest/concepts/pydantic_settings/
