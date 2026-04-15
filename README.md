# Social Media API Backend

A production-ready social media backend built with Django and Django REST Framework. This project secures all critical endpoints using **Knox token-based authentication** and implements advanced query capabilities via the Django ORM to recommend new connections based on mutual friendships and common interests.

## Features
- **Secure Knox Authentication** (Registration, Login, User Management).
- **Posts & Feeds** (Create posts and view feeds containing posts from your accepted network).
- **Like System** (Unique one-like-per-post validations).
- **Connections Management** (Send, Accept, Decline friend requests).
- **User Recommendation Engine** (Ranks and suggests users by mutual contacts first, then by shared interests).

---

## Setup Instructions

### 1. Requirements
- Python 3.8+
- SQLite (default) or any SQL database

### 2. Environment Initialization
Navigate to the root directory `social_project` and create a Python virtual environment:
```bash
python -m venv venv
```

Activate the virtual environment:
*On Windows:*
```bash
.\venv\Scripts\activate
```
*On macOS/Linux:*
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup & Migrations
First, ensure that the media directory gets correctly initialized by the server natively, then apply all migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Run the Server
```bash
python manage.py runserver
```
The server will start at `http://127.0.0.1:8000/`.

---

## API Documentation

> **Base URL:** `http://127.0.0.1:8000/api/`

*Note: All endpoints (except Auth Register and Login) require a Token header:*
`Authorization: Token <your_knox_token>`

### Authentication

#### 1. Register User
- **Method:** `POST`
- **URL:** `/auth/register/`
- **Body:**
  ```json
  {
      "username": "johndoe",
      "email": "johndoe@example.com",
      "password": "securepassword",
      "first_name": "John",
      "last_name": "Doe"
  }
  ```
- **Response:** 201 Created (Returns user object and Knox token)

#### 2. Login
- **Method:** `POST`
- **URL:** `/auth/login/`
- **Body:**
  ```json
  {
      "username": "johndoe",
      "password": "securepassword"
  }
  ```
- **Response:** 200 OK (Returns user object and Knox token)

#### 3. Logout
- **Method:** `POST`
- **URL:** `/auth/logout/`
- **Headers:** `Authorization: Token <token>`
- **Response:** 204 No Content

### Post & Interactions

#### 1. Create a Post / List All Posts
- **Method:** `GET` / `POST`
- **URL:** `/posts/`
- **Body (POST):**
  ```json
  {
      "content": "Hello, world! This is my first post."
  }
  ```
- **Response (POST):** 201 Created

#### 2. Get Feed
- **Method:** `GET`
- **URL:** `/posts/feed/`
- **Description:** Returns posts authored by you and your accepted connections.
- **Response:** 200 OK (Array of posts)

#### 3. Toggle Like on a Post
- **Method:** `POST`
- **URL:** `/posts/<post_id>/like/`
- **Description:** Automatically handles Like/Unlike. Protects against double-liking.
- **Response:** 200 OK (Unliked) or 201 Created (Liked)

### Connection Network

#### 1. Send Connection Request
- **Method:** `POST`
- **URL:** `/connections/request/<user_id>/`
- **Response:** 201 Created (or 400 if already sent)

#### 2. List Pending Requests
- **Method:** `GET`
- **URL:** `/connections/pending/`
- **Response:** 200 OK (Array of connection objects directed at the user)

#### 3. Accept Connection
- **Method:** `POST`
- **URL:** `/connections/accept/<connection_id>/`
- **Response:** 200 OK

#### 4. Decline Connection
- **Method:** `POST`
- **URL:** `/connections/decline/<connection_id>/`
- **Response:** 200 OK

### User Discovery

#### 1. Get User Recommendations
- **Method:** `GET`
- **URL:** `/users/recommendations/`
- **Description:** The complex logic engine. Pulls an optimized list of users excluded from your current network map, scored by mutual accepted connections, and then tie-broken by shared personal interests.
- **Response:** 200 OK (Ranked array of user objects)

#### 2. Add / List Global Interests
- **Method:** `GET` / `POST`
- **URL:** `/interests/`
- **Body (POST):**
  ```json
  {
      "name": "Technology"
  }
  ```
- **Response:** 200 OK / 201 Created
