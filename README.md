# Quiz Application

A Flask-based web application for creating and taking quizzes with user authentication and admin management.

## Features

- **User Authentication**: Register and login with JWT-based authentication
- **Admin Dashboard**: Create quizzes and manage users (admin role required)
- **Quiz Management**: 
  - Create quizzes with multiple choice questions
  - View all available quizzes
  - Take quizzes with picking options
  - Get instant results with correct answers
- **User Roles**: Separate admin and user roles with different access levels
- **Secure Password Storage**: Passwords are hashed using Werkzeug
- **Database**: MongoDB for data persistence

## Technologies Used

- **Backend**: Flask (Python)
- **Database**: MongoDB with PyMongo
- **Authentication**: JWT (JSON Web Tokens) via PyJWT
- **Security**: Werkzeug for password hashing
- **Environment**: python-dotenv for configuration management

## Installation

1. **Install Python dependencies** (see `requirements.txt`):
   - Flask
   - PyMongo
   - python-dotenv
   - PyJWT

2. **Set up MongoDB**: Ensure MongoDB is running and accessible

3. **Configure environment**: Create a `.env` file in the project root with the following variables:
   ```
   MONGO_URI=mongodb://localhost:27017/
   DB_NAME=userdb
   JWT_SECRET_KEY=your-secret-key-here
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=admin123
   ```

4. **Run the application**: The app runs on port 5000 by default

## API Endpoints

### Authentication

#### Register User
- **POST** `/register`
- **Body**: 
  ```json
  {
    "name": "John Doe",
    "email_id": "john@example.com",
    "phone": "+91-9876543210",
    "password": "password123",
    "confirm_password": "password123",
    "school": "School Name"
  }
  ```
- **Response**: User details and role

#### Login
- **POST** `/login`
- **Body**:
  ```json

- **Response**: JWT token and user information

### Quiz Management (Admin Only)

#### Create Quiz
- **POST** `/quiz`
- **Auth**: Bearer token (Admin)
- **Body**:
  ```json
  {
    "title": "Math Quiz",
    "questions": [
      {
        "question": "What is 2+2?",
        "options": ["3", "4", "5", "6"],
        "correct_answer": "4"
      }
    ]
  }
  ```

#### Get All Users
- **GET** `/users`
- **Auth**: Bearer token (Admin)

### Quiz Taking

#### Get All Quizzes
- **GET** `/quizzes`
- **Optional Query**: `?created_by=Administrator`

#### Get Quiz Details
- **GET** `/quiz/<quiz_id>`
- **Auth**: Bearer token
- **Response**: Quiz questions (without correct answers)

#### Submit Quiz
- **POST** `/quiz/<quiz_id>/submit`
- **Auth**: Bearer token
- **Body**:
  ```json
  {
    "answers": ["4", "Earth"],
    "time": 120
  }
  ```
- **Response**: Score, correct answers, and detailed results

### Utility Endpoints

#### Decode Token
- **POST** `/decode-token`
- **Body**: `{ "token": "your-jwt-token" }`
- **Response**: Decoded token information

#### Verify Token
- **GET** `/verify-token`
- **Auth**: Bearer token
- **Response**: Current user information

## User Roles

### Admin
- Default credentials: username `admin`, password `admin123`
- Can create quizzes
- Can view all users
- Can access admin-specific endpoints

### User
- Regular users registered through `/register`
- Can view and take quizzes
- Can submit quiz answers

## Data Validation

- **Email**: Must be valid email format
- **Phone**: Must be in format `+91-XXXXXXXXXX` (10 digits after prefix)
- **Password**: Must match confirm password
- **JWT Token**: Valid for 8766 hours (approximately 1 year)

## Database Collections

- `users`: User accounts and credentials
- `quizzes`: Quiz definitions and questions
- `quiz_results`: Submitted quiz answers and scores

## Security Features

- Password hashing using Werkzeug
- JWT token-based authentication
- Role-based access control (admin vs user)
- Token expiration validation
- Admin credentials stored in environment variables

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `409`: Conflict
- `500`: Internal Server Error

