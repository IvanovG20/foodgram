## Проект "Foodgram"

Проект Foodgram - онлайн-сервис, пользователи которого могут выкладывать свои рецепты,
просматривать рецепты других пользователей, и если чей-то рецепт приглянулся,
пользователь может добавить его в "Избранное". Пользователь может подписаться на автора,
чьи рецепты нравятся ему. Присутствует фильтрация по тегам, чтобы было удобно выбирать
блюда на разные виды приема пищи. Если пользователь решит приготовить блюдо по выбранному
рецепту, нужно будет добавить его в "Список покупок". В данном разделе можно скачать 
получившийся список покупок, в котором будут ингредиенты и их количество.

## Запуск проекта локально

Склонируйте репозиторий и перейдите в папку backend/:
```
git clone https://github.com/IvanovG20/foodgram.git
```
```
cd foodgram/backend/
```
Создать и активировать виртуальное окружение:
```
python3 -m venv venv
```
```
source venv/bin/activate
```

После установки зависимостей перейдите в директорию с инфраструктурой:
```
cd ..
```
```
cd infra
```

Создать файл .env:
```
touch .env
```

Заполнить файл .env в соотвествии с примером .env.example:
```
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_NAME=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=django-insecure-+alqk6o@#cr6_@e^wrvgr5ko)ivub$o)6%dxyb9a=j2g)oc5l%
```

Запустить контейнеры локально следующей командой:
```
sudo docker -f docker-compose.yml up -d
```

С этого момента проект будет доступен по адресу:
```
http://localhost:8000/
```

После запуска, собираем статику в контейнере бэкэнда:
```
sudo docker -f docker-compose.yml exec backend python manage.py collectstatic
```

В этом же контейнере создать и выполнить миграции:
```
sudo docker -f docker-compose.yml exec backend python manage.py makemigrations
```
```
sudo docker -f docker-compose.yml exec backend python manage.py migrate
```

Загрузить ингредиенты в базу данных:
```
sudo docker -f docker-compose.yml exec backend python manage.py add_ingredients
```
